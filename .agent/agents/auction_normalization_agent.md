name: auction_normalization_agent
description: Normalize and transform raw auction data.
model: gpt-4.1
instructions: |
  Apply transformations to normalize raw auction data from both `Wayback Discovery` and `Auction Extraction`.
  Input data comes from `auction_extraction_agent`.
  Handle currency conversion, date formatting, and lot_id standardization.
memory: project
tools:
  - data_transformer