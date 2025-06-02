import json
import requests
import time

# --- Configuration ---
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL_NAME = "openai/o1"
INPUT_FILE = "test_set_clod_v3.json"

# Generate output file name from model name and input file type
sanitized_model_name = OPENROUTER_MODEL_NAME.replace("/", "_").replace(":", "_")
file_suffix = ""
if "_v2.json" in INPUT_FILE:
    file_suffix = "_v2_prompt"
elif "_v3.json" in INPUT_FILE:
    file_suffix = "_v3_prompt"
OUTPUT_FILE = f"{sanitized_model_name}_results{file_suffix}.json"

YOUR_SITE_URL = "http://localhost"
YOUR_APP_NAME = "ThesisModelTesting"

# --- API Call Function ---
def call_openrouter_api(prompt_text):
    if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE" or not OPENROUTER_API_KEY:
        print("ERROR: Please set your OpenRouter API key.")
        return None, 0
    if OPENROUTER_MODEL_NAME == "MODEL_NAME_HERE" or not OPENROUTER_MODEL_NAME:
        print("ERROR: Please specify the OpenRouter model name.")
        return None, 0

    start_time = time.time()
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_APP_NAME,
            },
            data=json.dumps({
                "model": OPENROUTER_MODEL_NAME,
                "messages": [
                    {"role": "user", "content": prompt_text}
                ]
            })
        )
        response.raise_for_status()
        api_response_json = response.json()
        end_time = time.time()
        duration = end_time - start_time

        if api_response_json.get("choices") and len(api_response_json["choices"]) > 0:
            assistant_reply = api_response_json["choices"][0].get("message", {}).get("content")
            return assistant_reply, duration
        else:
            print(f"Warning: Unexpected API response format: {api_response_json}")
            return None, duration

    except requests.exceptions.RequestException as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"Error calling OpenRouter API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None, duration
    except json.JSONDecodeError as e:
        end_time = time.time()
        duration = end_time - start_time
        # response object might not be defined here if json.loads(response.text) was the one that failed
        # but if requests.post was successful, response.text should be available.
        # However, to be safe, let's assume response might not always be available or have .text
        error_context = ""
        try:
            error_context = response.text
        except NameError:
            error_context = "Response object not available"
        except AttributeError:
            error_context = "Response object does not have text attribute"
        print(f"Error decoding JSON response from OpenRouter: {e}. Response text: {error_context}")
        return None, duration

