# 📊 Modular Analysis Scripts

This directory contains the refactored, modular analysis system for LED optimization LLM evaluation. The original monolithic `auto_analyze_results.py` has been split into focused, maintainable components.

## 🗂️ File Structure

### Core Components

| Script | Purpose | Key Functions |
|--------|---------|---------------|
| `run_analysis.py` | **Main orchestrator** | Coordinates all components, CLI interface |
| `data_loader.py` | **Ground truth & data** | Load test data, calculate scenario complexity |
| `model_analyzer.py` | **Individual model analysis** | Parse model outputs, extract performance metrics |
| `statistical_analyzer.py` | **Statistical analysis** | Correlations, regression, significance testing |
| `visualization_generator.py` | **Figure generation** | Thesis-ready plots with **FIXED model names** |
| `report_generator.py` | **Report creation** | README and HTML report generation |

### Legacy Files
- `auto_analyze_results.py` - Original monolithic script (2200+ lines)

## 🚀 Quick Start

### Run Complete Analysis
```bash
cd analysis_scripts
python run_analysis.py
```

### Monitor for New Results
```bash
python run_analysis.py --monitor
```

### Get Help
```bash
python run_analysis.py --help
```

## ✨ Key Improvements

### 🔧 Fixed Issues
- **✅ Model Naming Bug**: Centralized model name mapping in `visualization_generator.py`
- **✅ Maintainability**: Each component has single responsibility
- **✅ Testing**: Individual components can be tested separately
- **✅ Reusability**: Components can be used independently

### 🎯 Enhanced Features
- **Modular Architecture**: Easy to modify individual analysis steps
- **Centralized Configuration**: Consistent model naming across all outputs
- **Better Error Handling**: Isolated failures don't crash entire analysis
- **Improved Documentation**: Each script is self-documenting

## 📊 Output Structure

```
results/
├── figures/                    # Generated visualizations (PNG)
├── analysis_reports/           # HTML reports + timestamped files
├── analysis/                   # Raw analysis data (JSON)
└── model_outputs/             # Input: Model response files
```

## 🔍 Component Details

### `data_loader.py`
- Loads ground truth optimal solutions
- Calculates scenario complexity scores
- Provides ground truth comparison utilities

### `model_analyzer.py`  
- Parses individual model output files
- Extracts API success, JSON validity, optimization performance
- Maps model names to parameters and specifications

### `statistical_analyzer.py`
- Comprehensive correlation analysis (Pearson, Spearman)
- Bootstrap confidence intervals
- Regression modeling for scaling laws
- Statistical significance testing

### `visualization_generator.py`
- **CRITICAL FIX**: Centralized model name mapping
- Four key figures: Scaling Law, Performance Comparison, Failure Analysis, Heatmap
- Thesis-ready formatting with proper model labels

### `report_generator.py`
- Comprehensive README generation
- HTML report with CSS styling
- Performance rankings and detailed analysis sections

### `run_analysis.py`
- Main entry point and workflow orchestration
- File discovery and validation
- Progress tracking and error reporting
- Monitoring mode for continuous analysis

## 🐛 Bug Fixes Applied

### Model Naming Issue (RESOLVED)
**Problem**: Generic `elif 'deepseek' in model_name.lower():` checks caused both DeepSeek models to be labeled as "DeepSeek Distill"

**Solution**: Centralized exact string matching in `get_clean_model_name()`:
```python
name_mapping = {
    'deepseek-r1-0528-free': 'DeepSeek R1 (671B)',
    'deepseek-r1-distill-qwen-7b': 'DeepSeek Distill (7B)', 
    # ... other mappings
}
```

This ensures:
- ✅ DeepSeek R1 shows as "DeepSeek R1 (671B)"  
- ✅ DeepSeek Distill shows as "DeepSeek Distill (7B)"
- ✅ Consistent naming across all figures and reports

## 🔄 Migration from Original Script

The modular system maintains full compatibility with the original analysis while providing:

1. **Better Code Organization**: 6 focused scripts vs 1 monolithic file
2. **Enhanced Debugging**: Isolate issues to specific components  
3. **Improved Testing**: Test individual functions separately
4. **Easier Maintenance**: Modify specific features without affecting others
5. **Fixed Bugs**: Resolved model naming and other issues

## 📝 Dependencies

Same as original script:
```bash
pip install pandas numpy matplotlib seaborn scipy scikit-learn statsmodels markdown
```

## 🤝 Contributing

When modifying the analysis:

1. **Model Names**: Update mapping in `visualization_generator.py`
2. **New Metrics**: Add to `model_analyzer.py` and `statistical_analyzer.py`
3. **New Plots**: Add functions to `visualization_generator.py`
4. **Report Changes**: Modify `report_generator.py`
5. **Workflow Changes**: Update `run_analysis.py`

This modular approach makes the codebase much more maintainable and debuggable! 