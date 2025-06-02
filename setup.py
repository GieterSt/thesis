#!/usr/bin/env python3
"""
Setup script for LLM LED Optimization Evaluation

This script helps initialize the project environment and validates the setup.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        return False

def validate_directory_structure():
    """Validate that all required directories exist"""
    required_dirs = [
        "data/test_sets",
        "data/ground_truth", 
        "data/raw_data",
        "scripts/data_preparation",
        "scripts/model_testing",
        "scripts/analysis",
        "results/model_outputs",
        "results/analysis_reports",
        "results/comparisons",
        "prompts",
        "archive"
    ]
    
    print("Validating directory structure...")
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - missing")
            all_exist = False
    
    return all_exist

def validate_data_files():
    """Check if essential data files exist"""
    essential_files = [
        "data/test_sets/test_set_v1.json",
        "data/test_sets/test_set_v2.json", 
        "data/test_sets/test_set_v3.json",
        "data/ground_truth/test_set_ground_truth_complete.xlsx"
    ]
    
    print("Validating essential data files...")
    all_exist = True
    for file_path in essential_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - missing")
            all_exist = False
    
    return all_exist

def validate_scripts():
    """Check if essential scripts exist and are executable"""
    essential_scripts = [
        "scripts/data_preparation/create_test_sets.py",
        "scripts/model_testing/run_model_tests.py",
        "scripts/analysis/analyze_performance.py"
    ]
    
    print("Validating essential scripts...")
    all_exist = True
    for script_path in essential_scripts:
        if Path(script_path).exists():
            print(f"✓ {script_path}")
        else:
            print(f"✗ {script_path} - missing")
            all_exist = False
    
    return all_exist

def check_api_key():
    """Check if OpenRouter API key is configured"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        print("✓ OPENROUTER_API_KEY environment variable is set")
        return True
    else:
        print("⚠ OPENROUTER_API_KEY environment variable not set")
        print("  Set it with: export OPENROUTER_API_KEY='your-api-key-here'")
        return False

def run_quick_test():
    """Run a quick test to validate the setup"""
    print("Running quick validation test...")
    
    # Test data loading
    try:
        test_set_path = "data/test_sets/test_set_v3.json"
        if Path(test_set_path).exists():
            with open(test_set_path, 'r') as f:
                test_data = json.load(f)
            print(f"✓ Successfully loaded {len(test_data)} test items from {test_set_path}")
        else:
            print(f"✗ Cannot load test set from {test_set_path}")
            return False
    except Exception as e:
        print(f"✗ Error loading test data: {e}")
        return False
    
    # Test script imports
    try:
        sys.path.append('scripts/analysis')
        import analyze_performance
        print("✓ Analysis script imports successfully")
    except ImportError as e:
        print(f"✗ Cannot import analysis script: {e}")
        return False
    
    return True

def print_usage_examples():
    """Print usage examples for getting started"""
    print("\n" + "="*60)
    print("SETUP COMPLETE - Usage Examples")
    print("="*60)
    
    print("\n1. Generate test sets (if needed):")
    print("   cd scripts/data_preparation")
    print("   python create_test_sets.py --version v3 --output ../../data/test_sets/test_set_v3.json")
    
    print("\n2. Test a model:")
    print("   cd scripts/model_testing")
    print("   export OPENROUTER_API_KEY='your-api-key-here'")
    print("   python run_model_tests.py \\")
    print("     --model anthropic/claude-opus-4 \\")
    print("     --test-set ../../data/test_sets/test_set_v3.json")
    
    print("\n3. Analyze results:")
    print("   cd scripts/analysis")
    print("   python analyze_performance.py \\")
    print("     --results ../../results/model_outputs/anthropic_claude-opus-4_results_v3_prompt.json \\")
    print("     --ground-truth ../../data/ground_truth/test_set_ground_truth_complete.xlsx")
    
    print("\n4. View results:")
    print("   # JSON summary: results/analysis_reports/")
    print("   # Excel comparison: results/comparisons/")
    
    print("\nFor more information, see README.md and individual directory READMEs")

def main():
    """Main setup function"""
    print("LLM LED Optimization Evaluation - Setup Validation")
    print("="*60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Validate structure
    if not validate_directory_structure():
        success = False
    
    # Validate data files
    if not validate_data_files():
        success = False
        print("  Note: Run data preparation scripts to generate missing test sets")
    
    # Validate scripts
    if not validate_scripts():
        success = False
    
    # Check API key (warning only)
    check_api_key()
    
    # Run quick test
    if not run_quick_test():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✓ SETUP VALIDATION PASSED")
        print_usage_examples()
    else:
        print("✗ SETUP VALIDATION FAILED")
        print("Please fix the issues above before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main() 