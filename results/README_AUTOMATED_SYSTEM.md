# Automated Results Generation System

This directory contains an automated system for generating analysis results from model outputs. When you add new model output files, all related analysis files are automatically created.

## 📁 Directory Structure

```
results/
├── model_outputs/          # Place new model output JSON files here
├── analysis_reports/       # Auto-generated analysis summary JSON files  
├── analysis/              # Auto-generated detailed analysis files
├── figures/               # Auto-generated performance figures
├── comparisons/           # Auto-generated Excel comparison files
└── old/                   # Previous results (archived)
    ├── model_outputs/
    ├── analysis_reports/
    ├── analysis/
    ├── figures/
    └── comparisons/
```

## 🚀 How It Works

### 1. **Manual Processing** (Recommended)
Add your model output JSON file to `results/model_outputs/` and run:
```bash
python scripts/auto_generate_results.py [filename.json]
```

Or process all files in the directory:
```bash
python scripts/auto_generate_results.py
```

### 2. **Automatic File Watching** (Optional)
Start the file watcher to automatically process new files:
```bash
python scripts/watch_model_outputs.py
```

This will monitor the `model_outputs/` directory and automatically run analysis when new JSON files are added.

## 📊 Generated Files

For each model output file (e.g., `anthropic_claude-3.5-sonnet_results_v3_prompt.json`), the system generates:

### Analysis Summary JSON
- **Location**: `analysis_reports/analysis_summary_[model_name].json`
- **Contains**: Performance metrics, cost analysis, data quality stats

### Comparison Excel File  
- **Location**: `comparisons/comparison_[model_name]_vs_ground_truth.xlsx`
- **Contains**: Side-by-side comparison of model vs ground truth allocations

### Additional Analysis Files
- Statistical analysis reports
- Performance visualization figures
- Cost comparison charts

## 📋 Requirements

### Python Packages
```bash
pip install pandas numpy scipy openpyxl matplotlib seaborn
```

### For File Watching (Optional)
```bash
pip install watchdog
```

## 🔧 Configuration

The system uses these ground truth data sources:
- **Test data**: `data/input-output pairs json/test_ground_truth.json`
- **Training data**: `data/input-output pairs json/training_ground_truth.json`  
- **Validation data**: `data/input-output pairs json/validation_ground_truth.json`

## 📝 Model Output Format

Your model output JSON files should follow this structure:
```json
[
  {
    "item_index": 1,
    "original_user_prompt": "Context Dump:\nDate: 2024-01-15\n...",
    "openrouter_model_response": {
      "allocation_PPFD_per_hour": {
        "hour_0": 300.0,
        "hour_1": 250.5,
        ...
        "hour_23": 100.0
      }
    }
  }
]
```

## 🔄 Supported File Naming Conventions

The system automatically detects model names and versions from filenames:
- `[model_name]_results.json`
- `[model_name]_results_v2_prompt.json`
- `[model_name]_results_v3_prompt.json`

Examples:
- `anthropic_claude-3.5-sonnet_results_v3_prompt.json`
- `openai_gpt-4o_results_v2_prompt.json`
- `meta-llama_llama-3.3-70b-instruct_free_results.json`

## 📈 Analysis Metrics

### Performance Metrics
- **MAE**: Mean Absolute Error
- **RMSE**: Root Mean Square Error  
- **Correlation**: Pearson correlation coefficient

### Cost Analysis
- **Total Cost**: Model allocation cost vs ground truth cost
- **Cost Difference**: Absolute and percentage differences
- **Cost Efficiency**: Per-unit cost analysis

### Data Quality
- **JSON Success Rate**: Percentage of valid JSON responses
- **Valid Predictions**: Number of usable data points
- **Coverage**: Data completeness metrics

## 🛠️ Troubleshooting

### Common Issues

1. **"Ground truth file not found"**
   - Ensure `data/input-output pairs json/test_ground_truth.json` exists
   - Check file permissions

2. **"No valid predictions found"**
   - Verify your model output JSON format
   - Check that date parsing is working correctly

3. **File watcher not working**
   - Install watchdog: `pip install watchdog`
   - Check directory permissions

### Manual Debugging
```bash
# Test the auto-generate script
python scripts/auto_generate_results.py --debug

# Check ground truth loading
python -c "
import sys; sys.path.append('scripts')
from auto_generate_results import load_ground_truth
print(load_ground_truth().head())
"
```

## 📚 Examples

### Process a Single File
```bash
python scripts/auto_generate_results.py anthropic_claude-3.5-sonnet_results_v3_prompt.json
```

### Process All Files
```bash
python scripts/auto_generate_results.py
```

### Start File Watcher
```bash
python scripts/watch_model_outputs.py
```

## 🗂️ Archive System

All previous results have been moved to the `old/` directory. The current system generates fresh results for each model run, ensuring consistency with the updated datasets and analysis methods.

---

**Note**: This automated system replaces manual analysis workflows and ensures consistent, reproducible results across all model evaluations. 