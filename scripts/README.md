# Scripts Directory

This directory contains all the Python scripts for data preparation, model testing, and performance analysis.

## Structure

### `data_preparation/`
Scripts for creating and formatting test datasets:

- **`create_test_sets.py`**: Unified script to generate test sets with different prompt versions
- **`create_complete_test_set_ground_truth.py`**: Generate ground truth reference solutions
- **`update_test_set_clod_format.py`**: Format and validate test set structure

#### Legacy Files
- **`create_test_sets_v1.py`**: Original test set generator (V1 prompts)
- **`create_test_sets_v2_v3.py`**: Enhanced test set generator (V2/V3 prompts)

### `model_testing/`
Scripts for testing LLM models via API:

- **`run_model_tests.py`**: Clean, refactored model testing script with CLI interface
- **`run_openrouter_tests.py`**: Legacy model testing script (preserved for reference)

### `analysis/`
Scripts for analyzing model performance:

- **`analyze_performance.py`**: Comprehensive performance analysis with statistical testing
- **`extract_model_allocations_to_excel.py`**: Extract model outputs to Excel format

## Quick Start

### 1. Generate Test Sets
```bash
# Create all prompt versions
cd scripts/data_preparation
python create_test_sets.py --version v1 --output ../../data/test_sets/test_set_v1.json
python create_test_sets.py --version v2 --output ../../data/test_sets/test_set_v2.json
python create_test_sets.py --version v3 --output ../../data/test_sets/test_set_v3.json
```

### 2. Test Models
```bash
# Test Claude Opus 4 with V3 prompts
cd scripts/model_testing
export OPENROUTER_API_KEY="your-api-key-here"
python run_model_tests.py \
  --model anthropic/claude-opus-4 \
  --test-set ../../data/test_sets/test_set_v3.json
```

### 3. Analyze Results
```bash
# Analyze model performance
cd scripts/analysis
python analyze_performance.py \
  --results ../../results/model_outputs/anthropic_claude-opus-4_results_v3_prompt.json \
  --ground-truth ../../data/ground_truth/test_set_ground_truth_complete.xlsx
```

## Script Details

### create_test_sets.py
Generates test datasets with different prompt engineering approaches:

**Arguments:**
- `--version`: Prompt version (v1, v2, v3)
- `--input`: Base test set file (default: data/raw_data/test_set.json)
- `--output`: Output file path

**Prompt Versions:**
- **V1**: Basic task description
- **V2**: Enhanced with role definition, algorithms, examples, validation
- **V3**: Optimized for pure JSON output (no validation text)

### run_model_tests.py
Tests LLM models on LED optimization tasks:

**Arguments:**
- `--model`: Model identifier (e.g., anthropic/claude-opus-4)
- `--test-set`: Path to test set JSON file
- `--api-key`: OpenRouter API key (or use OPENROUTER_API_KEY env var)
- `--start-index`: Resume from specific item (default: 1)
- `--output`: Custom output file path

**Features:**
- Automatic output file naming based on model and prompt version
- JSON response cleaning and validation
- Robust error handling and recovery
- Progress tracking and timing statistics

### analyze_performance.py
Comprehensive performance analysis with statistical testing:

**Arguments:**
- `--results`: Path to model results JSON file
- `--ground-truth`: Path to ground truth Excel file
- `--output-dir`: Output directory for reports

**Analysis Metrics:**
- JSON success rate
- Hourly allocation accuracy (MAE, RMSE)
- Daily PPFD target achievement
- Cost efficiency vs. optimal solutions
- Statistical significance testing
- Exact match rates

**Outputs:**
- JSON analysis summary
- Excel comparison file with detailed breakdowns
- Performance statistics and p-values

## Dependencies

Install required packages:
```bash
pip install pandas numpy openpyxl requests scipy json argparse
```

## Environment Setup

For model testing, set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## Best Practices

### Model Testing
1. Always use V3 prompts for new evaluations (best JSON compliance)
2. Test models in order of expected performance (start with strongest)
3. Monitor API costs and rate limits
4. Save partial results if testing is interrupted

### Analysis
1. Run analysis immediately after model testing
2. Compare results across prompt versions to measure improvement
3. Check statistical significance for cost differences
4. Review Excel outputs for detailed per-scenario insights

### Data Management
1. Follow naming conventions: `{provider}_{model}_results_{prompt_version}.json`
2. Keep separate analysis directories for each model/prompt combination
3. Archive legacy scripts but maintain clean working versions

## Troubleshooting

### Common Issues
- **JSON parsing errors**: Models may return explanatory text - use V3 prompts
- **API timeouts**: Implement resume functionality with `--start-index`
- **Missing ground truth**: Ensure Excel file has all required columns
- **Memory issues**: Process results in batches for very large datasets

### Error Recovery
- Model testing saves progress after each item
- Analysis can handle partial result files
- Use `--start-index` to resume interrupted testing sessions

## Enhanced Retry Logic and Rate Limiting

The model testing script now includes advanced retry logic and rate limiting to improve API success rates, especially for models with strict limitations like OpenAI O1:

### Key Features

**Exponential Backoff Retry Logic:**
- Automatic retry on rate limits, server errors, and timeouts
- Exponential backoff with jitter to avoid thundering herd
- Configurable max retries (default: 5 attempts)

**Model-Specific Rate Limiting:**
- OpenAI O1: 60 seconds between requests (strict rate limits)
- Claude models: 2 seconds between requests
- Other models: 5 seconds between requests

**Intelligent Error Detection:**
- Rate limit detection (429, "rate limit", "quota exceeded")
- Server availability detection (5xx errors, "unavailable")
- Automatic retry for recoverable errors only

### Usage Examples

**Basic OpenAI O1 testing:**
```bash
python run_model_tests.py --model openai/o1 --test-set ../../data/test_sets/test_set_v3.json
```

**Custom retry configuration for improved success rate:**
```bash
python run_model_tests.py --model openai/o1 --test-set ../../data/test_sets/test_set_v3.json \
  --max-retries 10 --base-delay 90 --backoff-factor 1.5 --timeout 300
```

**Resume from failed items:**
```bash
python run_model_tests.py --model openai/o1 --test-set ../../data/test_sets/test_set_v3.json \
  --start-index 25
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-retries` | 5 | Maximum retry attempts per API call |
| `--base-delay` | Auto-detected | Base delay between requests (seconds) |
| `--backoff-factor` | 2.0 | Exponential backoff multiplier |
| `--timeout` | 180 | API request timeout (seconds) |
| `--max-tokens` | Auto-detected | Override model max_tokens parameter |
| `--temperature` | Auto-detected | Override model temperature parameter |

### Model-Specific Optimizations

**OpenAI O1 Models:**
- No temperature parameter (not supported)
- Lower max_tokens limit (4000)
- Extended timeout (180s default)
- Longer delays between requests (60s)

**Claude Models:**
- Standard configuration with faster processing
- Shorter delays (2s) due to better availability 