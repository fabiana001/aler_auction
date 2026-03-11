import pandas as pd
import googlemaps
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, List

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
            
            # Not in cache, call API
            try:
                logger.info(f"[{i+1}/{len(unique_addresses)}] Geocoding: {address}")
                geocode_result = self.gmaps.geocode(address)
                
                if geocode_result:
                    location = geocode_result[0]['geometry']['location']
                    coords = {'lat': location['lat'], 'lng': location['lng']}
                    self.cache[address] = coords
                    new_geocodes += 1
                else:
                    logger.warning(f"No results found for: {address}")
                    coords = {'lat': None, 'lng': None}
                    self.cache[address] = coords
                
                results.append({
                    'address': address,
                    'lat': coords['lat'],
                    'lng': coords['lng']
                })
                
                # Small sleep to be polite to the API (though gmaps client handles most limits)
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
