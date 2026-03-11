name: dataset_integration_agent
description: Join property features with auction results.
model: gpt-4.1
instructions: |
  1. Load normalized property data and auction results data.
  2. Join the two datasets using `lot_id` as the primary key.
  3. Validate that every structural record has a corresponding (or correctly null) result record.
  4. Produce the final integrated CSV/Database.
memory: project
tools:
  - pandas
