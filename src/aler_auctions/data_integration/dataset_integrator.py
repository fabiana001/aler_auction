import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetIntegrator:
    """
    Agent responsible for joining property traits with auction results.
    """
    
    def __init__(self, properties_path: str, results_path: str):
        self.properties_path = Path(properties_path)
        self.results_path = Path(results_path)
        
    def integrate(self, output_path: str) -> Optional[pd.DataFrame]:
        """
        Loads property data and auction results, merges them on lot_id, and saves to file.
        """
        if not self.properties_path.exists():
            logger.error(f"Properties file not found: {self.properties_path}")
            return None
            
        if not self.results_path.exists():
            logger.error(f"Results file not found: {self.results_path}")
            return None
            
        logger.info(f"Loading properties from {self.properties_path}")
        df_props = pd.read_csv(self.properties_path)
        
        logger.info(f"Loading results from {self.results_path}")
        df_results = pd.read_csv(self.results_path)
        
        # Standardize lot_id format if necessary (e.g., stripping whitespace)
        df_props['lot_id'] = df_props['lot_id'].astype(str).str.strip()
        df_results['lot_id'] = df_results['lot_id'].astype(str).str.strip()
        
        # Merge datasets on lot_id
        # We use a left join to keep all properties, even those without a result in the PDF
        # Or an inner join if we only want properties with confirmed outcomes.
        # Given the "Auction Data Normalization" context, we likely want to see the outcomes.
        # But for a complete dataset, a left join is safer to identify missing results.
        logger.info("Merging datasets on lot_id...")
        df_joined = pd.merge(
            df_props, 
            df_results, 
            on='lot_id', 
            how='left', 
            suffixes=('_wayback', '_pdf')
        )
        
        # Handle cases where multiple results might exist for the same lot (unlikely but possible)
        # For now, we report the size
        logger.info(f"Joined records count: {len(df_joined)}")
        
        # Clean up column redundancy if they match
        if 'address_wayback' in df_joined.columns and 'address_pdf' in df_joined.columns:
            # Keep wayback address as it's usually cleaner/standardized during trait extraction
            df_joined['address'] = df_joined['address_wayback'].fillna(df_joined['address_pdf'])
            df_joined.drop(columns=['address_wayback', 'address_pdf'], inplace=True)
            
        # Standardize auction_result: if missing, label as "DATO MANCANTE" or similar
        if 'auction_result' in df_joined.columns:
            df_joined['auction_result'] = df_joined['auction_result'].fillna('ESITO NON DISPONIBILE')
            
        # Save consolidated dataset
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving consolidated dataset to {output_file}")
        df_joined.to_csv(output_file, index=False)
        
        # Also save as JSON for easier programmatic consumption
        json_output = output_file.with_suffix('.json')
        df_joined.to_json(json_output, orient='records', indent=2)
        logger.info(f"Saving JSON dataset to {json_output}")
        
        return df_joined

if __name__ == "__main__":
    # Smoke test path
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    props = PROJECT_ROOT / "data" / "extracted_auctions.csv"
    res = PROJECT_ROOT / "data" / "extracted_pdf_results.csv"
    out = PROJECT_ROOT / "data" / "consolidated_auction_dataset.csv"
    
    integrator = DatasetIntegrator(str(props), str(res))
    integrator.integrate(str(out))
