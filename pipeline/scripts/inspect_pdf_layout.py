import pdfplumber
from pathlib import Path

def inspect_pdf_text(pdf_path):
    print(f"--- Inspecting text for {pdf_path.name} ---")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"\n--- Page {i+1} ---")
                text = page.extract_text()
                if text:
                    print(text[:1000]) # First 1000 chars
                else:
                    print("No text extracted from page.")
                
                # Check for any objects that might indicate a table but aren't being caught
                # e.g. lines, rects
                print(f"Number of lines: {len(page.lines)}")
                print(f"Number of rects: {len(page.rects)}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sample_pdf = Path("data/historical_auction_data/esito-27novembre2025.pdf")
    if sample_pdf.exists():
        inspect_pdf_text(sample_pdf)
    else:
        print(f"File {sample_pdf} not found.")
