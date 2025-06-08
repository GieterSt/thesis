#!/usr/bin/env python3
"""
MAIN ANALYSIS ORCHESTRATOR
Coordinates all analysis components to generate comprehensive results
"""
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path

# Import our modular components
from data_loader import load_ground_truth
from model_analyzer import analyze_single_model, process_ground_truth_comparison
from statistical_analyzer import comprehensive_statistical_analysis
from visualization_generator import create_thesis_visualizations
from report_generator import generate_comprehensive_readme, generate_html_from_readme

def ensure_all_directories():
    """Ensure all required directories exist"""
    # Create all required output directories
    required_dirs = [
        '../results/model_outputs',
        '../results/analysis',
        '../results/methodology_logs',
        '../results/comparisons',
        '../results/figures',
        '../results/analysis_reports'
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def find_model_output_files():
    """Find all model output JSON files"""
    output_patterns = [
        '../results/model_outputs/*.json',
        '../results/model_outputs/**/*.json',
        '*.json'  # Fallback for files in current directory
    ]
    
    all_files = []
    for pattern in output_patterns:
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    
    # Filter to only include files that look like model results
    model_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        # Include files that start with 'results_' or contain model names
        if (filename.startswith('results_') or 
            any(model in filename.lower() for model in ['claude', 'deepseek', 'llama', 'mistral', 'gpt'])):
            model_files.append(file_path)
    
    return list(set(model_files))  # Remove duplicates

def run_comprehensive_analysis():
    """Run complete analysis pipeline"""
    print("="*80)
    print("🔬 LED OPTIMIZATION LLM ANALYSIS SYSTEM")
    print("="*80)
    print("🗂️  Modular Architecture: Splitting large analysis into components")
    print("⚡ Enhanced Performance: Centralized model naming fixes")
    print("📊 Comprehensive Output: Statistics, Visualizations, Reports")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure all directories exist
    ensure_all_directories()
    
    # Step 1: Load ground truth data
    print("\n📊 STEP 1: Loading Ground Truth Data")
    ground_truth = load_ground_truth()
    if not ground_truth:
        print("⚠️  Warning: No ground truth data found. Analysis will be limited.")
    
    # Step 2: Find and analyze model outputs
    print("\n📁 STEP 2: Finding Model Output Files")
    model_files = find_model_output_files()
    
    if not model_files:
        print("❌ No model output files found!")
        print("💡 Make sure model output files are in 'results/model_outputs/' directory")
        print("💡 Files should be named like 'results_model_name.json'")
        return None
    
    print(f"✅ Found {len(model_files)} model output files:")
    for file_path in model_files:
        print(f"  - {file_path}")
    
    # Step 3: Analyze each model
    print("\n🔍 STEP 3: Analyzing Individual Models")
    all_metrics = []
    
    for file_path in model_files:
        print(f"\n📂 Processing: {os.path.basename(file_path)}")
        
        # Analyze basic model performance
        metrics = analyze_single_model(file_path)
        
        if metrics:
            # Add ground truth comparison if available
            if ground_truth:
                metrics = process_ground_truth_comparison(metrics, ground_truth)
            
            all_metrics.append(metrics)
            print(f"✅ Analysis complete for {metrics['model_name']}")
        else:
            print(f"❌ Failed to analyze {file_path}")
    
    if not all_metrics:
        print("❌ No valid metrics generated. Check model output files.")
        return None
    
    print(f"\n✅ Successfully analyzed {len(all_metrics)} models")
    
    # Step 4: Statistical Analysis
    print("\n📈 STEP 4: Comprehensive Statistical Analysis")
    stats_results = comprehensive_statistical_analysis(all_metrics)
    
    # Step 5: Generate Visualizations
    print("\n📊 STEP 5: Generating Thesis Visualizations")
    visualizations = create_thesis_visualizations(all_metrics, stats_results, timestamp)
    
    # Step 6: Generate Reports
    print("\n📝 STEP 6: Generating Comprehensive Reports")
    readme_content = generate_comprehensive_readme(all_metrics, stats_results, visualizations, timestamp)
    
    if readme_content:
        html_report = generate_html_from_readme(readme_content, timestamp)
    
    # Step 7: Save comprehensive analysis data
    print("\n💾 STEP 7: Saving Analysis Data")
    try:
        import json
        analysis_data = {
            'timestamp': timestamp,
            'model_metrics': all_metrics,
            'statistical_results': stats_results,
            'generated_figures': visualizations,
            'summary': {
                'total_models': len(all_metrics),
                'models_with_ground_truth': len([m for m in all_metrics if m['ground_truth_analysis']]),
                'analysis_version': 'modular_v1.0'
            }
        }
        
        analysis_path = f"../results/analysis/comprehensive_analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"✅ Analysis data saved: {analysis_path}")
        
    except Exception as e:
        print(f"⚠️  Could not save analysis data: {e}")
    
    # Final Summary
    print("\n" + "="*80)
    print("🎉 ANALYSIS COMPLETE!")
    print("="*80)
    
    print(f"📊 Models Analyzed: {len(all_metrics)}")
    print(f"📈 Statistical Analysis: {'✅ Complete' if stats_results else '⚠️ Limited'}")
    print(f"📊 Visualizations: {len(visualizations) if visualizations else 0} figures generated")
    print(f"📝 Reports Generated: README.md + HTML report")
    
    if visualizations:
        print(f"\n📊 Generated Figures:")
        for i, fig_path in enumerate(visualizations, 1):
            print(f"  {i}. {os.path.basename(fig_path)}")
    
    print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📁 Check 'results/' directory for all outputs")
    
    return {
        'metrics': all_metrics,
        'stats': stats_results,
        'visualizations': visualizations,
        'timestamp': timestamp
    }

def monitor_and_auto_update():
    """Monitor for new model outputs and auto-update analysis"""
    print("="*80)
    print("👁️  MONITORING MODE: Auto-updating analysis on new results")
    print("="*80)
    print("Press Ctrl+C to stop monitoring")
    
    last_analysis_time = 0
    
    try:
        while True:
            # Check for new files
            model_files = find_model_output_files()
            
            if model_files:
                # Check if any files are newer than last analysis
                newest_file_time = max(os.path.getmtime(f) for f in model_files)
                
                if newest_file_time > last_analysis_time:
                    print(f"\n🔄 New/updated files detected. Running analysis...")
                    result = run_comprehensive_analysis()
                    
                    if result:
                        last_analysis_time = time.time()
                        print(f"✅ Analysis updated at {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        print("❌ Analysis failed")
            
            # Wait before checking again
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor":
            monitor_and_auto_update()
        elif sys.argv[1] == "--help":
            print_usage()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print_usage()
    else:
        run_comprehensive_analysis()

def print_usage():
    """Print usage information"""
    print("""
🔬 LED Optimization LLM Analysis System

Usage:
  python run_analysis.py           # Run complete analysis once
  python run_analysis.py --monitor # Monitor for new files and auto-update
  python run_analysis.py --help    # Show this help message

Features:
  ✅ Modular architecture for maintainable code
  ✅ Comprehensive statistical analysis
  ✅ Thesis-ready visualizations with correct model names
  ✅ Automatic README and HTML report generation
  ✅ Ground truth comparison with optimal solutions
  ✅ Performance grading and ranking system

Output:
  📊 results/figures/          - Generated visualizations
  📝 README.md                 - Comprehensive analysis report
  📄 results/analysis_reports/ - HTML reports and timestamped files
  💾 results/analysis/         - Raw analysis data (JSON)

Requirements:
  📁 Model output files in 'results/model_outputs/' directory
  📁 Ground truth data in 'data/input-output pairs json/'
  🐍 Python packages: pandas, numpy, matplotlib, seaborn, scipy, sklearn
    """)

if __name__ == "__main__":
    main() 