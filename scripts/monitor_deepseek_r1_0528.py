#!/usr/bin/env python3
"""
Monitor DeepSeek R1 0528 progress and detect rate limiting issues
"""
import json
import os
import time
from datetime import datetime, timedelta

def monitor_deepseek_r1_0528():
    """Monitor the DeepSeek R1 0528 testing progress"""
    
    results_file = "results/model_outputs/deepseek_deepseek-r1-0528_free_results_v2_prompt.json"
    
    print("🔍 DeepSeek R1 0528 Monitor")
    print("=" * 50)
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        print("   The DeepSeek R1 0528 test hasn't started or results file was moved.")
        return
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ Could not parse results file - it may be incomplete or corrupted")
        return
    except Exception as e:
        print(f"❌ Error reading results file: {e}")
        return
    
    if not results:
        print("📝 Results file is empty - test just started")
        return
    
    # Analyze results
    total_expected = 72  # Based on your test dataset
    completed_items = len(results)
    successful_responses = sum(1 for r in results if r.get("openrouter_model_response") is not None)
    json_valid_responses = 0
    total_time = 0
    rate_limited_responses = 0
    
    for result in results:
        duration = result.get("api_call_duration_seconds", 0)
        total_time += duration
        
        # Check if response is valid JSON
        response = result.get("openrouter_model_response")
        if response and isinstance(response, dict):
            json_valid_responses += 1
        
        # Detect potential rate limiting (very short response times usually indicate errors)
        if duration < 5 and response is None:
            rate_limited_responses += 1
    
    avg_response_time = total_time / completed_items if completed_items > 0 else 0
    
    # Status report
    print(f"📊 Current Status:")
    print(f"   Completed items: {completed_items}/{total_expected} ({completed_items/total_expected*100:.1f}%)")
    print(f"   Successful responses: {successful_responses}")
    print(f"   Valid JSON responses: {json_valid_responses}")
    print(f"   Success rate: {successful_responses/completed_items*100:.1f}%" if completed_items > 0 else "   Success rate: N/A")
    print(f"   JSON success rate: {json_valid_responses/completed_items*100:.1f}%" if completed_items > 0 else "   JSON success rate: N/A")
    print(f"   Average response time: {avg_response_time:.1f}s")
    print(f"   Total API time so far: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    
    if rate_limited_responses > 0:
        print(f"   ⚠️ Potential rate limited responses: {rate_limited_responses}")
        print(f"   Rate limiting percentage: {rate_limited_responses/completed_items*100:.1f}%")
    
    # Time estimation
    if completed_items > 0 and avg_response_time > 0:
        remaining_items = total_expected - completed_items
        estimated_remaining_time = remaining_items * avg_response_time
        estimated_completion = datetime.now() + timedelta(seconds=estimated_remaining_time)
        
        print(f"\n⏱️ Time Estimates:")
        print(f"   Remaining items: {remaining_items}")
        print(f"   Estimated remaining time: {estimated_remaining_time/60:.1f} minutes ({estimated_remaining_time/3600:.1f} hours)")
        print(f"   Estimated completion: {estimated_completion.strftime('%H:%M:%S')}")
    
    # Rate limiting assessment
    print(f"\n🚨 Rate Limiting Assessment:")
    if rate_limited_responses == 0:
        print("   ✅ No rate limiting detected - model is running smoothly")
    elif rate_limited_responses < completed_items * 0.1:
        print("   ⚠️ Minor rate limiting detected - acceptable level")
    elif rate_limited_responses < completed_items * 0.3:
        print("   ⚠️ Moderate rate limiting detected - consider increasing delays")
    else:
        print("   🚨 SEVERE rate limiting detected!")
        print("   🔧 RECOMMENDATION: Stop the current test and restart with:")
        print("      - Longer delays between requests (15-30 seconds)")
        print("      - More aggressive retry logic")
        print("      - Consider running during off-peak hours")
    
    # Performance assessment for thesis
    print(f"\n📚 Thesis Analysis Readiness:")
    if json_valid_responses >= 30:
        print(f"   🎉 EXCELLENT! {json_valid_responses} valid responses - perfect for thesis analysis")
    elif json_valid_responses >= 20:
        print(f"   ✅ GOOD! {json_valid_responses} valid responses - sufficient for thesis analysis")
    elif json_valid_responses >= 15:
        print(f"   ⚠️ MODERATE! {json_valid_responses} valid responses - borderline for thesis analysis")
    elif json_valid_responses > 0:
        print(f"   ❌ LIMITED! Only {json_valid_responses} valid responses - insufficient for robust thesis analysis")
    else:
        print(f"   ❌ CRITICAL! No valid JSON responses yet - major issues detected")
    
    # Latest response analysis
    if results:
        latest_result = results[-1]
        latest_time = latest_result.get("api_call_duration_seconds", 0)
        latest_response = latest_result.get("openrouter_model_response")
        
        print(f"\n📱 Latest Response Analysis:")
        print(f"   Item {latest_result.get('item_index', '?')}: {latest_time:.1f}s")
        
        if latest_response is None:
            print("   ❌ No response received - possible rate limiting or error")
        elif isinstance(latest_response, dict):
            print("   ✅ Valid JSON response received")
        else:
            print("   ⚠️ Response received but not valid JSON")
    
    print(f"\n🔄 Run this monitor again with: python monitor_deepseek_r1_0528.py")
    print("=" * 50)

if __name__ == "__main__":
    monitor_deepseek_r1_0528() 