# Skill: Geocoding

Patterns and best practices for converting addresses to coordinates.

## Guidelines
1. **API Selection**: Use Google Maps API or OpenStreetMap depending on availability.
2. **Rate Limiting**: Implementation of delays between requests to respect provider limits.
3. **Fallback Logic**: Search for the street if the specific number fails.
4. **Validation**: Check coordinates are within the Milan metropolitan area.
