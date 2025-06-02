#!/usr/bin/env python3
"""
Test Set Generator for LLM LED Optimization Evaluation

This script creates test datasets with different prompt versions for evaluating
LLM performance on greenhouse LED scheduling optimization tasks.

Usage:
    python create_test_sets.py --version v1 --output data/test_sets/test_set_v1.json
    python create_test_sets.py --version v2 --output data/test_sets/test_set_v2.json
    python create_test_sets.py --version v3 --output data/test_sets/test_set_v3.json
"""

import json
import argparse
import sys
from pathlib import Path

def get_base_prompt():
    """Base optimization problem description used across all versions"""
    return """You are tasked with optimizing LED lighting schedules for a greenhouse to achieve specific daily PPFD (Photosynthetic Photon Flux Density) targets while minimizing electricity costs.

**Key Parameters:**
- LED Power Output: 275 μmol/m²/s per LED unit
- Electricity prices vary by hour throughout the day
- Daily PPFD target must be achieved
- LED units can be adjusted hourly (0-23 hours)
- Goal: Minimize electricity cost while meeting PPFD target"""

def get_v1_prompt():
    """Original basic prompt"""
    return get_base_prompt() + """

Please provide your LED allocation for each hour in JSON format:
{
  "led_allocations": [hour0, hour1, hour2, ..., hour23]
}"""

def get_v2_prompt():
    """Enhanced prompt with detailed instructions and role definition"""
    return """You are an expert LED scheduling optimizer for greenhouse operations. Your role is to create cost-effective lighting schedules that meet daily PPFD targets while minimizing electricity expenses.

**SYSTEM OVERVIEW:**
- LED Power Output: 275 μmol/m²/s per LED unit
- Operating Window: 24 hours (0-23)
- Objective: Minimize electricity cost while achieving daily PPFD target

**OPTIMIZATION ALGORITHM:**
1. Calculate total daily PPFD requirement
2. Identify hours with lowest electricity prices
3. Prioritize LED allocation during cost-effective periods
4. Ensure daily PPFD target is exactly met
5. Minimize total electricity expenditure

**CONSTRAINTS:**
- Daily PPFD target must be achieved (±0.1% tolerance)
- LED units must be non-negative integers
- Each LED contributes 275 μmol/m²/s when active
- Hourly allocations can vary from 0 to maximum available

**EXAMPLE ALLOCATION:**
For 20 mol/m²/day target with varying electricity prices:
- Prioritize hours 2-6 (lowest prices: 0.05-0.08 €/kWh)
- Use hours 10-14 if additional PPFD needed
- Avoid peak price hours 17-20 (0.25-0.30 €/kWh)

**OUTPUT REQUIREMENTS:**
Provide ONLY valid JSON with hourly LED allocations:
{
  "led_allocations": [hour0, hour1, hour2, ..., hour23]
}

FINAL VALIDATION: Ensure total daily PPFD = target ± 0.1%"""

def get_v3_prompt():
    """Refined prompt ensuring pure JSON output"""
    return """You are an expert LED scheduling optimizer for greenhouse operations. Your role is to create cost-effective lighting schedules that meet daily PPFD targets while minimizing electricity expenses.

**SYSTEM OVERVIEW:**
- LED Power Output: 275 μmol/m²/s per LED unit
- Operating Window: 24 hours (0-23)
- Objective: Minimize electricity cost while achieving daily PPFD target

**OPTIMIZATION ALGORITHM:**
1. Calculate total daily PPFD requirement
2. Identify hours with lowest electricity prices
3. Prioritize LED allocation during cost-effective periods
4. Ensure daily PPFD target is exactly met
5. Minimize total electricity expenditure

**CONSTRAINTS:**
- Daily PPFD target must be achieved (±0.1% tolerance)
- LED units must be non-negative integers
- Each LED contributes 275 μmol/m²/s when active
- Hourly allocations can vary from 0 to maximum available

**EXAMPLE ALLOCATION:**
For 20 mol/m²/day target with varying electricity prices:
- Prioritize hours 2-6 (lowest prices: 0.05-0.08 €/kWh)
- Use hours 10-14 if additional PPFD needed
- Avoid peak price hours 17-20 (0.25-0.30 €/kWh)

**OUTPUT REQUIREMENTS:**
Provide ONLY valid JSON with hourly LED allocations:
{
  "led_allocations": [hour0, hour1, hour2, ..., hour23]
}"""

def create_test_set(version: str, input_file: str, output_file: str):
    """
    Create a test set with the specified prompt version
    
    Args:
        version: Prompt version ('v1', 'v2', or 'v3')
        input_file: Path to the base test set JSON file
        output_file: Path for the output test set file
    """
    
    # Load base test set
    try:
        with open(input_file, 'r') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        return False
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {input_file}")
        return False
    
    # Select prompt based on version
    prompt_functions = {
        'v1': get_v1_prompt,
        'v2': get_v2_prompt,
        'v3': get_v3_prompt
    }
    
    if version not in prompt_functions:
        print(f"Error: Unknown version {version}. Available: {list(prompt_functions.keys())}")
        return False
    
    prompt_text = prompt_functions[version]()
    
    # Update each item in the test set
    for item in test_data:
        if 'messages' in item and len(item['messages']) > 0:
            # Update the user message with the new prompt
            item['messages'][0]['content'] = prompt_text + "\n\n" + item['messages'][0]['content'].split('\n\n', 1)[-1]
    
    # Save updated test set
    try:
        with open(output_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        print(f"Successfully created {output_file} with {version} prompts")
        print(f"Total test cases: {len(test_data)}")
        return True
    except Exception as e:
        print(f"Error saving output file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate test sets with different prompt versions')
    parser.add_argument('--version', choices=['v1', 'v2', 'v3'], required=True,
                       help='Prompt version to generate')
    parser.add_argument('--input', default='data/raw_data/test_set.json',
                       help='Input base test set file')
    parser.add_argument('--output', required=True,
                       help='Output test set file')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    success = create_test_set(args.version, args.input, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 