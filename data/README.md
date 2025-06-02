# Data Directory

This directory contains all test datasets, ground truth reference solutions, and raw data files used in the LLM evaluation study.

## Structure

### `test_sets/`
Contains the test datasets with different prompt versions for model evaluation:

- **`test_set_v1.json`**: Original basic prompts
- **`test_set_v2.json`**: Enhanced prompts with detailed instructions, role definition, and examples
- **`test_set_v3.json`**: Refined prompts optimized for pure JSON output (removed validation instructions)

Each test set contains 72 unique scenarios covering:
- Full year coverage (2024-2025)
- Seasonal variation in growing requirements
- Variable electricity pricing throughout the year
- Daily PPFD targets ranging from 15-35 mol/m²/day

### `ground_truth/`
Contains reference optimal solutions and index files:

- **`test_set_ground_truth_complete.xlsx`**: Complete ground truth with optimal LED allocations and costs for all 72 scenarios
- **`test_set_date_hour_index.xlsx`**: Index mapping test items to specific dates and hours

### `raw_data/`
Contains original source data files:

- **`test_set.json`**: Original unprocessed test set before prompt engineering
- **`model_data_prep.xlsx`**: Raw data preparation workbook with electricity prices, SSRD data, and calculations

## Data Format

### Test Set JSON Structure
```json
[
  {
    "messages": [
      {
        "role": "user",
        "content": "Optimization prompt with specific scenario data..."
      },
      {
        "role": "assistant", 
        "content": "{\"led_allocations\": [optimal allocations for 24 hours]}"
      }
    ]
  }
]
```

### Ground Truth Excel Columns
- `Item_Index`: Test item identifier (1-72)
- `Date`: Scenario date
- `Daily_PPFD_Target`: Required daily light (mol/m²/day)
- `Electricity_Price_Hour_0` to `Electricity_Price_Hour_23`: Hourly electricity prices (€/kWh)
- `Optimal_LED_Hour_0` to `Optimal_LED_Hour_23`: Optimal LED allocations
- `Optimal_Cost`: Minimum possible electricity cost (€)

## Usage

The test sets are designed to be used with the model testing scripts:

```bash
# Test with V3 prompts (recommended)
python scripts/model_testing/run_model_tests.py \
  --model anthropic/claude-opus-4 \
  --test-set data/test_sets/test_set_v3.json

# Analyze results against ground truth
python scripts/analysis/analyze_performance.py \
  --results results/model_outputs/anthropic_claude-opus-4_results_v3_prompt.json \
  --ground-truth data/ground_truth/test_set_ground_truth_complete.xlsx
```

## Key Metrics

The ground truth solutions achieve:
- **100% PPFD target achievement**: All scenarios meet exact daily requirements
- **Optimal cost efficiency**: Minimum possible electricity costs given constraints
- **Temporal optimization**: LED schedules prioritize low-cost electricity hours

## Data Integrity

All test scenarios are validated for:
- Feasibility: PPFD targets achievable with available LED capacity
- Realism: Based on actual 2024-2025 electricity price patterns
- Consistency: Aligned seasonal growing requirements and solar radiation data 