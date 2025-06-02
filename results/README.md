# Results Directory

This directory contains all model outputs, analysis reports, and comparison files generated during the LLM evaluation study.

## Structure

### `model_outputs/`
Raw JSON responses from LLM models:

- **Format**: `{provider}_{model-name}_results_{prompt-version}.json`
- **Content**: Complete model responses with metadata, timing, and error information

**Current Results:**
- `openai_o1_results_v3_prompt.json` - OpenAI O1 with V3 prompts (72 items, 12.5% API success)
- `anthropic_claude-opus-4_results_v3_prompt.json` - Claude Opus 4 with V3 prompts (72 items)
- `anthropic_claude-3.7-sonnet_results_v2_prompt.json` - Claude 3.7 Sonnet with V2 prompts (72 items)
- `meta-llama_llama-3.3-70b-instruct_free_results_v3_prompt.json` - Llama 3.3 70B with V3 prompts (72 items, 100% API success)
- `deepseek_deepseek-r1-distill-qwen-7b_results.json` - DeepSeek model results (partial)

### `analysis_reports/`
Performance analysis summaries and detailed metrics:

- **Format**: `analysis_summary_{model-name}_{prompt-version}.json`
- **Content**: Aggregate performance metrics, statistical tests, detailed per-item results

**Current Reports:**
- `analysis_summary_openai_o1_results_v3_prompt.json`
- `analysis_summary_anthropic_claude-opus-4_results_v3_prompt.json`
- `analysis_summary_anthropic_claude-3.7-sonnet_results_v2_prompt.json`
- `analysis_summary_meta-llama_llama-3.3-70b-instruct_free_results_v3_prompt.json`

### `comparisons/`
Excel files comparing model outputs against ground truth:

- **Format**: `comparison_{model-name}_{prompt-version}_vs_ground_truth.xlsx`
- **Content**: Side-by-side hourly allocations, cost calculations, error metrics

**Current Comparisons:**
- `comparison_openai_o1_results_v3_prompt_vs_ground_truth.xlsx`
- `comparison_anthropic_claude-opus-4_results_v3_prompt_vs_ground_truth.xlsx`
- `comparison_anthropic_claude-3.7-sonnet_results_v2_prompt_vs_ground_truth.xlsx`
- `comparison_meta-llama_llama-3.3-70b-instruct_free_results_v3_prompt_vs_ground_truth.xlsx`

## Result File Formats

### Model Output JSON Structure
```json
[
  {
    "item_index": 1,
    "original_user_prompt": "LED optimization task prompt...",
    "original_assistant_response": {"led_allocations": [...]},
    "model_response": {"led_allocations": [0, 5, 10, ...]},
    "api_call_duration_seconds": 2.45,
    "error_message": "Optional error description"
  }
]
```

### Analysis Summary JSON Structure
```json
{
  "summary": {
    "total_items": 72,
    "successful_items": 72,
    "json_success_rate": 100.0
  },
  "ppfd_performance": {
    "daily_ppfd_mae": 285.42,
    "daily_ppfd_mae_percent": 11.16,
    "daily_ppfd_median_error": 201.35
  },
  "cost_performance": {
    "cost_difference_mean": -0.89,
    "cost_difference_percent_mean": -4.23,
    "cost_p_value": 0.1139,
    "cost_statistically_significant": false
  },
  "accuracy_performance": {
    "hourly_allocation_mae": 31.58,
    "exact_hourly_match_rate": 83.39,
    "hourly_mae_median": 25.0
  }
}
```

## Key Performance Metrics

### Model Performance Summary

| Model | Prompt | API Success | Hourly MAE | Daily PPFD Error | Cost Diff | Exact Matches | P-Value |
|-------|--------|-------------|------------|------------------|-----------|---------------|---------|
| OpenAI O1 | V3 | 12.5% | 0.00007 | 0.0003 (0.00001%) | -0.0000004% | 100.0% | 0.4817 |
| Claude Opus 4 | V3 | 100% | 31.58 | 285.42 (11.16%) | -4.23% | 83.39% | 0.1139 |
| Claude 3.7 Sonnet | V2 | 100% | 46.19 | 340.13 (13.30%) | -8.85% | 78.53% | 0.0214 |

### Interpretation
- **JSON Success Rate**: Percentage of valid JSON responses
- **Hourly MAE**: Mean Absolute Error in LED allocations per hour
- **Daily PPFD Error**: Deviation from target daily light requirements
- **Cost Diff**: Percentage difference from optimal electricity costs
- **Exact Matches**: Percentage of hours with perfect LED allocation prediction
- **P-Value**: Statistical significance of cost differences (p < 0.05 = significant)

## Statistical Significance

### Cost Performance Analysis
- **OpenAI O1 (V3)**: Cost difference NOT statistically significant (p=0.4817)
  - Exceptional accuracy for successful responses (100% exact matches)
  - Low API success rate (12.5%) limits practical applicability
  - When successful, achieves near-perfect optimization performance
  
- **Claude Opus 4 (V3)**: Cost difference NOT statistically significant (p=0.1139)
  - Indicates model costs are statistically indistinguishable from optimal
  - Represents excellent cost optimization performance
  
- **Claude 3.7 Sonnet (V2)**: Cost difference statistically significant (p=0.0214)
  - Model consistently deviates from optimal costs
  - Still shows good directional optimization (negative cost difference)

## Usage Examples

### Loading Model Results
```python
import json
with open('results/model_outputs/anthropic_claude-opus-4_results_v3_prompt.json', 'r') as f:
    results = json.load(f)
```