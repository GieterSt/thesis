#!/usr/bin/env python3
"""
Test DeepSeek R1 Distill Qwen 7B with robust retry logic
"""
import json
import requests
import time
import random
from datetime import datetime

def call_openrouter_api_with_retry(prompt_text, model_name, api_key, max_retries=5, base_delay=3):
    """Call OpenRouter API with retry logic and exponential backoff"""
    
    for attempt in range(max_retries):
        start_time = time.time()
        try:
            # Add random delay to avoid synchronization
            time.sleep(random.uniform(0.3, 1.0))
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "ThesisModelTesting",
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.1
                },
                timeout=180  # 3 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: 3s, 6s, 12s, 24s, 48s
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                    print(f"  ⏰ Rate limited. Waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  ❌ Rate limited after {max_retries} attempts")
                    return None, duration
            
            response.raise_for_status()
            api_response = response.json()

            if api_response.get("choices") and len(api_response["choices"]) > 0:
                assistant_reply = api_response["choices"][0].get("message", {}).get("content")
                return assistant_reply, duration
            else:
                print(f"  ⚠️ Unexpected API response format")
                return None, duration

        except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration = end_time - start_time
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"  ⚠️ Request error: {str(e)[:80]}... Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            else:
                print(f"  ❌ Request failed after {max_retries} attempts: {str(e)[:80]}...")
                return None, duration

    return None, 0

def test_deepseek_r1_distill():
    """Test DeepSeek R1 Distill Qwen 7B specifically"""
    
    model_name = "deepseek/deepseek-r1-distill-qwen-7b"
    input_file = "data/test_sets/test_dataset_v0_prompts_clean.json"
    output_file = "results/model_outputs/deepseek_deepseek-r1-distill-qwen-7b_results_v0_retry.json"
    request_delay = 5.0  # 5 seconds between requests
    
    OPENROUTER_API_KEY = "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"
    
    print(f"🚀 Testing DeepSeek R1 Distill Qwen 7B - Your Priority Model!")
    print(f"🤖 Model: {model_name}")
    print(f"📁 Input: {input_file}")
    print(f"📝 Output: {output_file}")
    print(f"⏱️ Request delay: {request_delay}s")
    print(f"🔄 Max retries: 5 with exponential backoff")
    print(f"💰 Cost: $0.10/$0.20 per million tokens")
    print(f"🎯 Target: 30+ valid JSON responses for thesis analysis")
    
    # Load test data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{input_file}'.")
        return

    results = []
    total_items = len(test_data)
    successful_calls = 0
    total_api_time = 0
    json_success_count = 0
    
    print(f"📊 Processing {total_items} test cases...\n")

    for i, item in enumerate(test_data):
        print(f"🔄 Processing item {i+1}/{total_items}...")
        
        # Find messages in the item structure
        messages_key = None
        for key in item.keys():
            if key.startswith('messages'):
                messages_key = key
                break
        
        if not messages_key or not item.get(messages_key):
            print(f"  ⚠️ Skipping item {i+1} - no messages found")
            continue

        # Extract user prompt from the messages
        user_prompt = None
        for message in item[messages_key]:
            if message.get("role") == "user":
                user_prompt = message.get("content")
                break

        if not user_prompt:
            print(f"  ⚠️ Skipping item {i+1} - no user prompt found")
            continue
        
        print(f"  📤 Sending prompt to DeepSeek R1 Distill...")
        model_response, api_duration = call_openrouter_api_with_retry(
            user_prompt, model_name, OPENROUTER_API_KEY
        )
        total_api_time += api_duration
        
        if model_response is not None:
            successful_calls += 1
            print(f"  ✅ Response received ({api_duration:.2f}s)")
        else:
            print(f"  ❌ No response received ({api_duration:.2f}s)")

        # Try to parse response as JSON
        model_response_json = None
        error_message = None
        
        if model_response:
            # Clean response (remove markdown if present)
            cleaned_response = model_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()

            try:
                model_response_json = json.loads(cleaned_response)
                json_success_count += 1
                print(f"  ✅ Valid JSON response parsed")
            except json.JSONDecodeError as e:
                print(f"  ⚠️ Response is not valid JSON: {e}")
                model_response_json = cleaned_response
                error_message = "Response was not valid JSON"

        # Store result
        result = {
            "item_index": i + 1,
            "original_user_prompt": user_prompt,
            "openrouter_model_response": model_response_json,
            "api_call_duration_seconds": api_duration
        }
        
        if error_message:
            result["error_message"] = error_message
            
        results.append(result)
        
        # Progress update every 10 items
        if (i + 1) % 10 == 0:
            current_success_rate = (successful_calls / (i + 1)) * 100
            current_json_rate = (json_success_count / (i + 1)) * 100 if successful_calls > 0 else 0
            avg_time = total_api_time / (i + 1) if i > 0 else 0
            print(f"  📈 Progress: {i+1}/{total_items} | Success: {current_success_rate:.1f}% | JSON: {current_json_rate:.1f}% | Avg: {avg_time:.1f}s")
        
        # Delay between requests
        if i < total_items - 1:
            print(f"  ⏱️ Waiting {request_delay}s before next request...")
            time.sleep(request_delay)

    # Save results
    print(f"\n💾 Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Print comprehensive summary
    print(f"\n🎯 DeepSeek R1 Distill Qwen 7B Test Summary:")
    print(f"{'='*70}")
    print(f"   Total test cases: {total_items}")
    print(f"   Successful API calls: {successful_calls}")
    print(f"   Success rate: {successful_calls/total_items*100:.1f}%")
    print(f"   Valid JSON responses: {json_success_count}")
    print(f"   JSON success rate: {json_success_count/total_items*100:.1f}%")
    print(f"   Total API time: {total_api_time:.1f}s")
    if successful_calls > 0:
        print(f"   Average per successful call: {total_api_time/successful_calls:.1f}s")
        estimated_cost = (successful_calls * 2000) * 0.0001  # Rough estimate
        print(f"   Estimated cost: ~${estimated_cost:.3f}")
    print(f"   Results saved to: {output_file}")
    print(f"\n{'='*70}")
    
    # Quality assessment
    if json_success_count >= 30:
        print(f"🎉 EXCELLENT! {json_success_count} valid JSON responses - perfect for thesis analysis!")
    elif json_success_count >= 20:
        print(f"✅ GOOD! {json_success_count} valid JSON responses - sufficient for thesis analysis")
    else:
        print(f"⚠️ LIMITED! Only {json_success_count} valid JSON responses - may need improvement")
    
    print(f"\n✅ DeepSeek R1 Distill Qwen 7B test completed!")

if __name__ == "__main__":
    test_deepseek_r1_distill() 