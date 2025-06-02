#!/usr/bin/env python3
"""
Automated Analysis Pipeline for All LLM Models
Analyzes all model results, generates comprehensive statistics, and updates documentation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple

class ModelPerformanceCollector:
    """Collects and analyzes performance data from all models"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.results_dir = self.base_dir / "results" / "model_outputs"
        self.analysis_dir = self.base_dir / "results" / "analysis"
        self.ground_truth_file = self.base_dir / "data" / "ground_truth" / "test_set_ground_truth_complete.xlsx"
        
        # Ensure analysis directory exists
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
    
    def find_all_model_files(self) -> List[Path]:
        """Find all model result JSON files"""
        if not self.results_dir.exists():
            print(f"Results directory {self.results_dir} not found!")
            return []
        
        return list(self.results_dir.glob("*_results_*.json"))
    
    def analyze_single_model(self, model_file: Path) -> Dict:
        """Run analysis for a single model"""
        print(f"Analyzing {model_file.name}...")
        
        # Run the analyze_performance.py script
        cmd = [
            "python", "scripts/analysis/analyze_performance.py",
            "--results", str(model_file),
            "--ground-truth", str(self.ground_truth_file),
            "--output-dir", str(self.analysis_dir)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ Analysis completed for {model_file.name}")
            
            # Parse the summary from output
            output_lines = result.stdout.split('\n')
            summary = {}
            
            for line in output_lines:
                if "JSON Success Rate:" in line:
                    summary['json_success_rate'] = float(line.split(":")[1].strip().rstrip('%'))
                elif "Daily PPFD MAE:" in line:
                    parts = line.split(":")
                    mae_part = parts[1].strip().split()[0]
                    summary['daily_ppfd_mae'] = float(mae_part)
                elif "Cost Difference:" in line:
                    summary['cost_difference'] = float(line.split(":")[1].strip().rstrip('%'))
                elif "Hourly Allocation MAE:" in line:
                    summary['hourly_mae'] = float(line.split(":")[1].strip())
                elif "Exact Hourly Match Rate:" in line:
                    summary['exact_match_rate'] = float(line.split(":")[1].strip().rstrip('%'))
            
            # Load the detailed analysis file
            analysis_file = self.analysis_dir / f"analysis_summary_{model_file.stem}.json"
            if analysis_file.exists():
                with open(analysis_file, 'r') as f:
                    detailed_analysis = json.load(f)
                summary.update(detailed_analysis.get('aggregate_metrics', {}))
            
            return summary
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error analyzing {model_file.name}: {e}")
            print(f"  Error output: {e.stderr}")
            return {}
        except Exception as e:
            print(f"  ✗ Unexpected error analyzing {model_file.name}: {e}")
            return {}
    
    def extract_model_info(self, filename: str) -> Dict:
        """Extract model name and version from filename"""
        # Remove file extension
        basename = filename.replace('.json', '')
        
        # Extract model name (everything before _results_)
        if '_results_' in basename:
            model_name = basename.split('_results_')[0]
            version_part = basename.split('_results_')[1]
        else:
            model_name = basename
            version_part = 'unknown'
        
        # Clean up model name
        model_display_name = model_name.replace('_', ' ').replace('-', ' ').title()
        
        # Map specific models to clean names
        name_mapping = {
            'claude-opus-4': 'Claude Opus 4',
            'claude-3.7-sonnet': 'Claude 3.7 Sonnet', 
            'openai-o1-preview': 'OpenAI O1',
            'llama-3.3-70b-instruct': 'Llama 3.3 70B',
            'deepseek-r1-7b': 'DeepSeek R1 7B',
            'google-gemini-2.5-pro-preview': 'Google Gemini 2.5 Pro'
        }
        
        for key, value in name_mapping.items():
            if key in model_name:
                model_display_name = value
                break
        
        return {
            'model_name': model_name,
            'display_name': model_display_name,
            'version': version_part,
            'filename': filename
        }
    
    def generate_comprehensive_report(self, all_results: Dict) -> Dict:
        """Generate comprehensive performance report"""
        
        # Sort models by performance (API success rate, then accuracy)
        sorted_models = sorted(all_results.items(), 
                             key=lambda x: (x[1].get('json_success_rate', 0), 
                                          -x[1].get('hourly_mae', float('inf'))))
        
        # Create summary table
        summary_table = []
        for model_key, metrics in sorted_models:
            model_info = self.extract_model_info(model_key)
            
            summary_table.append({
                'Model': model_info['display_name'],
                'Version': model_info['version'],
                'API Success Rate (%)': f"{metrics.get('json_success_rate', 0):.1f}",
                'Hourly Success Rate (%)': f"{metrics.get('exact_match_rate', 0):.1f}",
                'Cost Difference (%)': f"{metrics.get('cost_difference', 0):.2f}",
                'Hourly MAE': f"{metrics.get('hourly_mae', 0):.3f}",
                'PPFD MAE': f"{metrics.get('daily_ppfd_mae', 0):.3f}"
            })
        
        return {
            'summary_table': summary_table,
            'detailed_results': all_results,
            'best_model': sorted_models[-1][0] if sorted_models else None,
            'total_models': len(all_results)
        }
    
    def create_performance_visualizations(self, report_data: Dict):
        """Create updated performance visualization charts"""
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Extract data for plotting
        models = [row['Model'] for row in report_data['summary_table']]
        api_success = [float(row['API Success Rate (%)']) for row in report_data['summary_table']]
        hourly_success = [float(row['Hourly Success Rate (%)']) for row in report_data['summary_table']]
        cost_diff = [float(row['Cost Difference (%)']) for row in report_data['summary_table']]
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. API Success Rate
        bars1 = ax1.bar(models, api_success, alpha=0.8, color='skyblue')
        ax1.set_title('API Success Rate by Model', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_ylim(0, 105)
        for i, v in enumerate(api_success):
            ax1.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Hourly Success Rate (for successful API calls)
        bars2 = ax2.bar(models, hourly_success, alpha=0.8, color='lightgreen')
        ax2.set_title('Hourly Allocation Accuracy (when API succeeds)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Exact Match Rate (%)')
        ax2.set_ylim(0, 105)
        for i, v in enumerate(hourly_success):
            ax2.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Cost Difference
        colors = ['red' if x > 0 else 'green' for x in cost_diff]
        bars3 = ax3.bar(models, cost_diff, alpha=0.8, color=colors)
        ax3.set_title('Cost Difference vs Optimal (%)', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Cost Difference (%)')
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        for i, v in enumerate(cost_diff):
            ax3.text(i, v + (0.5 if v >= 0 else -0.5), f'{v:.2f}%', ha='center', va='bottom' if v >= 0 else 'top')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Combined Performance Score
        # Calculate composite score: API Success * Hourly Success / 100
        composite_scores = [a * h / 100 for a, h in zip(api_success, hourly_success)]
        bars4 = ax4.bar(models, composite_scores, alpha=0.8, color='orange')
        ax4.set_title('Overall Performance Score', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Composite Score (API × Hourly / 100)')
        ax4.set_ylim(0, max(composite_scores) * 1.1 if composite_scores else 1)
        for i, v in enumerate(composite_scores):
            ax4.text(i, v + max(composite_scores) * 0.01 if composite_scores else 0.01, f'{v:.1f}', ha='center', va='bottom')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the figure
        figures_dir = self.base_dir / "results" / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(figures_dir / "model_performance_comparison.png", dpi=300, bbox_inches='tight')
        plt.savefig(figures_dir / "model_performance_comparison.pdf", bbox_inches='tight')
        
        print(f"Performance visualizations saved to {figures_dir}")
        plt.show()
    
    def update_readme(self, report_data: Dict):
        """Update README.md with latest results"""
        readme_path = self.base_dir / "README.md"
        
        if not readme_path.exists():
            print("README.md not found, skipping update")
            return
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Create new results table
        table_header = """| Model | API Success | Hourly Success | Cost Difference | Overall Score |
|-------|-------------|----------------|-----------------|---------------|"""
        
        table_rows = []
        for row in report_data['summary_table']:
            api_success = float(row['API Success Rate (%)'])
            hourly_success = float(row['Hourly Success Rate (%)'])
            overall_score = api_success * hourly_success / 100
            
            table_rows.append(
                f"| **{row['Model']}** ({row['Version']}) | {row['API Success Rate (%)']}% | "
                f"{row['Hourly Success Rate (%)']}% | {row['Cost Difference (%)']}% | {overall_score:.1f} |"
            )
        
        new_table = table_header + "\n" + "\n".join(table_rows)
        
        # Find and replace the existing results table
        # Look for a pattern like "| Model | API Success" to "## " (next section)
        pattern = r'\| Model \| API Success.*?(?=##|\Z)'
        replacement = new_table + "\n\n"
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # If no existing table found, add it after "## Results" section
        if updated_content == content:
            results_pattern = r'(## Results.*?\n\n)'
            replacement_with_header = r'\1' + new_table + "\n\n"
            updated_content = re.sub(results_pattern, replacement_with_header, content, flags=re.DOTALL)
        
        with open(readme_path, 'w') as f:
            f.write(updated_content)
        
        print("README.md updated with latest results")
    
    def update_html_documentation(self):
        """Update HTML documentation with latest results"""
        try:
            subprocess.run(["python", "scripts/utils/update_html.py"], check=True)
            print("HTML documentation updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error updating HTML documentation: {e}")
        except FileNotFoundError:
            print("HTML update script not found, skipping HTML update")
    
    def run_complete_analysis(self):
        """Run complete analysis pipeline for all models"""
        print("Starting comprehensive model analysis pipeline...")
        print("=" * 60)
        
        # Find all model files
        model_files = self.find_all_model_files()
        if not model_files:
            print("No model result files found!")
            return
        
        print(f"Found {len(model_files)} model result files:")
        for f in model_files:
            print(f"  - {f.name}")
        print()
        
        # Analyze each model
        all_results = {}
        for model_file in model_files:
            model_key = model_file.stem  # filename without extension
            analysis_results = self.analyze_single_model(model_file)
            if analysis_results:
                all_results[model_key] = analysis_results
        
        if not all_results:
            print("No successful analyses completed!")
            return
        
        print(f"\nSuccessfully analyzed {len(all_results)} models")
        print("=" * 60)
        
        # Generate comprehensive report
        report_data = self.generate_comprehensive_report(all_results)
        
        # Save comprehensive report
        report_file = self.analysis_dir / "comprehensive_model_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"Comprehensive report saved to: {report_file}")
        
        # Create visualizations
        self.create_performance_visualizations(report_data)
        
        # Update documentation
        self.update_readme(report_data)
        self.update_html_documentation()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FINAL ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Models Analyzed: {report_data['total_models']}")
        print("\nModel Rankings (by overall performance):")
        
        for i, row in enumerate(report_data['summary_table'], 1):
            api_success = float(row['API Success Rate (%)'])
            hourly_success = float(row['Hourly Success Rate (%)'])
            overall_score = api_success * hourly_success / 100
            print(f"{i:2d}. {row['Model']:20s} - {overall_score:5.1f} pts "
                  f"(API: {api_success:5.1f}%, Hourly: {hourly_success:5.1f}%)")
        
        print("\n" + "=" * 60)
        print("Analysis pipeline completed successfully!")
        print("All results, figures, and documentation have been updated.")
        print("=" * 60)

def main():
    """Main function"""
    collector = ModelPerformanceCollector()
    collector.run_complete_analysis()

if __name__ == "__main__":
    main() 