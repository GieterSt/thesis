#!/usr/bin/env python3
"""
Automatic Results Generation Script

This script monitors the results/model_outputs directory and automatically generates
all analysis files when a new model output is added:
- Analysis summary JSON files
- Comparison Excel files  
- Statistical analysis
- Performance figures

Usage:
    python scripts/auto_generate_results.py [model_output_file.json]
    
If no file is specified, it processes all files in results/model_outputs/
"""

import json
import pandas as pd
import numpy as np
import os
import sys
import re
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from scipy.stats import ttest_rel

# Configuration
BASE_DIR = Path(__file__).parent.parent  # Go up to project root
RESULTS_DIR = BASE_DIR / "results"
MODEL_OUTPUTS_DIR = RESULTS_DIR / "model_outputs"
ANALYSIS_REPORTS_DIR = RESULTS_DIR / "analysis_reports"
ANALYSIS_DIR = RESULTS_DIR / "analysis"
FIGURES_DIR = RESULTS_DIR / "figures"
COMPARISONS_DIR = RESULTS_DIR / "comparisons"
SCRIPTS_DIR = BASE_DIR / "scripts"
ANALYSIS_SCRIPTS_DIR = SCRIPTS_DIR / "analysis"

# Ground truth file
GROUND_TRUTH_FILE = BASE_DIR / "data" / "input-output pairs json" / "test_ground_truth.json"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    for dir_path in [ANALYSIS_REPORTS_DIR, ANALYSIS_DIR, FIGURES_DIR, COMPARISONS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_model_name_from_filename(filename):
    """Extract model name and version from filename."""
    if "_results_v3_prompt.json" in filename:
        return filename.replace("_results_v3_prompt.json", ""), "_v3_prompt"
    elif "_results_v2_prompt.json" in filename:
        return filename.replace("_results_v2_prompt.json", ""), "_v2_prompt"
    elif "_results.json" in filename:
        return filename.replace("_results.json", ""), ""
    else:
        return filename.replace(".json", ""), ""

def load_ground_truth():
    """Load and process ground truth data."""
    try:
        with open(GROUND_TRUTH_FILE, 'r') as f:
            ground_truth_data = json.load(f)
        
        # Convert to DataFrame format similar to Excel structure
        gt_rows = []
        for item in ground_truth_data:
            input_data = item['input']
            output_data = item['output']
            date = input_data['date']
            
            # Extract EUR/PPFD rankings and max PPFD capacity
            eur_ppfd_rankings = input_data['eur_ppfd_rankings']
            max_ppfd_capacity = input_data['max_ppfd_capacity']
            
            for hour_data in output_data['hourly_results']:
                hour = hour_data['hour']
                ppfd_allocated = hour_data['ppfd_allocated']
                
                # Get EUR/PPFD for this hour (assuming it's in rankings)
                hour_key = f"hour_{hour}"
                eur_ppfd = eur_ppfd_rankings.get(hour_key, np.nan)
                
                gt_rows.append({
                    'date': date,
                    'hour': hour,
                    'ppfd_allocated': ppfd_allocated,
                    'EUR/PPFD': eur_ppfd,
                    'max_ppfd_capacity': max_ppfd_capacity.get(hour_key, np.nan)
                })
        
        return pd.DataFrame(gt_rows)
    
    except FileNotFoundError:
        print(f"Error: Ground truth file '{GROUND_TRUTH_FILE}' not found.")
        return None
    except Exception as e:
        print(f"Error loading ground truth: {e}")
        return None

def extract_date_from_prompt(prompt_text):
    """Extract date from prompt text."""
    if not prompt_text or not isinstance(prompt_text, str):
        return "UnknownDate"
    
    match = re.search(r"Context Dump:\nDate: (\d{4}-\d{2}-\d{2})", prompt_text)
    if match:
        return match.group(1)
    
    match_fallback = re.search(r"Date: (\d{4}-\d{2}-\d{2})", prompt_text)
    if match_fallback:
        return match_fallback.group(1)
    
    return "UnknownDate"

def parse_model_output(model_file_path):
    """Parse model output file and extract allocations."""
    try:
        with open(model_file_path, 'r', encoding='utf-8') as f:
            model_results = json.load(f)
    except Exception as e:
        print(f"Error loading model file {model_file_path}: {e}")
        return None, 0, 0
    
    model_allocations = []
    valid_json_count = 0
    total_items = len(model_results)
    
    for item_index, result_item in enumerate(model_results):
        item_num = result_item.get("item_index", item_index + 1)
        prompt = result_item.get("original_user_prompt")
        date_str = extract_date_from_prompt(prompt)
        model_response_raw = result_item.get("openrouter_model_response")
        
        hourly_allocations_dict = None
        is_valid_json = False
        
        # Parse model response
        if isinstance(model_response_raw, str):
            try:
                parsed_response = json.loads(model_response_raw)
                if isinstance(parsed_response, dict):
                    if "allocation_PPFD_per_hour" in parsed_response:
                        hourly_allocations_dict = parsed_response["allocation_PPFD_per_hour"]
                    elif "allocation PPFD_per_hour" in parsed_response:
                        hourly_allocations_dict = parsed_response["allocation PPFD_per_hour"]
                    
                    if hourly_allocations_dict and isinstance(hourly_allocations_dict, dict):
                        valid_json_count += 1
                        is_valid_json = True
            except json.JSONDecodeError:
                pass
        elif isinstance(model_response_raw, dict):
            if "allocation_PPFD_per_hour" in model_response_raw:
                hourly_allocations_dict = model_response_raw["allocation_PPFD_per_hour"]
            elif "allocation PPFD_per_hour" in model_response_raw:
                hourly_allocations_dict = model_response_raw["allocation PPFD_per_hour"]
            
            if hourly_allocations_dict and isinstance(hourly_allocations_dict, dict):
                valid_json_count += 1
                is_valid_json = True
        
        # Extract hourly allocations
        for hour in range(24):
            hour_key = f"hour_{hour}"
            ppfd_value = np.nan
            
            if is_valid_json and hourly_allocations_dict:
                raw_val = hourly_allocations_dict.get(hour_key)
                if raw_val is not None:
                    try:
                        ppfd_value = float(raw_val)
                    except (ValueError, TypeError):
                        ppfd_value = np.nan
            
            model_allocations.append({
                'date': date_str,
                'hour': hour,
                'ppfd_allocated_by_model': ppfd_value
            })
    
    return pd.DataFrame(model_allocations), valid_json_count, total_items

def generate_analysis_summary(model_df, ground_truth_df, model_name, valid_json_count, total_items):
    """Generate comprehensive analysis summary."""
    # Merge model and ground truth data
    comparison_df = pd.merge(model_df, ground_truth_df, on=['date', 'hour'], how='left')
    
    # Calculate statistics
    valid_predictions = comparison_df.dropna(subset=['ppfd_allocated_by_model', 'ppfd_allocated'])
    
    if len(valid_predictions) == 0:
        print(f"Warning: No valid predictions found for {model_name}")
        return {}
    
    # Performance metrics
    mae = np.mean(np.abs(valid_predictions['ppfd_allocated_by_model'] - valid_predictions['ppfd_allocated']))
    rmse = np.sqrt(np.mean((valid_predictions['ppfd_allocated_by_model'] - valid_predictions['ppfd_allocated'])**2))
    correlation = valid_predictions['ppfd_allocated_by_model'].corr(valid_predictions['ppfd_allocated'])
    
    # Cost analysis
    if 'EUR/PPFD' in valid_predictions.columns:
        model_cost = (valid_predictions['ppfd_allocated_by_model'] * valid_predictions['EUR/PPFD']).sum()
        ground_truth_cost = (valid_predictions['ppfd_allocated'] * valid_predictions['EUR/PPFD']).sum()
        cost_difference = model_cost - ground_truth_cost
        cost_percentage = (cost_difference / ground_truth_cost * 100) if ground_truth_cost != 0 else 0
    else:
        model_cost = ground_truth_cost = cost_difference = cost_percentage = np.nan
    
    # JSON success rate
    json_success_rate = (valid_json_count / total_items * 100) if total_items > 0 else 0
    
    summary = {
        "model_name": model_name,
        "analysis_timestamp": datetime.now().isoformat(),
        "data_quality": {
            "total_responses": total_items,
            "valid_json_responses": valid_json_count,
            "json_success_rate_percent": json_success_rate,
            "valid_predictions": len(valid_predictions),
            "total_data_points": len(comparison_df)
        },
        "performance_metrics": {
            "mae": float(mae) if not np.isnan(mae) else None,
            "rmse": float(rmse) if not np.isnan(rmse) else None,
            "correlation": float(correlation) if not np.isnan(correlation) else None
        },
        "cost_analysis": {
            "model_total_cost": float(model_cost) if not np.isnan(model_cost) else None,
            "ground_truth_total_cost": float(ground_truth_cost) if not np.isnan(ground_truth_cost) else None,
            "cost_difference": float(cost_difference) if not np.isnan(cost_difference) else None,
            "cost_difference_percentage": float(cost_percentage) if not np.isnan(cost_percentage) else None
        }
    }
    
    return summary

def generate_comparison_excel(model_df, ground_truth_df, model_name, output_path):
    """Generate Excel comparison file."""
    comparison_df = pd.merge(model_df, ground_truth_df, on=['date', 'hour'], how='left')
    
    # Add calculated columns
    comparison_df['difference'] = comparison_df['ppfd_allocated_by_model'] - comparison_df['ppfd_allocated']
    comparison_df['absolute_difference'] = np.abs(comparison_df['difference'])
    
    if 'EUR/PPFD' in comparison_df.columns:
        comparison_df['model_cost'] = comparison_df['ppfd_allocated_by_model'] * comparison_df['EUR/PPFD']
        comparison_df['ground_truth_cost'] = comparison_df['ppfd_allocated'] * comparison_df['EUR/PPFD']
        comparison_df['cost_difference'] = comparison_df['model_cost'] - comparison_df['ground_truth_cost']
    
    # Save to Excel
    comparison_df.to_excel(output_path, index=False)
    print(f"Generated comparison Excel: {output_path}")

def run_existing_analysis_scripts(model_file_name):
    """Run existing analysis scripts if they exist."""
    scripts_to_run = [
        "enhanced_statistical_analysis.py",
        "generate_publication_figures.py",
        "analyze_performance.py"
    ]
    
    original_cwd = os.getcwd()
    
    try:
        # Change to project root directory
        os.chdir(BASE_DIR)
        
        for script in scripts_to_run:
            script_path = ANALYSIS_SCRIPTS_DIR / script
            if script_path.exists():
                try:
                    print(f"Running {script}...")
                    # Modify the script to use the current model file
                    result = subprocess.run([
                        sys.executable, str(script_path)
                    ], cwd=BASE_DIR, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✓ Successfully ran {script}")
                    else:
                        print(f"⚠ Warning running {script}: {result.stderr}")
                except Exception as e:
                    print(f"⚠ Error running {script}: {e}")
    finally:
        os.chdir(original_cwd)

def process_model_output(model_file_path):
    """Process a single model output file and generate all analysis files."""
    model_file_name = model_file_path.name
    print(f"\n{'='*60}")
    print(f"Processing: {model_file_name}")
    print(f"{'='*60}")
    
    # Extract model name and version
    model_name_base, version_suffix = get_model_name_from_filename(model_file_name)
    model_name = f"{model_name_base}{version_suffix}"
    
    # Load ground truth
    print("Loading ground truth data...")
    ground_truth_df = load_ground_truth()
    if ground_truth_df is None:
        print("Failed to load ground truth data. Skipping this model.")
        return
    
    # Parse model output
    print("Parsing model output...")
    model_df, valid_json_count, total_items = parse_model_output(model_file_path)
    if model_df is None:
        print("Failed to parse model output. Skipping this model.")
        return
    
    print(f"Model statistics: {valid_json_count}/{total_items} valid JSON responses")
    
    # Generate analysis summary
    print("Generating analysis summary...")
    analysis_summary = generate_analysis_summary(
        model_df, ground_truth_df, model_name, valid_json_count, total_items
    )
    
    # Save analysis summary
    summary_file = ANALYSIS_REPORTS_DIR / f"analysis_summary_{model_name_base}{version_suffix}.json"
    with open(summary_file, 'w') as f:
        json.dump(analysis_summary, f, indent=2)
    print(f"✓ Generated analysis summary: {summary_file}")
    
    # Generate comparison Excel
    print("Generating comparison Excel...")
    excel_file = COMPARISONS_DIR / f"comparison_{model_name_base}{version_suffix}_vs_ground_truth.xlsx"
    generate_comparison_excel(model_df, ground_truth_df, model_name, excel_file)
    print(f"✓ Generated comparison Excel: {excel_file}")
    
    # Run additional analysis scripts
    print("Running additional analysis scripts...")
    run_existing_analysis_scripts(model_file_name)
    
    print(f"\n✓ Completed processing {model_file_name}")

def main():
    """Main function to process model outputs."""
    ensure_directories()
    
    if len(sys.argv) > 1:
        # Process specific file
        model_file = Path(sys.argv[1])
        if not model_file.is_absolute():
            model_file = MODEL_OUTPUTS_DIR / model_file
        
        if model_file.exists():
            process_model_output(model_file)
        else:
            print(f"Error: File {model_file} not found.")
            sys.exit(1)
    else:
        # Process all files in model_outputs directory
        if not MODEL_OUTPUTS_DIR.exists():
            print(f"Error: Model outputs directory {MODEL_OUTPUTS_DIR} not found.")
            sys.exit(1)
        
        model_files = list(MODEL_OUTPUTS_DIR.glob("*.json"))
        if not model_files:
            print("No JSON files found in model outputs directory.")
            return
        
        print(f"Found {len(model_files)} model output files to process")
        
        for model_file in sorted(model_files):
            try:
                process_model_output(model_file)
            except Exception as e:
                print(f"Error processing {model_file}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print("All processing completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 