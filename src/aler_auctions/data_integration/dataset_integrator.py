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

        if df_props.empty:
            logger.error("Properties file is empty")
            return None
        if df_results.empty:
            logger.error("Results file is empty")
            return None

        # Standardize lot_id
        df_props['lot_id'] = df_props['lot_id'].astype(str).str.strip()
        df_results['lot_id'] = df_results['lot_id'].astype(str).str.strip()

        # Deduplicate before merge to avoid cartesian explosion when lot_id appears
        # multiple times in either source (e.g. re-runs, duplicate PDFs).
        props_before = len(df_props)
        results_before = len(df_results)
        df_props = df_props.drop_duplicates(subset=['lot_id'], keep='first')
        df_results = df_results.drop_duplicates(subset=['lot_id'], keep='first')
        if len(df_props) < props_before:
            logger.warning("Dropped %d duplicate lot_id rows from properties", props_before - len(df_props))
        if len(df_results) < results_before:
            logger.warning("Dropped %d duplicate lot_id rows from results", results_before - len(df_results))

        # Full outer join: keep Wayback rows (with property details) AND PDF-only rows (no Wayback snapshot)
        logger.info("Merging datasets on lot_id (outer join)...")
        df_joined = pd.merge(
            df_props,
            df_results,
            on='lot_id',
            how='outer',
            suffixes=('_wayback', '_pdf')
        )

        logger.info(f"Joined records count: {len(df_joined)}")

        # Reconcile address: prefer Wayback (richer), fall back to PDF
        if 'address_wayback' in df_joined.columns and 'address_pdf' in df_joined.columns:
            df_joined['address'] = df_joined['address_wayback'].fillna(df_joined['address_pdf'])
            df_joined.drop(columns=['address_wayback', 'address_pdf'], inplace=True)

        # Reconcile auction_date: prefer Wayback, fall back to PDF-derived date
        if 'auction_date_wayback' in df_joined.columns and 'auction_date_pdf' in df_joined.columns:
            df_joined['auction_date'] = df_joined['auction_date_wayback'].fillna(df_joined['auction_date_pdf'])
            df_joined.drop(columns=['auction_date_wayback', 'auction_date_pdf'], inplace=True)

        # Mark source for transparency
        if 'source_file' in df_joined.columns:
            df_joined['data_source'] = df_joined['source_file'].apply(
                lambda x: 'wayback' if pd.notna(x) else 'pdf_only'
            )

        # Standardize auction_result
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
