import pandas as pd
import googlemaps
import logging
import json
import re
import time
from pathlib import Path
from typing import Optional, Dict, List

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    _NOMINATIM_AVAILABLE = True
except ImportError:
    _NOMINATIM_AVAILABLE = False

_nominatim = Nominatim(user_agent="aler_auction_geocoder/1.0") if _NOMINATIM_AVAILABLE else None


def _nominatim_geocode(address: str) -> dict | None:
    """Try geocoding via Nominatim (OpenStreetMap). Returns {'lat': ..., 'lng': ...} or None."""
    if not _NOMINATIM_AVAILABLE or _nominatim is None:
        return None
    try:
        time.sleep(1.1)  # Nominatim rate limit: 1 req/s
        loc = _nominatim.geocode(address, timeout=10)
        if loc:
            return {"lat": loc.latitude, "lng": loc.longitude}
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        pass
    return None


def _clean_pdf_address(address: str) -> str:
    """Normalize PDF address format for Nominatim geocoding.

    PDF addresses look like: "MILANO VIA GIOVANNI PASCOLI '4 70"
    → "Via Giovanni Pascoli 4, Milano"
    The ' before the civic number is a separator; trailing number is apartment (dropped).
    """
    if not address:
        return address
    addr = address.strip()

    # Extract city prefix (first uppercase word(s) before a street keyword)
    city_match = re.match(
        r"^([A-ZÀÈÌÒÙÉÁ][A-ZÀÈÌÒÙÉÁ\s]+?)\s+(VIA|VIALE|CORSO|PIAZZA|LARGO|VICOLO|PIAZZALE|STRADA)\b",
        addr,
    )
    city = city_match.group(1).title() if city_match else "Milano"
    # Remove city prefix from address
    addr_no_city = addr[city_match.end(0) - len(city_match.group(2)):].strip() if city_match else addr

    # Remove apartment: '4 70 → 4
    m = re.match(r"^(.*?)\s+'(\d+[A-Za-z]?)\s+\d+$", addr_no_city)
    if m:
        street_part = m.group(1)
        civic = m.group(2)
    else:
        # No apartment suffix — just strip the apostrophe before civic number
        cleaned = re.sub(r"'\s*(\d)", r"\1", addr_no_city)
        # Try to split last token as civic number
        parts = cleaned.rsplit(None, 1)
        if len(parts) == 2 and re.match(r"^\d+[A-Za-z]?$", parts[1]):
            street_part, civic = parts[0], parts[1]
        else:
            street_part, civic = cleaned, ""

    street_titled = street_part.title().strip()
    if civic:
        return f"{street_titled} {civic}, {city}"
    return f"{street_titled}, {city}"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Geocoder:
    """
    Agent responsible for enriching address data with GPS coordinates using Google Maps API.
    Includes persistent caching to minimize API costs and redundant calls.
    """
    
    def __init__(self, api_key: str, cache_path: Optional[str] = None):
        self.gmaps = googlemaps.Client(key=api_key)
        self.cache_path = Path(cache_path) if cache_path else Path("data/geocoding_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Optional[float]]]:
        """Loads cached coordinates from a JSON file."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Starting with empty cache.")
        return {}

    def _save_cache(self):
        """Saves current cache to a JSON file."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def geocode_series(self, address_series: pd.Series) -> pd.DataFrame:
        """
        Geocodes a series of addresses, leveraging cache and handling API calls.
        
        Args:
            address_series: A pandas Series containing full address strings.
            
        Returns:
            pd.DataFrame with columns ['address', 'lat', 'lng'].
        """
        unique_addresses = address_series.dropna().unique()
        logger.info(f"Analyzing {len(unique_addresses)} unique addresses...")
        
        results = []
        new_geocodes = 0
        
        for i, address in enumerate(unique_addresses):
            # Check cache first
            if address in self.cache:
                results.append({
                    'address': address,
                    'lat': self.cache[address].get('lat'),
                    'lng': self.cache[address].get('lng')
                })
                continue
            
            # Not in cache, try Google Maps then Nominatim as fallback
            try:
                logger.info(f"[{i+1}/{len(unique_addresses)}] Geocoding: {address}")
                coords = None

                # Try Google Maps
                try:
                    geocode_result = self.gmaps.geocode(address)
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        coords = {'lat': location['lat'], 'lng': location['lng']}
                    else:
                        logger.warning(f"Google: no results for: {address}")
                except Exception as gmaps_err:
                    logger.warning(f"Google Maps failed ({gmaps_err}), trying Nominatim...")

                # Fallback to Nominatim — address is already clean at this point
                if coords is None:
                    nom_result = _nominatim_geocode(address)
                    if nom_result:
                        coords = nom_result
                        logger.info(f"  → Nominatim hit: {coords}")
                    else:
                        logger.warning(f"No geocoding result for: {address}")

                if coords is None:
                    coords = {'lat': None, 'lng': None}

                self.cache[address] = coords
                new_geocodes += 1
                results.append({'address': address, 'lat': coords['lat'], 'lng': coords['lng']})

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error geocoding {address}: {e}")
                results.append({'address': address, 'lat': None, 'lng': None})
            
            # Save cache incrementally every 20 new geocodes
            if new_geocodes > 0 and new_geocodes % 20 == 0:
                self._save_cache()

        # Final cache save
        if new_geocodes > 0:
            self._save_cache()
            logger.info(f"Geocoding complete. {new_geocodes} new addresses geocoded and cached.")
            
        return pd.DataFrame(results)

def geocode(address_series: pd.Series, api_key: str, cache_path: Optional[str] = None) -> pd.DataFrame:
    """
    Functional wrapper for the Geocoder agent, compatible with the requested signature
    but enhanced with persistent caching and logging.
    """
    geocoder = Geocoder(api_key, cache_path)
    return geocoder.geocode_series(address_series)
