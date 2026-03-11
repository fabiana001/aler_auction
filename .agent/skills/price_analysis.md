# Skill: Price Analysis

Methods for analyzing auction price trends and disparities.

## Guidelines
1. **Price Disparity**: Calculate `(final_offer - base_price) / base_price`.
2. **Market Comparison**: Compare auction base prices with average market values in the same neighborhood.
3. **Seasonality**: Track how results vary across different months/years.
4. **Success Rate**: Calculate the ratio of SOLD vs DESERTED lots per zone. Zone is computed using DBSCAN clustering on the geocoded coordinates.
