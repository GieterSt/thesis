#!/usr/bin/env python3
"""
Improved Mistral 7B testing with enhanced retry logic and JSON handling
"""
import json
import requests
import time
import random
from datetime import datetime

def call_openrouter_api_with_retry(prompt_text, model_name, api_key, max_retries=7, base_delay=5):
    """Call OpenRouter API with aggressive retry logic for rate-limited models"""
    
    for attempt in range(max_retries):
        start_time = time.time()
        try:
            # Longer random delay for heavily rate-limited models
            time.sleep(random.uniform(1.0, 3.0))
            
            # Enhanced JSON instruction in prompt
            enhanced_prompt = f"""{prompt_text}

IMPORTANT: Please respond ONLY with valid JSON format. Do not include any markdown formatting, explanations, or additional text outside the JSON structure."""
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "ThesisModelTesting",
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": enhanced_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                timeout=300  # 5 minute timeout for slower models
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    # More aggressive backoff: 5s, 15s, 45s, 90s, 180s, 360s
                    delay = base_delay * (3 ** attempt) + random.uniform(5, 15)
                    delay = min(delay, 600)  # Cap at 10 minutes
                    print(f"  ⏰ Rate limited. Waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  ❌ Rate limited after {max_retries} attempts")
                    return None, duration
            
            if response.status_code == 502 or response.status_code == 503:  # Bad Gateway / Service Unavailable
                if attempt < max_retries - 1:
                    delay = 30 + random.uniform(10, 30)
                    print(f"  🔄 Server error ({response.status_code}). Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"  ❌ Server error after {max_retries} attempts")
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
                delay = base_delay * (2 ** attempt) + random.uniform(5, 15)
                print(f"  ⚠️ Request error: {str(e)[:80]}... Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            else:
                print(f"  ❌ Request failed after {max_retries} attempts: {str(e)[:80]}...")
                return None, duration

    return None, 0

def aggressive_json_parsing(response_text):
    """Attempt multiple strategies to extract JSON from response"""
    if not response_text:
        return None, "Empty response"
    
    # Strategy 1: Direct parsing
    try:
        return json.loads(response_text.strip()), None
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Remove markdown
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Find JSON in text
    import re
    json_pattern = r'\{.*\}'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match), None
        except json.JSONDecodeError:
            continue
    
    # Strategy 4: Extract between specific markers
    markers = [
        ('{', '}'),
        ('{"', '"}'),
    ]
    
    for start_marker, end_marker in markers:
        start_idx = response_text.find(start_marker)
        if start_idx != -1:
            end_idx = response_text.rfind(end_marker)
            if end_idx > start_idx:
                potential_json = response_text[start_idx:end_idx + len(end_marker)]
                try:
                    return json.loads(potential_json), None
                except json.JSONDecodeError:
                    continue
    
    return None, f"Could not extract valid JSON from response: {response_text[:100]}..."

def test_mistral_7b_improved():
    """Test Mistral 7B with improved retry and JSON handling"""
    
    model_name = "mistralai/mistral-7b-instruct:free"
    input_file = "data/test_sets/test_dataset_v0_prompts_clean.json"
    output_file = "results/model_outputs/mistralai_mistral-7b-instruct_free_results_v0_improved.json"
    request_delay = 8.0  # 8 seconds between requests
    
    OPENROUTER_API_KEY = "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"
    
    print(f"🔧 Testing Mistral 7B (Improved) - Fixing Rate Limiting & JSON Issues!")
    print(f"🤖 Model: {model_name}")
    print(f"📁 Input: {input_file}")
    print(f"📝 Output: {output_file}")
    print(f"⏱️ Request delay: {request_delay}s")
    print(f"🔄 Max retries: 7 with aggressive backoff")
    print(f"💰 Cost: FREE!")
    print(f"🎯 Target: Fix JSON parsing and rate limiting issues")
    
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
    rate_limit_count = 0
    
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
        
        print(f"  📤 Sending prompt to Mistral 7B (enhanced)...")
        model_response, api_duration = call_openrouter_api_with_retry(
            user_prompt, model_name, OPENROUTER_API_KEY
        )
        total_api_time += api_duration
        
        if model_response is not None:
            successful_calls += 1
            print(f"  ✅ Response received ({api_duration:.2f}s)")
        else:
            print(f"  ❌ No response received ({api_duration:.2f}s)")
            rate_limit_count += 1

        # Aggressive JSON parsing
        model_response_json = None
        error_message = None
        
        if model_response:
            model_response_json, parsing_error = aggressive_json_parsing(model_response)
            
            if model_response_json is not None:
                json_success_count += 1
                print(f"  ✅ Valid JSON response parsed")
            else:
                print(f"  ⚠️ JSON parsing failed: {parsing_error}")
                model_response_json = model_response
                error_message = parsing_error

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
        
        # Progress update every 5 items
        if (i + 1) % 5 == 0:
            current_success_rate = (successful_calls / (i + 1)) * 100
            current_json_rate = (json_success_count / (i + 1)) * 100 if successful_calls > 0 else 0
            avg_time = total_api_time / (i + 1) if i > 0 else 0
            print(f"  📈 Progress: {i+1}/{total_items} | Success: {current_success_rate:.1f}% | JSON: {current_json_rate:.1f}% | Avg: {avg_time:.1f}s | Rate limits: {rate_limit_count}")
        
        # Dynamic delay based on recent performance
        current_delay = request_delay
        if rate_limit_count > (i + 1) * 0.3:  # If > 30% rate limited
            current_delay = request_delay * 2
            print(f"  🐌 High rate limiting detected, increasing delay to {current_delay}s")
        
        # Delay between requests
        if i < total_items - 1:
            print(f"  ⏱️ Waiting {current_delay}s before next request...")
            time.sleep(current_delay)

    # Save results
    print(f"\n💾 Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Print comprehensive summary
    print(f"\n🔧 Mistral 7B (Improved) Test Summary:")
    print(f"{'='*70}")
    print(f"   Total test cases: {total_items}")
    print(f"   Successful API calls: {successful_calls}")
    print(f"   Success rate: {successful_calls/total_items*100:.1f}%")
    print(f"   Rate limited calls: {rate_limit_count}")
    print(f"   Rate limit percentage: {rate_limit_count/total_items*100:.1f}%")
    print(f"   Valid JSON responses: {json_success_count}")
    print(f"   JSON success rate: {json_success_count/total_items*100:.1f}%")
    print(f"   Total API time: {total_api_time:.1f}s")
    if successful_calls > 0:
        print(f"   Average per successful call: {total_api_time/successful_calls:.1f}s")
    print(f"   Results saved to: {output_file}")
    print(f"   💰 Cost: FREE!")
    print(f"\n{'='*70}")
    
    # Quality assessment
    if json_success_count >= 30:
        print(f"🎉 EXCELLENT! {json_success_count} valid JSON responses - perfect for thesis analysis!")
    elif json_success_count >= 20:
        print(f"✅ GOOD! {json_success_count} valid JSON responses - sufficient for thesis analysis")
    elif json_success_count >= 10:
        print(f"⚠️ MODERATE! {json_success_count} valid JSON responses - could work for thesis")
    else:
        print(f"❌ POOR! Only {json_success_count} valid JSON responses - needs more work")
    
    print(f"\n✅ Mistral 7B (Improved) test completed!")

if __name__ == "__main__":
    test_mistral_7b_improved() 