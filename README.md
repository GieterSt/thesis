# LLM-Powered Greenhouse LED Optimization - Thesis Project

## 📋 Overview

This repository contains the complete implementation and results for the Master's thesis research on LED lighting optimization using Large Language Models. The core of the repository is a modular, automated analysis pipeline designed to evaluate the performance of various LLMs on a complex, real-world optimization task.

## 🎯 Research Question

How effectively can different Large Language Models optimize LED lighting schedules for plant growth, and what factors (such as model scale) determine their performance?

## 🗂️ Repository Structure

```
├── analysis_scripts/           # Core analysis modules
│   ├── run_analysis.py        # Main orchestrator to run the entire pipeline
│   ├── data_loader.py         # Loads ground truth data
│   ├── model_analyzer.py      # Analyzes a single model's performance
│   ├── statistical_analyzer.py # Performs statistical tests (correlation, regression)
│   ├── visualization_generator.py # Creates thesis-ready figures
│   └── report_generator.py    # Generates final HTML and Markdown reports
├── data/                       # All input data
│   ├── test_sets/             # The 72 test case scenarios
│   └── ground_truth/          # Optimal solutions from the greedy algorithm
├── results/                    # All generated outputs
│   ├── model_outputs/         # Raw JSON responses from the LLMs
│   ├── analysis/              # Processed analysis data
│   ├── figures/               # Final, publication-ready figures
│   └── analysis_reports/      # Generated HTML and Markdown summary reports
├── archive/                    # Legacy scripts and old versions
└── requirements.txt            # Required Python packages
```

## 🚀 Quick Start

### 1. Install Dependencies
Ensure you have Python 3.9+ installed. Then, set up the necessary packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Full Analysis Pipeline
To execute the entire analysis from start to finish, run the main orchestrator script from the root directory:
```bash
python analysis_scripts/run_analysis.py
```
This single command will:
1. Load all data.
2. Analyze every model output file.
3. Perform statistical analysis.
4. Generate all thesis figures (e.g., the log-scaling law plot).
5. Create a timestamped, comprehensive HTML report in `results/analysis_reports/`.

### 3. View the Final Report
The final, human-readable report is the best place to view the results. Find the latest `analysis_report_*.html` file in the `results/analysis_reports/` directory and open it in your web browser.

## 🔬 Methodology & Findings

Detailed information on the methodology, key findings, and statistical results are contained within the final generated HTML report. The system is designed to be fully reproducible, with all data, scripts, and outputs version-controlled.

This codebase demonstrates:
- A systematic LLM evaluation methodology.
- An automated and modular analysis pipeline.
- Statistical rigor in evaluating model performance.
- Discovery and validation of scaling laws in a practical optimization task.
