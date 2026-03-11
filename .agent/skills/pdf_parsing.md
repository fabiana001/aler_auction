# Skill: PDF Parsing

Techniques for extracting tables and text from Italian auction PDFs.

## Guidelines
1. **Tabular Identification**: Locate headers like "LOTTO", "INDIRIZZO", "PREZZO".
2. **Text Cleaning**: Strip newline characters mid-sentence.
3. **Layout Analysis**: Handle multi-page tables where headers are repeated.
4. **Encoding**: Ensure UTF-8 handling for Italian accents (à, è, ì, ò, ù).
