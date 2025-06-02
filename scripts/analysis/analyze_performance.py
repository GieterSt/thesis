#!/usr/bin/env python3
"""
LLM Performance Analysis for LED Optimization Evaluation

This script analyzes model performance on greenhouse LED scheduling tasks,
comparing model outputs against ground truth optimal solutions.

Usage:
    python analyze_performance.py --results results/model_outputs/claude-opus-4_v3.json --ground-truth data/ground_truth/test_set_ground_truth_complete.xlsx
"""

import json
import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from scipy import stats
from typing import Dict, List, Tuple, Optional

class LEDOptimizationAnalyzer:
    """Analyzer for LED optimization model performance"""
    
    def __init__(self, results_file: str, ground_truth_file: str):
        self.results_file = results_file
        self.ground_truth_file = ground_truth_file
        self.led_power = 275  # μmol/m²/s per LED unit
        
        # Load data
        self.model_results = self._load_model_results()
        self.ground_truth = self._load_ground_truth()
        
    def _load_model_results(self) -> List[Dict]:
        """Load model results from JSON file"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Results file '{self.results_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in results file '{self.results_file}'.")
            sys.exit(1)
    
    def _load_ground_truth(self) -> pd.DataFrame:
        """Load ground truth data from Excel file"""
        try:
            return pd.read_excel(self.ground_truth_file)
        except FileNotFoundError:
            print(f"Error: Ground truth file '{self.ground_truth_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading ground truth file: {e}")
            sys.exit(1)
    
    def extract_led_allocations(self, model_response) -> Optional[List[float]]:
        """Extract PPFD allocations from model response"""
        if not model_response:
            return None
            
        # Handle OpenRouter API response format
        if isinstance(model_response, dict):
            # Check for OpenRouter response format
            if 'openrouter_model_response' in model_response:
                response_data = model_response['openrouter_model_response']
            else:
                response_data = model_response
                
            # Extract allocation data
            if 'allocation_PPFD_per_hour' in response_data:
                allocations = response_data['allocation_PPFD_per_hour']
                # Convert hour_X keys to ordered list
                hourly_values = []
                for hour in range(24):
                    key = f'hour_{hour}'
                    if key in allocations:
                        hourly_values.append(float(allocations[key]))
                    else:
                        hourly_values.append(0.0)
                return hourly_values
            elif 'led_allocations' in response_data:
                return response_data['led_allocations']
            elif 'allocations' in response_data:
                return response_data['allocations']
                
        elif isinstance(model_response, list) and len(model_response) == 24:
            return [float(x) for x in model_response]
            
        return None
    
    def calculate_ppfd_metrics(self, predicted: List[float], target_ppfd: float) -> Dict:
        """Calculate PPFD-related metrics"""
        if not predicted or len(predicted) != 24:
            return {
                'daily_total_ppfd': 0,
                'daily_ppfd_error': float('inf'),
                'daily_ppfd_error_percent': float('inf'),
                'hourly_ppfd': []
            }
        
        # The predicted values are already PPFD allocations
        daily_total = sum(predicted)
        
        return {
            'daily_total_ppfd': daily_total,
            'daily_ppfd_error': abs(daily_total - target_ppfd),
            'daily_ppfd_error_percent': abs(daily_total - target_ppfd) / target_ppfd * 100 if target_ppfd > 0 else float('inf'),
            'hourly_ppfd': predicted
        }
    
    def calculate_cost_metrics(self, predicted: List[float], ground_truth_rows: pd.DataFrame) -> Dict:
        """Calculate electricity cost metrics using ground truth EUR/PPFD values"""
        if not predicted or len(predicted) != 24:
            return {
                'predicted_cost': float('inf'),
                'optimal_cost': 0,
                'cost_difference': float('inf'),
                'cost_difference_percent': float('inf')
            }
        
        # Calculate predicted cost using EUR/PPFD values
        predicted_cost = 0
        optimal_cost = 0
        
        for hour in range(24):
            ppfd_allocation = predicted[hour]
            if hour < len(ground_truth_rows):
                eur_per_ppfd = ground_truth_rows.iloc[hour]['EUR/PPFD']
                hourly_predicted_cost = ppfd_allocation * eur_per_ppfd
                predicted_cost += hourly_predicted_cost
                
                # Optimal cost from ground truth
                optimal_ppfd = ground_truth_rows.iloc[hour]['ppfd_allocated']
                optimal_cost += optimal_ppfd * eur_per_ppfd
        
        cost_diff = predicted_cost - optimal_cost
        cost_diff_percent = (cost_diff / optimal_cost * 100) if optimal_cost != 0 else float('inf')
        
        return {
            'predicted_cost': predicted_cost,
            'optimal_cost': optimal_cost,
            'cost_difference': cost_diff,
            'cost_difference_percent': cost_diff_percent
        }
    
    def calculate_accuracy_metrics(self, predicted: List[float], optimal: List[float]) -> Dict:
        """Calculate allocation accuracy metrics"""
        if not predicted or not optimal or len(predicted) != 24 or len(optimal) != 24:
            return {
                'hourly_mae': float('inf'),
                'hourly_rmse': float('inf'),
                'exact_hourly_matches': 0,
                'exact_match_rate': 0
            }
        
        # Convert to numpy arrays for easier calculation
        pred_array = np.array(predicted)
        opt_array = np.array(optimal)
        
        # Calculate metrics
        mae = np.mean(np.abs(pred_array - opt_array))
        rmse = np.sqrt(np.mean((pred_array - opt_array) ** 2))
        
        # For PPFD values, consider "exact" match within 0.1 tolerance
        exact_matches = np.sum(np.abs(pred_array - opt_array) < 0.1)
        exact_match_rate = exact_matches / 24 * 100
        
        return {
            'hourly_mae': mae,
            'hourly_rmse': rmse,
            'exact_hourly_matches': exact_matches,
            'exact_match_rate': exact_match_rate
        }
    
    def analyze_single_result(self, result: Dict, ground_truth_day: pd.DataFrame) -> Dict:
        """Analyze a single model result against ground truth"""
        item_index = result.get('item_index', 0)
        
        # Extract model allocations from different possible response keys
        model_response = result.get('openrouter_model_response') or result.get('model_response')
        model_allocations = self.extract_led_allocations(model_response)
        
        # Extract ground truth optimal allocations (24 hours for this day)
        optimal_allocations = ground_truth_day['ppfd_allocated'].tolist()
        
        # Get target PPFD (sum of all optimal allocations for the day)
        target_ppfd = sum(optimal_allocations)
        
        # Calculate all metrics
        ppfd_metrics = self.calculate_ppfd_metrics(model_allocations, target_ppfd)
        cost_metrics = self.calculate_cost_metrics(model_allocations, ground_truth_day)
        accuracy_metrics = self.calculate_accuracy_metrics(model_allocations, optimal_allocations)
        
        # Check for JSON parsing success
        json_success = model_allocations is not None
        
        return {
            'item_index': item_index,
            'json_success': json_success,
            'model_allocations': model_allocations,
            'optimal_allocations': optimal_allocations,
            'target_ppfd': target_ppfd,
            **ppfd_metrics,
            **cost_metrics,
            **accuracy_metrics
        }
    
    def run_complete_analysis(self) -> Dict:
        """Run complete analysis on all results"""
        analyses = []
        
        print(f"Analyzing {len(self.model_results)} model results...")
        
        # Group ground truth by date for easier lookup
        ground_truth_by_date = self.ground_truth.groupby('date')
        
        for result in self.model_results:
            item_index = result.get('item_index', 0)
            
            # Extract date from the prompt (need to parse from the original prompt)
            original_prompt = result.get('original_user_prompt', '')
            
            # Try to extract date from prompt
            import re
            date_pattern = r'Date: (\d{4}-\d{2}-\d{2})'
            match = re.search(date_pattern, original_prompt)
            if match:
                date_str = match.group(1)  # Keep as string
                
                if date_str in ground_truth_by_date.groups:
                    gt_day = ground_truth_by_date.get_group(date_str)
                    analysis = self.analyze_single_result(result, gt_day)
                    analyses.append(analysis)
                else:
                    print(f"Warning: No ground truth found for date {date_str}")
            else:
                print(f"Warning: Could not extract date from prompt for item {item_index}")
        
        return self._calculate_aggregate_metrics(analyses)
    
    def _calculate_aggregate_metrics(self, analyses: List[Dict]) -> Dict:
        """Calculate aggregate metrics across all analyses"""
        # Filter successful JSON responses
        successful_analyses = [a for a in analyses if a['json_success']]
        
        if not successful_analyses:
            return {'error': 'No successful JSON responses found'}
        
        # Calculate aggregate metrics
        json_success_rate = len(successful_analyses) / len(analyses) * 100
        
        # PPFD metrics
        daily_ppfd_errors = [a['daily_ppfd_error'] for a in successful_analyses]
        daily_ppfd_error_percents = [a['daily_ppfd_error_percent'] for a in successful_analyses]
        
        # Cost metrics
        cost_differences = [a['cost_difference'] for a in successful_analyses]
        cost_difference_percents = [a['cost_difference_percent'] for a in successful_analyses]
        
        # Accuracy metrics
        hourly_maes = [a['hourly_mae'] for a in successful_analyses]
        exact_match_rates = [a['exact_match_rate'] for a in successful_analyses]
        
        # Statistical significance test for cost differences
        cost_p_value = None
        if cost_differences:
            t_stat, p_value = stats.ttest_1samp(cost_differences, 0)
            cost_p_value = p_value
        
        # Seasonal analysis
        seasonal_metrics = self._analyze_seasonal_performance(successful_analyses)
        
        return {
            'summary': {
                'total_items': len(analyses),
                'successful_items': len(successful_analyses),
                'json_success_rate': json_success_rate
            },
            'ppfd_performance': {
                'daily_ppfd_mae': np.mean(daily_ppfd_errors),
                'daily_ppfd_mae_percent': np.mean(daily_ppfd_error_percents),
                'daily_ppfd_median_error': np.median(daily_ppfd_errors)
            },
            'cost_performance': {
                'cost_difference_mean': np.mean(cost_differences),
                'cost_difference_percent_mean': np.mean(cost_difference_percents),
                'cost_difference_median': np.median(cost_differences),
                'cost_p_value': cost_p_value,
                'cost_statistically_significant': cost_p_value < 0.05 if cost_p_value else False
            },
            'accuracy_performance': {
                'hourly_allocation_mae': np.mean(hourly_maes),
                'exact_hourly_match_rate': np.mean(exact_match_rates),
                'hourly_mae_median': np.median(hourly_maes)
            },
            'seasonal_analysis': seasonal_metrics,
            'detailed_results': analyses
        }
    
    def _analyze_seasonal_performance(self, analyses: List[Dict]) -> Dict:
        """Analyze performance by season"""
        # This would require date information in the ground truth
        # For now, return placeholder
        return {
            'spring': {'count': 0, 'avg_accuracy': 0},
            'summer': {'count': 0, 'avg_accuracy': 0},
            'autumn': {'count': 0, 'avg_accuracy': 0},
            'winter': {'count': 0, 'avg_accuracy': 0}
        }
    
    def save_analysis_report(self, analysis_results: Dict, output_dir: str) -> str:
        """Save analysis results to JSON file"""
        # Generate output filename
        model_name = Path(self.results_file).stem
        output_file = f"{output_dir}/analysis_summary_{model_name}.json"
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        return output_file
    
    def create_comparison_excel(self, analysis_results: Dict, output_dir: str) -> str:
        """Create Excel comparison file"""
        model_name = Path(self.results_file).stem
        output_file = f"{output_dir}/comparison_{model_name}_vs_ground_truth.xlsx"
        
        # Prepare data for Excel
        detailed_results = analysis_results.get('detailed_results', [])
        
        rows = []
        for result in detailed_results:
            if not result['json_success']:
                continue
                
            # Create row with comparison data
            row = {
                'Item_Index': result['item_index'],
                'JSON_Success': result['json_success'],
                'Target_PPFD': result['target_ppfd'],
                'Predicted_Daily_PPFD': result['daily_total_ppfd'],
                'Daily_PPFD_Error': result['daily_ppfd_error'],
                'Daily_PPFD_Error_Percent': result['daily_ppfd_error_percent'],
                'Predicted_Cost': result['predicted_cost'],
                'Optimal_Cost': result['optimal_cost'],
                'Cost_Difference': result['cost_difference'],
                'Cost_Difference_Percent': result['cost_difference_percent'],
                'Hourly_MAE': result['hourly_mae'],
                'Exact_Hourly_Matches': result['exact_hourly_matches'],
                'Exact_Match_Rate': result['exact_match_rate']
            }
            
            # Add hourly allocations
            if result['model_allocations']:
                for hour in range(24):
                    row[f'Model_LED_Hour_{hour}'] = result['model_allocations'][hour]
            
            if result['optimal_allocations']:
                for hour in range(24):
                    row[f'Optimal_LED_Hour_{hour}'] = result['optimal_allocations'][hour]
            
            rows.append(row)
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(rows)
        df.to_excel(output_file, index=False)
        
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Analyze LLM performance on LED optimization tasks')
    parser.add_argument('--results', required=True, help='Path to model results JSON file')
    parser.add_argument('--ground-truth', default='data/ground_truth/test_set_ground_truth_complete.xlsx',
                       help='Path to ground truth Excel file')
    parser.add_argument('--output-dir', default='results/analysis_reports',
                       help='Output directory for analysis reports')
    
    args = parser.parse_args()
    
    print(f"Analyzing model results: {args.results}")
    print(f"Ground truth file: {args.ground_truth}")
    
    # Initialize analyzer
    analyzer = LEDOptimizationAnalyzer(args.results, args.ground_truth)
    
    # Run analysis
    analysis_results = analyzer.run_complete_analysis()
    
    if 'error' in analysis_results:
        print(f"Analysis failed: {analysis_results['error']}")
        sys.exit(1)
    
    # Save results
    summary_file = analyzer.save_analysis_report(analysis_results, args.output_dir)
    excel_file = analyzer.create_comparison_excel(analysis_results, args.output_dir)
    
    # Print summary
    summary = analysis_results['summary']
    ppfd = analysis_results['ppfd_performance']
    cost = analysis_results['cost_performance'] 
    accuracy = analysis_results['accuracy_performance']
    
    print(f"\n--- Analysis Complete ---")
    print(f"Analysis summary saved to: {summary_file}")
    print(f"Excel comparison saved to: {excel_file}")
    print(f"\n--- Performance Summary ---")
    print(f"JSON Success Rate: {summary['json_success_rate']:.1f}%")
    print(f"Daily PPFD MAE: {ppfd['daily_ppfd_mae']:.2f} ({ppfd['daily_ppfd_mae_percent']:.2f}%)")
    print(f"Cost Difference: {cost['cost_difference_percent_mean']:.2f}%")
    print(f"Cost Statistically Significant: {cost['cost_statistically_significant']}")
    print(f"Hourly Allocation MAE: {accuracy['hourly_allocation_mae']:.2f}")
    print(f"Exact Hourly Match Rate: {accuracy['exact_hourly_match_rate']:.2f}%")

if __name__ == "__main__":
    main() 