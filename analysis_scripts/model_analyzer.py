#!/usr/bin/env python3
"""
INDIVIDUAL MODEL ANALYSIS
Handles analysis of single model performance and parameter extraction
"""
import json
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
import re
from pathlib import Path
from data_loader import calculate_ground_truth_metrics

def extract_model_parameters(model_name):
    """Extract model parameters from model name using pattern matching"""
    model_name_lower = model_name.lower()
    
    # More specific patterns for different models - ordered by specificity
    parameter_map = {
        # DeepSeek models - check most specific first
        'deepseek-r1-0528': {'parameters': 671, 'architecture': 'MoE', 'type': 'Reasoning'},
        'deepseek_deepseek-r1-0528': {'parameters': 671, 'architecture': 'MoE', 'type': 'Reasoning'},
        'deepseek-r1-distill': {'parameters': 7, 'architecture': 'Dense', 'type': 'Distilled'},
        'deepseek_deepseek-r1-distill': {'parameters': 7, 'architecture': 'Dense', 'type': 'Distilled'},
        
        # Other models - exact patterns
        'claude-3-7-sonnet': {'parameters': 200, 'architecture': 'Dense', 'type': 'Multi-modal'},
        'anthropic_claude-3.7-sonnet': {'parameters': 200, 'architecture': 'Dense', 'type': 'Multi-modal'},
        'llama-3.3-70b': {'parameters': 70, 'architecture': 'Dense', 'type': 'Instruction'},
        'meta-llama_llama-3.3-70b': {'parameters': 70, 'architecture': 'Dense', 'type': 'Instruction'},
        'mistral-7b': {'parameters': 7, 'architecture': 'Dense', 'type': 'Instruction'},
        'mistralai_mistral-7b': {'parameters': 7, 'architecture': 'Dense', 'type': 'Instruction'},
        
        # Generic fallbacks (less specific)
        'claude': {'parameters': 200, 'architecture': 'Dense', 'type': 'Multi-modal'},
        'llama': {'parameters': 70, 'architecture': 'Dense', 'type': 'Instruction'},
        'mistral': {'parameters': 7, 'architecture': 'Dense', 'type': 'Instruction'},
        'deepseek': {'parameters': 7, 'architecture': 'Dense', 'type': 'Distilled'},  # Fallback to smaller DeepSeek
    }
    
    # Check for matches, most specific first
    for pattern, params in parameter_map.items():
        if pattern in model_name_lower:
            return params
    
    # Default fallback
    return {'parameters': 1, 'architecture': 'Unknown', 'type': 'Unknown'}

def assign_performance_grade(metrics):
    """Assign performance grade based on hourly success rate criteria"""
    api_success = metrics['basic_performance']['api_success_rate']
    json_success = metrics['basic_performance']['json_success_rate']
    
    if metrics['ground_truth_analysis']:
        hourly_success = metrics['ground_truth_analysis']['mean_hourly_match_rate']
        
        # Grade based on hourly success rates as defined in methodology
        if hourly_success > 95:
            return "🏆 **A+ (Exceptional)**"
        elif hourly_success > 85:
            return "🥇 **A (Excellent)**"
        elif hourly_success > 75:
            return "🥈 **B (Good)**"
        elif hourly_success > 60:
            return "🥉 **C (Acceptable)**"
        elif hourly_success > 40:
            return "📊 **D (Poor)**"
        else:
            return "❌ **F (Failed)**"
    else:
        # Fallback for models without ground truth analysis
        # Use JSON success as proxy for performance
        if json_success > 85:
            return "🥈 **B (Good)**"
        elif json_success > 60:
            return "🥉 **C (Acceptable)**"
        elif json_success > 40:
            return "📊 **D (Poor)**"
        else:
            return "❌ **F (Failed)**"

def analyze_single_model(filepath):
    """Analyze single model output file"""
    print(f"\n📂 Analyzing: {filepath}")
    
    model_name = os.path.basename(filepath).replace('.json', '').replace('results_', '')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic metrics
        total_responses = len(data)
        valid_json_count = 0
        api_success_count = 0
        parsing_errors = []
        
        # Ground truth comparison data
        ground_truth_comparisons = []
        hourly_allocations = []
        
        for i, item in enumerate(data):
            # Check if item has valid openrouter_model_response
            if 'openrouter_model_response' in item and item['openrouter_model_response']:
                api_success_count += 1
                
                try:
                    # The response is already parsed JSON in openrouter_model_response
                    parsed_json = item['openrouter_model_response']
                    valid_json_count += 1
                    
                    # Extract hourly allocations for ground truth comparison
                    if 'allocation_PPFD_per_hour' in parsed_json:
                        model_allocations = {}
                        for hour_key, ppfd_value in parsed_json['allocation_PPFD_per_hour'].items():
                            model_allocations[hour_key] = ppfd_value
                        
                        hourly_allocations.append(model_allocations)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    parsing_errors.append(f"Item {i}: {str(e)}")
            else:
                parsing_errors.append(f"Item {i}: Missing or empty openrouter_model_response")
        
        # Calculate basic performance metrics
        api_success_rate = (api_success_count / total_responses) * 100 if total_responses > 0 else 0
        json_success_rate = (valid_json_count / total_responses) * 100 if total_responses > 0 else 0
        
        # Performance metrics
        basic_performance = {
            'total_responses': total_responses,
            'api_success_count': api_success_count,
            'api_success_rate': api_success_rate,
            'valid_json_count': valid_json_count,
            'json_success_rate': json_success_rate,
            'parsing_errors': len(parsing_errors)
        }
        
        # Model parameters
        model_params = extract_model_parameters(model_name)
        
        # Compile all metrics
        metrics = {
            'model_name': model_name,
            'filepath': filepath,
            'timestamp': datetime.now().isoformat(),
            'model_parameters': model_params,
            'basic_performance': basic_performance,
            'ground_truth_analysis': None,  # Will be filled by ground truth comparison
            'hourly_allocations': hourly_allocations,
            'parsing_errors': parsing_errors[:10],  # Keep only first 10 errors
            'absolute_counts': {
                'total_scenarios_tested': total_responses,
                'valid_json_responses': valid_json_count,
                'failed_responses': total_responses - api_success_count,
                'parsing_failures': len(parsing_errors)
            }
        }
        
        print(f"✅ {model_name}: API {api_success_rate:.1f}%, JSON {json_success_rate:.1f}%")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error analyzing {filepath}: {e}")
        return None

