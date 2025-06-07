#!/usr/bin/env python3
"""
DeepSeek R1 Distill Response Post-Processor

This script attempts to extract valid JSON from DeepSeek R1 Distill responses
that failed JSON parsing due to reasoning text or formatting issues.
"""

import json
import re
import os
from pathlib import Path

def extract_json_from_response(response_text):
    """Extract JSON from response that may contain reasoning text"""
    
    if not response_text or response_text.strip() == "":
        return None
    
    # Method 1: Look for allocation_PPFD_per_hour object
    allocation_pattern = r'"allocation_PPFD_per_hour"\s*:\s*\{[^}]+\}'
    match = re.search(allocation_pattern, response_text)
    if match:
        try:
            json_str = "{" + match.group() + "}"
            return json.loads(json_str)
        except:
            pass
    
    # Method 2: Extract complete JSON object
    json_patterns = [
        r'\{[^{}]*"allocation_PPFD_per_hour"[^{}]*\{[^}]+\}[^{}]*\}',
        r'\{.*?"allocation_PPFD_per_hour".*?\}',
        r'\{[\s\S]*?"hour_0"[\s\S]*?\}',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    
    # Method 3: Extract hourly values and construct JSON
    hour_pattern = r'"hour_(\d+)"\s*:\s*([0-9.]+)'
    hour_matches = re.findall(hour_pattern, response_text)
    
    if len(hour_matches) >= 20:  # Need most hours
        allocation = {}
        for hour, value in hour_matches:
            allocation[f"hour_{hour}"] = float(value)
        
        # Fill missing hours with 0
        for h in range(24):
            if f"hour_{h}" not in allocation:
                allocation[f"hour_{h}"] = 0.0
        
        return {"allocation_PPFD_per_hour": allocation}
    
    return None

def fix_deepseek_distill_file(input_file, output_file):
    """Post-process a DeepSeek Distill results file to extract valid JSON"""
    
    print(f"🔧 Processing: {input_file}")
    
    try:
        with open(input_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {input_file}: {e}")
        return False
    
    fixed_count = 0
    total_responses = len(results)
    
    for i, item in enumerate(results):
        original_response = item.get('openrouter_model_response')
        
        # Skip if already valid JSON
        if isinstance(original_response, dict):
            continue
            
        # Skip if no response
        if not original_response:
            continue
            
        # Try to extract JSON from text response
        if isinstance(original_response, str):
            extracted_json = extract_json_from_response(original_response)
            
            if extracted_json:
                # Store original response for reference
                item['original_text_response'] = original_response
                item['openrouter_model_response'] = extracted_json
                item['post_processed'] = True
                fixed_count += 1
                print(f"✅ Fixed item {i+1}: Extracted valid JSON")
    
    # Save fixed results
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 POST-PROCESSING COMPLETE!")
        print(f"📊 Results Summary:")
        print(f"   Total responses: {total_responses}")
        print(f"   Fixed responses: {fixed_count}")
        print(f"   Success rate improvement: +{fixed_count/total_responses*100:.1f}%")
        print(f"💾 Saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving {output_file}: {e}")
        return False

if __name__ == "__main__":
    # Look for DeepSeek Distill results files
    results_dir = Path("results/model_outputs")
    
    distill_files = list(results_dir.glob("*deepseek*distill*.json"))
    
    if not distill_files:
        print("📁 No DeepSeek Distill result files found")
        print("📝 Place DeepSeek Distill results in results/model_outputs/")
        exit(1)
    
    for input_file in distill_files:
        # Create output filename
        output_file = input_file.parent / f"{input_file.stem}_fixed.json"
        
        print(f"\n🔧 PROCESSING: {input_file.name}")
        success = fix_deepseek_distill_file(input_file, output_file)
        
        if success:
            print(f"✅ Fixed file saved as: {output_file.name}")
        else:
            print(f"❌ Failed to process: {input_file.name}")
    
    print(f"\n🎯 POST-PROCESSING COMPLETE!")
    print(f"📈 Run the analysis system to see improved results:")
    print(f"   python auto_analyze_results.py") 