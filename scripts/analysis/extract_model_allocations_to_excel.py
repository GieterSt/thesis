import json
import pandas as pd
import re

# Configuration
MODEL_RESULTS_FILE = 'anthropic_claude-3.7-sonnet_results.json'
OUTPUT_EXCEL_FILE = 'anthropic_claude-3.7-sonnet_allocations.xlsx'

def extract_date_from_prompt(prompt_text):
    """Extracts the date from the user prompt string."""
    if not prompt_text or not isinstance(prompt_text, str):
        return "UnknownDate"
    # Regex to find "Date: YYYY-MM-DD" in the Context Dump
    match = re.search(r"Context Dump:\nDate: (\d{4}-\d{2}-\d{2})", prompt_text)
    if match:
        return match.group(1)
    else:
        # Fallback if the primary pattern isn't found (e.g. slight variations)
        match_fallback = re.search(r"Date: (\d{4}-\d{2}-\d{2})", prompt_text)
        if match_fallback:
            return match_fallback.group(1)
    return "UnknownDate" # Default if no date is found

def main():
    try:
        with open(MODEL_RESULTS_FILE, 'r', encoding='utf-8') as f:
            model_results = json.load(f)
    except FileNotFoundError:
        print(f"Error: Model results file '{MODEL_RESULTS_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{MODEL_RESULTS_FILE}'.")
        return

    all_allocations_data = []

    for item_index, result_item in enumerate(model_results):
        item_num = result_item.get("item_index", item_index + 1) # Use item_index from file if available
        prompt = result_item.get("original_user_prompt")
        date_str = extract_date_from_prompt(prompt)

        model_response = result_item.get("openrouter_model_response")
        
        hourly_allocations = None
        
        if isinstance(model_response, str): # If response was stored as a string
            try:
                model_response_json = json.loads(model_response)
                if isinstance(model_response_json, dict): # Ensure it's a dict after loading
                    hourly_allocations = model_response_json.get("allocation_PPFD_per_hour")
            except json.JSONDecodeError:
                print(f"Warning: Could not parse model response string as JSON for item {item_num}. Raw response: '{model_response[:100]}...'")
        elif isinstance(model_response, dict): # If response is already a dictionary
            hourly_allocations = model_response.get("allocation_PPFD_per_hour")
        else:
            print(f"Warning: Model response for item {item_num} is neither a string nor a dict. Skipping. Response type: {type(model_response)}")
            
        if hourly_allocations and isinstance(hourly_allocations, dict):
            for hour in range(24):
                hour_key = f"hour_{hour}"
                ppfd_value = hourly_allocations.get(hour_key)
                
                if ppfd_value is not None:
                    try:
                        # Ensure ppfd_value is float or can be converted
                        ppfd_value_float = float(ppfd_value)
                        all_allocations_data.append({
                            'date': date_str,
                            'hour': hour,
                            'ppfd_allocated_by_model': ppfd_value_float
                        })
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert PPFD value '{ppfd_value}' to float for item {item_num}, date {date_str}, hour {hour_key}. Storing as is or None.")
                        all_allocations_data.append({
                            'date': date_str,
                            'hour': hour,
                            'ppfd_allocated_by_model': ppfd_value # Store as is, or handle as error
                        })
                else:
                    print(f"Warning: Missing allocation for {hour_key} in item {item_num}, date {date_str}. Storing as None.")
                    all_allocations_data.append({
                        'date': date_str,
                        'hour': hour,
                        'ppfd_allocated_by_model': None
                    })
        else:
            if result_item.get("error_message") == "Response was not valid JSON":
                 print(f"Info: Item {item_num} (date {date_str}) had a non-JSON response. Skipping allocation extraction for this item as per previous error.")
            elif result_item.get("error_message") == "No response content from model":
                 print(f"Info: Item {item_num} (date {date_str}) had no model response. Skipping allocation extraction for this item.")
            else:
                print(f"Warning: 'allocation_PPFD_per_hour' not found or not a dict in model response for item {item_num}, date {date_str}. Model response: {str(model_response)[:200]}...")
            # Add 24 rows with None for this date if no valid allocations are found
            for hour in range(24):
                all_allocations_data.append({
                    'date': date_str,
                    'hour': hour,
                    'ppfd_allocated_by_model': None
                })


    if not all_allocations_data:
        print("No allocation data was extracted. The output Excel file will be empty or not created.")
        return

    df = pd.DataFrame(all_allocations_data)
    
    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"Successfully extracted allocations to '{OUTPUT_EXCEL_FILE}'.")
    except Exception as e:
        print(f"Error writing DataFrame to Excel file '{OUTPUT_EXCEL_FILE}': {e}")

if __name__ == '__main__':
    main() 