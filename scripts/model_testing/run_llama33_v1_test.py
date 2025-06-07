#!/usr/bin/env python3
"""
Test Llama 3.3 70B Instruct (free) on v1 clean dataset
"""
import json
import requests
import time
from datetime import datetime

# Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL_NAME = "meta-llama/llama-3.3-70b-instruct:free"
INPUT_FILE = "data/test_sets/test_dataset_v1_prompts_clean.json"
OUTPUT_FILE = "results/model_outputs/meta-llama_llama-3.3-70b-instruct_free_results_v1_prompt.json"

def call_openrouter_api(prompt_text):
    """Call OpenRouter API with the given prompt"""
    start_time = time.time()
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "ThesisModelTesting",
            },
            json={
                "model": OPENROUTER_MODEL_NAME,
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.1
            }
        )
        response.raise_for_status()
        api_response = response.json()
        end_time = time.time()
        duration = end_time - start_time

        if api_response.get("choices") and len(api_response["choices"]) > 0:
            assistant_reply = api_response["choices"][0].get("message", {}).get("content")
            return assistant_reply, duration
        else:
            print(f"Warning: Unexpected API response format: {api_response}")
            return None, duration

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"Error calling OpenRouter API: {e}")
        return None, duration

def main():
    """Main function to run the test"""
    print(f"🤖 Testing {OPENROUTER_MODEL_NAME} on {INPUT_FILE}")
    print(f"📝 Results will be saved to {OUTPUT_FILE}")
    
    # Load test data
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Input file '{INPUT_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{INPUT_FILE}'.")
        return

    results = []
    total_items = len(test_data)
    successful_calls = 0
    total_api_time = 0

    print(f"📊 Processing {total_items} test cases...")

    for i, item in enumerate(test_data):
        print(f"\n🔄 Processing item {i+1}/{total_items}...")
        
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
        
        print(f"  📤 Sending prompt to model...")
        model_response, api_duration = call_openrouter_api(user_prompt)
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

    # Save results
    print(f"\n💾 Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Total test cases: {total_items}")
    print(f"   Successful API calls: {successful_calls}")
    print(f"   Success rate: {successful_calls/total_items*100:.1f}%")
    print(f"   Total API time: {total_api_time:.1f}s")
    print(f"   Average per call: {total_api_time/total_items:.1f}s")
    print(f"   Results saved to: {OUTPUT_FILE}")
    print(f"   💰 Cost: FREE! (Llama 3.3 70B Instruct is completely free)")
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    main() 