def process_ground_truth_comparison(metrics, ground_truth, hourly_allocations_list):
    """Add ground truth comparison to existing metrics"""
    if not metrics or not ground_truth:
        return metrics
    
    model_name = metrics['model_name']
    total_scenarios_tested = metrics['absolute_counts']['total_scenarios_tested']

    print(f"\n🎯 Ground Truth Comparison: {model_name}")
    
    # Process each scenario to determine its MAE (or penalty)
    all_maes = []
    ground_truth_comparisons = []
    
    # We iterate up to the total number of scenarios tested
    for i in range(total_scenarios_tested):
        # Check if a valid, complete allocation exists for this scenario index
        if i < len(hourly_allocations_list) and isinstance(hourly_allocations_list[i], dict) and len(hourly_allocations_list[i]) == 24:
            # This is a successful, complete response
            model_allocations = hourly_allocations_list[i]
            comparison = calculate_ground_truth_metrics(model_allocations, ground_truth, i)
            if comparison:
                all_maes.append(comparison['daily_absolute_error'])
                ground_truth_comparisons.append(comparison)
        else:
            # This is a failure (API error, JSON error, or incomplete allocation)
            all_maes.append(10000.0)
            # We still need a placeholder in the comparisons list for stats, but with failure indicators
            failure_comp = {
                'exact_24h_match': False, 'hourly_matches': 0, 'hourly_match_rate': 0,
                'mean_absolute_error': 10000.0, 'daily_absolute_error': 10000.0,
                'daily_relative_error': float('inf'), 'total_model_ppfd': 0,
                'total_optimal_ppfd': ground_truth[i]['optimal_allocations'] if i in ground_truth else 0,
                'scenario_complexity': ground_truth[i]['scenario_complexity'] if i in ground_truth else {}
            }
            ground_truth_comparisons.append(failure_comp)
    
    if ground_truth_comparisons:
        # Calculate aggregate metrics from the full list of comparisons
        exact_matches = sum(1 for comp in ground_truth_comparisons if comp['exact_24h_match'])
        total_hourly_matches = sum(comp['hourly_matches'] for comp in ground_truth_comparisons)
        
        # Calculate success rates based on TOTAL SCENARIOS TESTED
        total_possible_hourly_matches = total_scenarios_tested * 24
        
        true_hourly_match_rate = (total_hourly_matches / total_possible_hourly_matches * 100) if total_possible_hourly_matches > 0 else 0
        true_exact_match_rate = (exact_matches / total_scenarios_tested * 100) if total_scenarios_tested > 0 else 0
        
        # Mean Daily MAE should only be calculated over successful runs
        successful_maes = [comp['daily_absolute_error'] for comp in ground_truth_comparisons if comp['daily_absolute_error'] < 10000.0]
        mean_daily_mae = np.mean(successful_maes) if successful_maes else float('inf')

        # The new Success-Weighted MAE is the mean of all MAEs (including penalties)
        mean_success_weighted_mae = np.mean(all_maes) if all_maes else 0
        
        ground_truth_analysis = {
            'total_scenarios_tested': total_scenarios_tested,
            'scenarios_with_valid_responses': len(successful_maes),
            'exact_24h_matches': exact_matches,
            'exact_24h_match_rate': true_exact_match_rate,
            'total_hourly_matches': total_hourly_matches,
            'mean_hourly_match_rate': true_hourly_match_rate,
            'mean_daily_mae': mean_daily_mae,
            'mean_success_weighted_mae': mean_success_weighted_mae,
            'ground_truth_comparisons': ground_truth_comparisons
        }
        
        metrics['ground_truth_analysis'] = ground_truth_analysis
        
        print(f"📊 {model_name}: {true_hourly_match_rate:.1f}% hourly accuracy, {exact_matches} exact matches")
    
    return metrics 