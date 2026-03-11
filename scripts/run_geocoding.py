import os
import pandas as pd
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

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
    input_path = data_dir / "consolidated_auction_dataset.csv"
    output_path = data_dir / "consolidated_auction_dataset_geocoded.csv"
    cache_path = data_dir / "geocoding_cache.json"
    
    if not input_path.exists():
        logger.error(f"Input dataset not found: {input_path}")
        sys.exit(1)
        
    # Load dataset
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Prepare address strings for geocoding
    # We combine address, street_number and city to get better results
    # and normalize to stay robust.
    df['full_address_for_geo'] = (
        df['address'].fillna('') + ' ' + 
        df['street_number'].fillna('').astype(str) + ', ' + 
        df['city'].fillna('MILANO') + ', Italy'
    ).str.strip().str.replace(r'\s+', ' ', regex=True)
    
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
