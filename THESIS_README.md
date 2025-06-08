# LED Optimization with Large Language Models - Thesis Submission

## 📋 Overview

This repository contains the complete implementation and results for the Master's thesis research on LED lighting optimization using Large Language Models.

## 🎯 Research Question

How effectively can different Large Language Models optimize LED lighting schedules for plant growth, and what factors determine their performance?

## 🗂️ Repository Structure

### Core Analysis System
- **`auto_analyze_results.py`** - Main comprehensive analysis framework
- **`requirements.txt`** - Python dependencies

### Model Testing Scripts
- **`run_deepseek_r1_0528_v2_test.py`** - Best performing model (DeepSeek R1 0528, 95.8% success)
- **`run_claude_3_7_sonnet_test.py`** - High-performance model (Claude 3.7 Sonnet, 79.5% success)

### Data
- **`data/test_sets/test_dataset_v2_prompts_clean.json`** - Final test dataset (72 scenarios)
- **`data/input-output pairs json/test_ground_truth.json`** - Optimal solutions from greedy algorithm

### Results
- **`results/model_outputs/`** - All model response files
- **`results/analysis/master_analysis_*.json`** - Comprehensive analysis results
- **`results/figures/`** - Research visualizations

### Documentation
- **`README.md`** - Auto-generated comprehensive research summary
- **`docs/LLM_LED_Optimization_Research_Results.html`** - Publication-ready HTML report

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Comprehensive Analysis
```bash
python auto_analyze_results.py
```

### 3. View Results
- Open `README.md` for complete research summary
- Open `docs/LLM_LED_Optimization_Research_Results.html` in browser
- Check `results/figures/` for visualizations

## 📊 Key Results

### Model Performance Summary
- **DeepSeek R1 0528**: 95.8% success rate (69/72 responses)
- **Claude 3.7 Sonnet**: 79.5% success rate (57/72 responses)  
- **Llama 3.3 70B**: 54% success rate (39/72 responses)
- **Mistral 7B**: 20.8% success rate (15/72 responses)
- **DeepSeek R1 Distill 7B**: 0.7% success rate (1/144 responses)

### Critical Findings
- **132× performance increase** from DeepSeek 7B (0.7%) to 671B (95.8%)
- **Two-stage failure pipeline**: JSON Generation → Optimization Success
- **Parameter scaling correlation**: Strong relationship between model size and performance
- **Production threshold**: >200B parameters needed for reliable performance

## 🔬 Methodology

### Test Dataset
- 72 diverse LED scenarios
- Range: 5-18 hours lighting duration
- Varied constraints: energy budgets, seasonal requirements
- Ground truth from greedy algorithm optimization

### Evaluation Metrics
- JSON compliance rate
- Optimization success rate (±5% energy tolerance)
- Two-stage failure analysis
- Statistical correlation analysis (n=5 models)

### Analysis Framework
- Automated comprehensive analysis system
- Bootstrap correlation analysis (1000 iterations)
- Scaling law parameter fitting
- Real-time monitoring and README generation

## 📈 Reproducibility

All results are fully reproducible:
1. Test dataset and ground truth are version-controlled
2. Model API calls are logged with exact parameters
3. Analysis system is deterministic with fixed random seeds
4. Complete audit trail in git history

## 🎓 Thesis Integration

This codebase demonstrates:
- Systematic LLM evaluation methodology
- Automated analysis pipeline development
- Statistical rigor with proper sample sizes
- Scaling law discovery and validation
- Production deployment considerations

The research provides concrete evidence for parameter scaling effects in optimization tasks and establishes practical thresholds for LLM deployment in engineering applications. 