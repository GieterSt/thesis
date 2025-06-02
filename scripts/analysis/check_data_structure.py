#!/usr/bin/env python3
"""
Data Structure Analysis Script
Examines the structure of model results to understand field names and calculate proper metrics.
"""

import json
from pathlib import Path
from typing import Dict, Any

def analyze_data_structure():
    """Analyze the structure of all model results files"""
    results_dir = Path("results/model_outputs")
    
    print("🔍 **DATA STRUCTURE ANALYSIS**")
    print("=" * 50)
    
    # Check a few different model files
    sample_files = [
        "google_gemini-2.5-pro-preview_results_v3_prompt.json",
        "anthropic_claude-opus-4_results_v3_prompt.json", 
        "meta-llama_llama-3.3-70b-instruct_free_results_v3_prompt.json"
    ]
    
    for filename in sample_files:
        file_path = results_dir / filename
        if not file_path.exists():
            print(f"❌ File not found: {filename}")
            continue
            
        print(f"\n📋 **Analyzing: {filename}**")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            print("   Empty file")
            continue
            
        first_item = data[0]
        print(f"   📊 Total items: {len(data)}")
        print(f"   🔑 Available keys:")
        
        for key in sorted(first_item.keys()):
            value = first_item[key]
            if isinstance(value, dict):
                print(f"      • {key}: (dict with {len(value)} keys)")
                if len(value) <= 5:  # Show dict contents if small
                    for sub_key in sorted(value.keys()):
                        print(f"         - {sub_key}: {type(value[sub_key]).__name__}")
            elif isinstance(value, list):
                print(f"      • {key}: (list with {len(value)} items)")
            elif isinstance(value, str):
                print(f"      • {key}: (string, length {len(value)})")
            else:
                print(f"      • {key}: {type(value).__name__}")
        
        # Check for ground truth data
        ground_truth_fields = [
            'ground_truth_allocation',
            'ground_truth', 
            'expected_allocation',
            'correct_allocation',
            'optimal_allocation'
        ]
        
        print(f"   🎯 Ground truth fields found:")
        for field in ground_truth_fields:
            if field in first_item:
                print(f"      ✅ {field}: {type(first_item[field]).__name__}")
            else:
                print(f"      ❌ {field}: not found")
        
        # Check if we have parsed allocation
        if 'parsed_allocation' in first_item:
            parsed = first_item['parsed_allocation']
            print(f"   📝 Parsed allocation structure:")
            if isinstance(parsed, dict):
                for key in sorted(parsed.keys()):
                    print(f"      • {key}: {type(parsed[key]).__name__}")
                    if key == 'allocation_PPFD_per_hour' and isinstance(parsed[key], dict):
                        allocation_dict = parsed[key]
                        print(f"         - Contains {len(allocation_dict)} hour entries")
                        # Show a few examples
                        sample_keys = list(sorted(allocation_dict.keys()))[:3]
                        for hour_key in sample_keys:
                            print(f"         - {hour_key}: {allocation_dict[hour_key]}")

def check_ground_truth_availability():
    """Check which files have ground truth data available"""
    print(f"\n🔍 **GROUND TRUTH AVAILABILITY CHECK**")
    print("=" * 50)
    
    results_dir = Path("results/model_outputs")
    
    for json_file in results_dir.glob("*.json"):
        if "_BACKUP.json" in json_file.name:
            continue
            
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            if not data:
                continue
                
            first_item = data[0]
            has_ground_truth = any(field in first_item for field in [
                'ground_truth_allocation', 'ground_truth', 'expected_allocation', 
                'correct_allocation', 'optimal_allocation'
            ])
            
            api_success_count = sum(1 for item in data if item.get('api_success'))
            parse_success_count = sum(1 for item in data if item.get('api_success') and not item.get('parse_error'))
            
            print(f"📁 {json_file.name}")
            print(f"   📊 Total scenarios: {len(data)}")
            print(f"   🌐 API successes: {api_success_count}")
            print(f"   ✅ Parse successes: {parse_success_count}")
            print(f"   🎯 Has ground truth: {has_ground_truth}")
            
        except Exception as e:
            print(f"❌ Error reading {json_file.name}: {e}")

def find_ground_truth_source():
    """Look for ground truth data in other files"""
    print(f"\n🔍 **SEARCHING FOR GROUND TRUTH SOURCE**")
    print("=" * 50)
    
    # Check various directories for ground truth data
    search_paths = [
        Path("data"),
        Path("results"),
        Path("input"),
        Path("test_data"),
        Path("."),
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        print(f"\n📂 Searching in: {search_path}")
        
        # Look for files that might contain ground truth
        patterns = ["*ground_truth*", "*optimal*", "*correct*", "*expected*", "*truth*"]
        
        for pattern in patterns:
            files = list(search_path.glob(pattern))
            if files:
                print(f"   Found {pattern}: {[f.name for f in files]}")
                
        # Also look for any JSON files that might contain truth data
        json_files = list(search_path.glob("*.json"))
        if json_files and search_path.name != "model_outputs":
            print(f"   JSON files: {[f.name for f in json_files[:5]]}")  # Show first 5

def main():
    """Main analysis function"""
    analyze_data_structure()
    check_ground_truth_availability() 
    find_ground_truth_source()
    
    print(f"\n💡 **RECOMMENDATIONS**")
    print("=" * 50)
    print("1. Need to locate or generate ground truth data for proper evaluation")
    print("2. Post-processing successfully fixed Google Gemini JSON parsing (100% API success)")
    print("3. Performance metrics need ground truth comparison for hourly success calculation")
    print("4. Current analysis shows API success but cannot calculate optimization accuracy")

if __name__ == "__main__":
    main() 