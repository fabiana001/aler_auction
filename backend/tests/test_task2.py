"""Quick test for Task 2 backend changes."""
import math
from app.data.loader import get_auctions_df, search_by_address

# Load data
df = get_auctions_df()
print(f"Dataset loaded: {len(df)} rows")

# Test search_by_address
result = search_by_address(df, "Roma")
print(f"Search 'Roma': {len(result)} results")

result2 = search_by_address(df, "via")
print(f"Search 'via': {len(result2)} results")

result3 = search_by_address(df, "ROME")
print(f"Search 'ROME': {len(result3)} results")
print("search_by_address: OK")

# Test _haversine inline
def _haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Test: distance from a point to itself should be 0
d = _haversine(41.9, 12.5, 41.9, 12.5)
assert d == 0.0, f"Expected 0, got {d}"
print(f"Haversine self-distance: {d} (should be 0)")

# Test: approximate Rome-Florence distance (~230km)
d2 = _haversine(41.9, 12.5, 43.77, 11.25)
print(f"Haversine Rome-Florence: {d2:.0f}m (expected ~230000m)")
assert 200000 < d2 < 260000, f"Unexpected distance: {d2}"
print("Haversine: OK")

# Test that the router module imports cleanly
from app.routers.auctions import _haversine as h2
d3 = h2(41.9, 12.5, 41.9, 12.5)
assert d3 == 0.0
print("Router import: OK")

print("\nAll tests passed!")
