import logging
import sys
import pandas as pd
from pathlib import Path

# Add src to python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

from aler_auctions.analysis.price_analyzer import PriceAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Price Analysis Agent.
    Performs clustering and calculates price metrics.
    """
    logger.info("Starting Price Analysis Process...")
    
    # Define paths
    data_dir = PROJECT_ROOT / "data"
    # We use the geocoded dataset as input for clustering
    input_path = data_dir / "consolidated_auction_dataset_geocoded.csv"
    output_path = data_dir / "consolidated_auction_dataset_analyzed"
    
    if not input_path.exists():
        logger.error(f"Geocoded dataset not found at {input_path}. Please run geocoding first.")
        sys.exit(1)

    # Load dataset
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Initialize analyzer
    # The columns in the geocoded file are 'latitude' and 'longitude' (renamed by run_geocoding.py)
    # PriceAnalyzer expects 'lat' and 'lng' based on the user's snippet.
    # We'll map them.
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df = df.rename(columns={'latitude': 'lat', 'longitude': 'lng'})

    analyzer = PriceAnalyzer(min_cluster_size=20)
    
    # Execute analysis
    df_analyzed = analyzer.analyze_dataset(df)
    
    # Save enriched dataset
    analyzer.save_enhanced_dataset(df_analyzed, output_path)
    
    logger.info("Price analysis completed successfully.")
    
    # Stats
    if 'zone_id' in df_analyzed.columns:
        zones = df_analyzed['zone_id'].dropna().unique()
        logger.info(f"Identified {len(zones)} zones (clusters).")
        # Zone -1 is noise in HDBSCAN
        noise_count = (df_analyzed['zone_id'] == -1).sum()
        if noise_count > 0:
            logger.info(f"Records classified as noise: {noise_count}")

if __name__ == "__main__":
    main()
