import logging
import sys
from pathlib import Path

# Add src to python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "src"))

from aler_auctions.data_integration.dataset_integrator import DatasetIntegrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Dataset Integration Agent.
    Joins Waymachine property data with PDF auction results.
    """
    logger.info("Starting Dataset Integration Process...")
    
    # Define paths
    data_dir = PROJECT_ROOT / "data"
    properties_path = data_dir / "extracted_auctions.csv"
    results_path = data_dir / "extracted_pdf_results.csv"
    output_path = data_dir / "consolidated_auction_dataset.csv"
    
    # Initialize integrator
    integrator = DatasetIntegrator(
        properties_path=str(properties_path),
        results_path=str(results_path)
    )
    
    # Execute integration
    logger.info(f"Source 1 (Properties): {properties_path}")
    logger.info(f"Source 2 (Results): {results_path}")
    
    df_consolidated = integrator.integrate(str(output_path))
    
    if df_consolidated is not None:
        logger.info("Dataset integration completed successfully.")
        logger.info(f"Consolidated dataset contains {len(df_consolidated)} records.")
        logger.info(f"Final files saved to {output_path} and its .json version.")
        
        # Statistics
        if 'auction_result' in df_consolidated.columns:
            results_stats = df_consolidated['auction_result'].value_counts()
            logger.info("Auction Result Statistics:")
            for result, count in results_stats.items():
                logger.info(f"  - {result}: {count}")
    else:
        logger.error("Dataset integration failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
