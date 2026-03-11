import logging
import pandas as pd
import hdbscan
import json
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class PriceAnalyzer:
    """Analyzes auction prices and performs spatial clustering to identify zones."""

    def __init__(self, min_cluster_size: int = 20):
        self.min_cluster_size = min_cluster_size

    def analyze_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Performs spatial clustering and calculates price metrics.
        
        Args:
            df: DataFrame containing at least 'lat', 'lng', 'base_price_eur', 'final_offer_eur'.
        
        Returns:
            DataFrame enriched with 'zone_id' and 'price_disparity'.
        """
        df = df.copy()

        # 1. Spatial Clustering
        if 'lat' in df.columns and 'lng' in df.columns:
            # Filter valid coordinates
            valid_coords = df.dropna(subset=['lat', 'lng'])
            if len(valid_coords) >= self.min_cluster_size:
                logger.info(f"Performing HDBSCAN clustering on {len(valid_coords)} records...")
                cls = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size, metric='euclidean')
                df.loc[valid_coords.index, 'zone_id'] = cls.fit_predict(valid_coords[['lat', 'lng']])
                # Convert zone_id to Int64 to handle NaNs and still be integers
                df['zone_id'] = df['zone_id'].astype('Int64')
            else:
                logger.warning(f"Not enough records with valid coordinates ({len(valid_coords)}) for clustering (min={self.min_cluster_size}).")
                df['zone_id'] = None
        else:
            logger.warning("Coordinates 'lat'/'lng' not found in dataset. Skipping clustering.")
            df['zone_id'] = None

        # 2. Price Metrics Calculation
        if 'base_price_eur' in df.columns and 'final_offer_eur' in df.columns and 'surface_sqm' in df.columns:
            logger.info("Calculating price metrics...")
            
            # Price disparity: (final_offer - base_price) / base_price
            mask_disparity = (df['base_price_eur'] > 0) & df['final_offer_eur'].notna()
            df.loc[mask_disparity, 'price_disparity'] = (df.loc[mask_disparity, 'final_offer_eur'] - df.loc[mask_disparity, 'base_price_eur']) / df.loc[mask_disparity, 'base_price_eur']
            
            # 2a. Base Price per square meter
            mask_base_sqm = (df['surface_sqm'] > 0) & df['base_price_eur'].notna()
            df.loc[mask_base_sqm, 'base_price_per_sqm'] = df.loc[mask_base_sqm, 'base_price_eur'] / df.loc[mask_base_sqm, 'surface_sqm']
            
            # 2b. Final Price per square meter (user requested name: final_base_price_eur)
            mask_final_sqm = (df['surface_sqm'] > 0) & df['final_offer_eur'].notna()
            df.loc[mask_final_sqm, 'final_base_price_eur'] = df.loc[mask_final_sqm, 'final_offer_eur'] / df.loc[mask_final_sqm, 'surface_sqm']
        else:
            logger.warning("Required columns for price metrics not found. Skipping calculations.")
            df['price_disparity'] = None
            df['base_price_per_sqm'] = None
            df['final_base_price_eur'] = None

        return df

    def save_enhanced_dataset(self, df: pd.DataFrame, output_path: str | Path):
        """Saves the enriched dataframe to CSV and JSON."""
        path = Path(output_path)
        
        # Save CSV
        df.to_csv(path.with_suffix('.csv'), index=False, encoding='utf-8')
        
        # Save JSON (orient='records' for list of objects)
        # We use json.dumps to handle Int64 and other types if needed, 
        # but pandas to_json is usually sufficient.
        df.to_json(path.with_suffix('.json'), orient='records', indent=2, force_ascii=False)
        
        logger.info(f"Enhanced dataset saved to {path.with_suffix('.csv')} and {path.with_suffix('.json')}")
