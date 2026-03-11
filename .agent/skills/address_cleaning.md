# Skill: Address Cleaning

Instructions for normalizing Italian real estate addresses for geocoding.

## Guidelines
1. **Standardize Prefixes**: Ensure "Via", "Viale", "Piazza", "Corso" are correctly identified.
2. **Handle Street Numbers**: Separate street numbers from the street name.
3. **Handle Missing Cities**: Default to "Milan" if no city is specified, as per project scope.
4. **Acronym Expansion**: Expand common abbreviations like "V." to "Via".
