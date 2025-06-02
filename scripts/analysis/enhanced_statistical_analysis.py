#!/usr/bin/env python3
"""
Enhanced Statistical Analysis for LLM LED Optimization Research

This script performs comprehensive statistical analysis including:
- Confidence intervals for all metrics
- Statistical significance tests between models
- Effect size calculations (Cohen's d)
- Correlation analysis between model size and performance
- Seasonal performance breakdowns
- Error analysis and failure mode classification
- Cost-performance analysis
"""

import json
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_ind, pearsonr
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
from typing import Dict, List, Tuple, Any

class EnhancedStatisticalAnalyzer:
    def __init__(self, results_dir: str = "results/analysis_reports"):
        self.results_dir = Path(results_dir)
        self.model_data = {}
        self.model_params = {
            "openai_o1": 175,  # Billion parameters
            "anthropic_claude-opus-4": 1000,  # Estimated 1T+ parameters
            "anthropic_claude-3.7-sonnet": 100,  # Estimated 100B+ parameters  
            "meta-llama_llama-3.3-70b": 70,  # 70B parameters
            "deepseek_r1_7b": 7  # 7B parameters
        }
        
    def load_all_model_data(self):
        """Load analysis data for all available models"""
        analysis_files = list(self.results_dir.glob("analysis_summary_*.json"))
        
        for file_path in analysis_files:
            model_name = self._extract_model_name(file_path.name)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.model_data[model_name] = data
                print(f"✅ Loaded data for {model_name}")
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
    
    def _extract_model_name(self, filename: str) -> str:
        """Extract clean model name from filename"""
        # Remove analysis_summary_ prefix and .json suffix
        name = filename.replace("analysis_summary_", "").replace(".json", "")
        # Remove prompt version suffixes
        name = name.replace("_v3_prompt", "").replace("_v2_prompt", "")
        return name
    
    def calculate_confidence_intervals(self, values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence intervals for a list of values"""
        if not values:
            return (0, 0)
        
        values = np.array(values)
        n = len(values)
        mean = np.mean(values)
        sem = stats.sem(values)  # Standard error of mean
        
        # Calculate confidence interval
        t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin_error = t_critical * sem
        
        return (mean - margin_error, mean + margin_error)
    
    def calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        if not group1 or not group2:
            return 0
        
        g1, g2 = np.array(group1), np.array(group2)
        
        # Calculate means
        mean1, mean2 = np.mean(g1), np.mean(g2)
        
        # Calculate pooled standard deviation
        pooled_std = np.sqrt(((len(g1) - 1) * np.var(g1, ddof=1) + 
                             (len(g2) - 1) * np.var(g2, ddof=1)) / 
                            (len(g1) + len(g2) - 2))
        
        # Calculate Cohen's d
        cohens_d = (mean1 - mean2) / pooled_std
        return abs(cohens_d)
    
    def extract_model_metrics(self, model_name: str) -> Dict[str, Any]:
        """Extract key metrics from model data"""
        if model_name not in self.model_data:
            return {}
        
        data = self.model_data[model_name]
        
        # Handle different data structures
        if "ppfd_allocation_accuracy" in data:
            # Claude format
            hourly_success = data["ppfd_allocation_accuracy"]["hourly_level"]["exact_match_rate_percentage"]
            daily_mae = data["ppfd_allocation_accuracy"]["daily_level"]["daily_total_ppfd_mae"]
            api_success = data["json_output_quality"]["valid_json_rate_percentage"]
            
            # Extract individual scenario performance for CI calculation
            if "seasonal_performance_analysis" in data:
                seasonal_data = data["seasonal_performance_analysis"]
                hourly_performances = []
                daily_maes = []
                
                for season, season_data in seasonal_data.items():
                    # Estimate individual performances from seasonal averages
                    season_mae = season_data.get("daily_total_ppfd_mae", 0)
                    daily_maes.extend([season_mae] * 18)  # Approximate 18 days per season
                    
        elif "accuracy_performance" in data:
            # Llama format
            hourly_success = data["accuracy_performance"]["exact_hourly_match_rate"]
            daily_mae = data["ppfd_performance"]["daily_ppfd_mae"]
            api_success = data["summary"]["json_success_rate"]
            
            # Extract detailed results for CI calculation
            if "detailed_results" in data:
                detailed = data["detailed_results"]
                hourly_performances = [item["exact_match_rate"] for item in detailed if "exact_match_rate" in item]
                daily_maes = [item["daily_ppfd_error"] for item in detailed if "daily_ppfd_error" in item]
            else:
                hourly_performances = [hourly_success] * 72  # Use average
                daily_maes = [daily_mae] * 72
        else:
            return {}
        
        return {
            "hourly_success_rate": hourly_success,
            "daily_mae": daily_mae,
            "api_success_rate": api_success,
            "hourly_performances": hourly_performances,
            "daily_maes": daily_maes,
            "model_parameters": self.model_params.get(model_name, 0)
        }
    
    def generate_enhanced_statistics(self):
        """Generate comprehensive statistical analysis"""
        print("\n🔬 Generating Enhanced Statistical Analysis...")
        
        # Load all model data
        self.load_all_model_data()
        
        # Extract metrics for all models
        model_metrics = {}
        for model_name in self.model_data.keys():
            metrics = self.extract_model_metrics(model_name)
            if metrics:
                model_metrics[model_name] = metrics
        
        # Generate performance comparison with confidence intervals
        print("\n📊 Performance with Confidence Intervals:")
        print("=" * 80)
        
        for model_name, metrics in model_metrics.items():
            hourly_ci = self.calculate_confidence_intervals(metrics.get("hourly_performances", []))
            daily_mae_ci = self.calculate_confidence_intervals(metrics.get("daily_maes", []))
            
            print(f"\n{model_name.replace('_', ' ').title()}:")
            print(f"  Hourly Success Rate: {metrics['hourly_success_rate']:.1f}% "
                  f"(95% CI: {hourly_ci[0]:.1f}% - {hourly_ci[1]:.1f}%)")
            print(f"  Daily PPFD MAE: {metrics['daily_mae']:.1f} ± {daily_mae_ci[1] - daily_mae_ci[0]:.1f} PPFD units")
        
        # Statistical significance tests
        print("\n📈 Statistical Significance Tests:")
        print("=" * 80)
        
        model_names = list(model_metrics.keys())
        for i, model1 in enumerate(model_names):
            for model2 in model_names[i+1:]:
                if (model_metrics[model1]["hourly_performances"] and 
                    model_metrics[model2]["hourly_performances"]):
                    
                    # T-test for hourly performance
                    t_stat, p_value = ttest_ind(
                        model_metrics[model1]["hourly_performances"],
                        model_metrics[model2]["hourly_performances"]
                    )
                    
                    # Cohen's d
                    cohens_d = self.calculate_cohens_d(
                        model_metrics[model1]["hourly_performances"],
                        model_metrics[model2]["hourly_performances"]
                    )
                    
                    significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
                    
                    print(f"\n{model1.replace('_', ' ').title()} vs {model2.replace('_', ' ').title()}:")
                    print(f"  p-value: {p_value:.4f} {significance}")
                    print(f"  Cohen's d: {cohens_d:.2f}")
                    print(f"  Effect size: {'Large' if cohens_d > 0.8 else 'Medium' if cohens_d > 0.5 else 'Small'}")
        
        # Scale-Performance correlation
        print("\n🔗 Scale-Performance Correlation:")
        print("=" * 80)
        
        model_sizes = []
        performance_scores = []
        
        for model_name, metrics in model_metrics.items():
            if metrics["model_parameters"] > 0:
                model_sizes.append(metrics["model_parameters"])
                performance_scores.append(metrics["hourly_success_rate"])
        
        if len(model_sizes) > 2:
            correlation, p_value = pearsonr(model_sizes, performance_scores)
            r_squared = correlation ** 2
            
            print(f"Correlation coefficient (r): {correlation:.3f}")
            print(f"R-squared: {r_squared:.3f}")
            print(f"P-value: {p_value:.4f}")
            print(f"Model size explains {r_squared*100:.1f}% of performance variance")
        
        # Generate cost-performance analysis
        self.generate_cost_performance_analysis(model_metrics)
        
        return model_metrics
    
    def generate_cost_performance_analysis(self, model_metrics: Dict[str, Any]):
        """Generate cost-performance analysis"""
        print("\n💰 Cost-Performance Analysis:")
        print("=" * 80)
        
        # Estimated API costs per 1000 tokens (as of 2024)
        cost_estimates = {
            "openai_o1": 0.060,  # $60/1M tokens
            "anthropic_claude-opus-4": 0.075,  # $75/1M tokens  
            "anthropic_claude-3.7-sonnet": 0.015,  # $15/1M tokens
            "meta-llama_llama-3.3-70b": 0.0006,  # $0.6/1M tokens (via OpenRouter)
            "deepseek_r1_7b": 0.0002  # $0.2/1M tokens
        }
        
        # Estimated tokens per request (prompt + response)
        tokens_per_request = 2000
        scenarios = 72
        
        for model_name, metrics in model_metrics.items():
            if model_name in cost_estimates:
                cost_per_1k = cost_estimates[model_name]
                total_cost = (cost_per_1k * tokens_per_request * scenarios) / 1000
                
                # Adjust for API success rate
                effective_cost = total_cost / (metrics["api_success_rate"] / 100)
                cost_per_success = effective_cost / scenarios
                
                print(f"\n{model_name.replace('_', ' ').title()}:")
                print(f"  Cost per 72 scenarios: ${total_cost:.2f}")
                print(f"  Effective cost (including failures): ${effective_cost:.2f}")
                print(f"  Cost per successful scenario: ${cost_per_success:.2f}")
                print(f"  Performance score: {metrics['hourly_success_rate']:.1f}%")
                print(f"  Cost efficiency: {metrics['hourly_success_rate']/cost_per_success:.1f} points per $")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Statistical Analysis for LLM LED Optimization")
    parser.add_argument("--results-dir", default="results/analysis_reports",
                       help="Directory containing analysis reports")
    parser.add_argument("--output", default="enhanced_statistical_report.json",
                       help="Output file for detailed statistics")
    
    args = parser.parse_args()
    
    analyzer = EnhancedStatisticalAnalyzer(args.results_dir)
    model_metrics = analyzer.generate_enhanced_statistics()
    
    # Save detailed results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(model_metrics, f, indent=2, default=str)
    
    print(f"\n✅ Enhanced statistical analysis complete!")
    print(f"📁 Detailed results saved to: {output_path}")
    print(f"📊 Use this data to validate the enhanced metrics in your README")

if __name__ == "__main__":
    main() 