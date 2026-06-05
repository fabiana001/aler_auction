import os
import pandas as pd
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent

from aler_auctions.data_integration.geocoder import Geocoder

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Geocoding Agent.
    Enriches the consolidated auction dataset with latitude and longitude.
    """
    # Load environment variables (API Key)
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env file.")
        sys.exit(1)
        
    # Define paths
    data_dir = PROJECT_ROOT / "data"
    input_path = data_dir / "interim" / "consolidated_auction_dataset.csv"
    output_path = data_dir / "interim" / "consolidated_auction_dataset_geocoded.csv"
    cache_path = data_dir / "cache" / "geocoding_cache.json"
    
    if not input_path.exists():
        logger.error(f"Input dataset not found: {input_path}")
        sys.exit(1)
        
    # Load dataset
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Prepare address strings for geocoding.
    # Wayback rows: address + street_number + city in separate columns.
    # PDF-only rows: full address already in address field (e.g. "MILANO VIA PASCOLI '4 70").
    import re
    from aler_auctions.data_integration.geocoder import _clean_pdf_address

    def build_geo_address(row):
        addr = str(row.get('address') or '').strip()
        street_num = str(row.get('street_number') or '').strip()
        city = str(row.get('city') or '').strip()
        street_num = '' if street_num.lower() in ('nan', 'none', '') else street_num
        city = '' if city.lower() in ('nan', 'none', '') else city

        if street_num:
            # Wayback record with separate civic number
            city_part = city or 'MILANO'
            full = f"{addr} {street_num}, {city_part}, Italy"
        elif not city:
            # PDF-only record: city is embedded in address — clean and append Italy only
            full = _clean_pdf_address(addr) + ", Italy"
        else:
            full = f"{addr}, {city}, Italy"
        return re.sub(r'\s+', ' ', full).strip()

    df['full_address_for_geo'] = df.apply(build_geo_address, axis=1)
    
    # Initialize Geocoder
    geocoder = Geocoder(api_key=api_key, cache_path=str(cache_path))
    
    # Run geocoding on unique full addresses
    geo_df = geocoder.geocode_series(df['full_address_for_geo'])
    
    # Merge coordinates back to the main dataframe
    logger.info("Merging coordinates back to the dataset...")
    df = df.merge(
        geo_df, 
        left_on='full_address_for_geo', 
        right_on='address', 
        how='left', 
        suffixes=('', '_geo_result')
    )
    
    # Rename and clean up
    if 'lat' in df.columns:
        df.rename(columns={'lat': 'latitude', 'lng': 'longitude'}, inplace=True)
    
    # Drop intermediate columns
    df.drop(columns=['full_address_for_geo', 'address_geo_result'], inplace=True, errors='ignore')
    
    # Save enriched dataset
    logger.info(f"Saving geocoded dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Also update the JSON version
    json_output = output_path.with_suffix('.json')
    df.to_json(json_output, orient='records', indent=2)
    logger.info(f"Saving geocoded JSON to {json_output}")
    
    # Stats
    geocoded_count = df['latitude'].notna().sum()
    logger.info(f"Geocoding enrichment complete: {geocoded_count}/{len(df)} records geocoded.")

if __name__ == "__main__":
    main()
