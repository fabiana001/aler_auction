import tabula
import pandas as pd
from pathlib import Path

def test_extraction(pdf_path):
    print(f"--- Testing extraction for {pdf_path.name} ---")
    try:
        # read_pdf returns a list of DataFrames
        # lattice=True is often good for tables with clear grid lines
        dfs = tabula.read_pdf(pdf_path, pages='all', lattice=True)
        
        if not dfs:
            print("No tables found with lattice=True, trying stream=True...")
            dfs = tabula.read_pdf(pdf_path, pages='all', stream=True)
            
        for i, df in enumerate(dfs):
            print(f"\nTable {i+1}:")
            print(df.head(10))
            # Save to CSV for manual inspection
            output_csv = Path(f"/tmp/table_{pdf_path.stem}_{i+1}.csv")
            df.to_csv(output_csv, index=False)
            print(f"Saved to {output_csv}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sample_pdf = Path("data/historical_auction_data/esito-27novembre2025.pdf")
    if sample_pdf.exists():
        test_extraction(sample_pdf)
    else:
        print(f"File {sample_pdf} not found.")