# --- Main Script ---
def main():
    script_start_time = time.time()
    total_api_call_time = 0
    successful_api_calls = 0

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{INPUT_FILE}'.")
        return

    results = []
    items_to_process = test_data
    total_items_to_process_count = len(items_to_process)

    print(f"Starting to process {total_items_to_process_count} item(s) from '{INPUT_FILE}' using model '{OPENROUTER_MODEL_NAME}'...")

    for i, item in enumerate(items_to_process):
        print(f"Processing item {i+1}/{total_items_to_process_count}...")
        if not item.get("messages") or len(item["messages"]) < 2:
            print(f"  Skipping item {i+1} due to unexpected format: {item}")
            continue

        user_prompt = None
        original_assistant_response_content = None

        for message in item["messages"]:
            if message.get("role") == "user":
                user_prompt = message.get("content")
            elif message.get("role") == "assistant":
                original_assistant_response_content = message.get("content")

        if not user_prompt:
            print(f"  Skipping item {i+1} as no user prompt was found.")
            continue
        
        original_assistant_json = None
        try:
            if original_assistant_response_content:
                 original_assistant_json = json.loads(original_assistant_response_content)
        except (json.JSONDecodeError, TypeError):
            original_assistant_json = original_assistant_response_content
            print(f"  Warning: Could not parse original assistant content for item {i+1} as JSON. Storing as is.")

        print(f"  Prompting model for item {i+1}...")
        model_response_text, api_call_duration = call_openrouter_api(user_prompt)
        total_api_call_time += api_call_duration
        if model_response_text is not None: # Counting successful if we got any text back, even if not JSON
            successful_api_calls +=1
        print(f"  API call for item {i+1} took {api_call_duration:.2f} seconds.")
        
        model_response_json = None
        if model_response_text:
            # Attempt to strip markdown code block fences if present
            cleaned_response_text = model_response_text.strip()
            if cleaned_response_text.startswith("```json"):
                cleaned_response_text = cleaned_response_text[7:] # Remove ```json
            elif cleaned_response_text.startswith("```"):
                 cleaned_response_text = cleaned_response_text[3:] # Remove ```
            
            if cleaned_response_text.endswith("```"):
                cleaned_response_text = cleaned_response_text[:-3] # Remove ```
            
            cleaned_response_text = cleaned_response_text.strip() # Strip any leading/trailing whitespace again

            try:
                model_response_json = json.loads(cleaned_response_text)
            except json.JSONDecodeError as e:
                print(f"  CRITICAL ERROR: Model response for item {i+1} was not valid JSON after cleaning. Halting script.")
                print(f"  Error details: {e}")
                print(f"  Original response snippet: '{model_response_text[:500]}...'")
                print(f"  Cleaned response snippet: '{cleaned_response_text[:500]}...'")
                # Store the raw text if it's not JSON, then break
                model_response_json = model_response_text 
                results.append({
                    "item_index": i + 1,
                    "original_user_prompt": user_prompt,
                    "original_assistant_response": original_assistant_json,
                    "openrouter_model_response": model_response_json, # Storing the raw, non-JSON response
                    "api_call_duration_seconds": api_call_duration,
                    "error_message": "Response was not valid JSON"
                })
                break # Stop processing further items
        else:
            print(f"  No response content received from model for item {i+1}.")
            # Potentially add a placeholder or skip appending if no response is critical
            results.append({
                "item_index": i + 1,
                "original_user_prompt": user_prompt,
                "original_assistant_response": original_assistant_json,
                "openrouter_model_response": None, # Explicitly None for no response
                "api_call_duration_seconds": api_call_duration,
                "error_message": "No response content from model"
            })
            # Decide if "no response" should also halt the script. For now, it continues.
            # If it should halt, add 'break' here too.

        # This append is now conditional or handled within the try/except for JSON parsing
        # Only append if we haven't already appended in the error case and decided to break
        if model_response_text and model_response_json != model_response_text: # True if JSON was valid and parsed
            results.append({
                "item_index": i + 1,
                "original_user_prompt": user_prompt,
                "original_assistant_response": original_assistant_json,
                "openrouter_model_response": model_response_json,
                "api_call_duration_seconds": api_call_duration
            })
        elif not model_response_text and not any(r["item_index"] == i + 1 for r in results): # Ensure item not already added if no response
             results.append({ # This case might be redundant if handled by the 'else' block above, review logic
                "item_index": i + 1,
                "original_user_prompt": user_prompt,
                "original_assistant_response": original_assistant_json,
                "openrouter_model_response": None,
                "api_call_duration_seconds": api_call_duration,
                "error_message": "No response content from model (re-check append logic)"
            })

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Processing complete. Results saved to '{OUTPUT_FILE}'.")
    except IOError:
        print(f"Error: Could not write results to '{OUTPUT_FILE}'.")

    script_end_time = time.time()
    total_script_time = script_end_time - script_start_time
    average_api_call_time = total_api_call_time / successful_api_calls if successful_api_calls > 0 else 0

    print(f"\n--- Summary ---")
    print(f"Total items processed in this run: {len(results)}/{total_items_to_process_count}")
    print(f"Total script execution time: {total_script_time:.2f} seconds.")
    print(f"Total time spent on API calls: {total_api_call_time:.2f} seconds.")
    print(f"Number of successful API calls: {successful_api_calls}")
    print(f"Average API call time: {average_api_call_time:.2f} seconds.")

if __name__ == "__main__":
    main() 