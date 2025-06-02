import json
import re

NEW_PROMPT_TEMPLATE = """I need you to create an optimal LED lighting schedule for a greenhouse.

Goal:
Create the most cost-efficient LED lighting schedule that allocates exactly {TOTAL_PPFD_REQUIREMENT} PPFD-hours across a 24-hour period.

Return Format:
CRITICAL: Your ENTIRE response must be ONLY this exact JSON structure:

{{
  "allocation_PPFD_per_hour": {{
    "hour_0": 0.0,
    "hour_1": 0.0,
    "hour_2": 0.0,
    "hour_3": 0.0,
    "hour_4": 0.0,
    "hour_5": 0.0,
    "hour_6": 0.0,
    "hour_7": 0.0,
    "hour_8": 0.0,
    "hour_9": 0.0,
    "hour_10": 0.0,
    "hour_11": 0.0,
    "hour_12": 0.0,
    "hour_13": 0.0,
    "hour_14": 0.0,
    "hour_15": 0.0,
    "hour_16": 0.0,
    "hour_17": 0.0,
    "hour_18": 0.0,
    "hour_19": 0.0,
    "hour_20": 0.0,
    "hour_21": 0.0,
    "hour_22": 0.0,
    "hour_23": 0.0
  }}
}}

Do NOT include any text before or after the JSON. No explanations, no thinking, no comments.
Your response must be directly parseable by JSON.parse().

Warnings:
- Your entire response must be ONLY valid JSON
- Replace the 0.0 values with your calculated allocations
- Never allocate more than the maximum capacity for any hour
- Do not allocate any PPFD to hours with 0 capacity
- Ensure your total allocation equals exactly {TOTAL_PPFD_REQUIREMENT} PPFD-hours
- Use a greedy algorithm prioritizing hours with the lowest EUR/PPFD ranking first

Context Dump:
Date: {DATE}
Daily total PPFD requirement: {TOTAL_PPFD_REQUIREMENT}
EUR/PPFD rankings by hour (1=cheapest): {EUR_PPFD_RANKINGS_JSON}
Max PPFD capacity by hour: {MAX_CAPACITY_JSON}

ONLY RETURN THE JSON. NO OTHER TEXT."""

# SOURCE_FILE now points to the original test set with correct dates
SOURCE_FILE_WITH_CORRECT_DATES = "test_set.json" 
OUTPUT_FILE = "test_set_clod.json" # This will be overwritten with new prompts

def extract_data_from_original_prompt(original_prompt_text):
    """
    Extracts data from the original prompt format in test_set.json.
    The key difference is that this prompt should reliably contain the actual date.
    """
    data = {}
    try:
        # Date is at the beginning of the prompt
        date_match = re.search(r"Date: (\d{4}-\d{2}-\d{2})", original_prompt_text)
        if date_match:
            data['DATE'] = date_match.group(1).strip()
        else:
            data['DATE'] = "ErrorExtractingDate_NotFound"

        # Other fields are on separate lines after "Optimize LED lighting schedule:"
        ppfd_match = re.search(r"- Daily total PPFD requirement: ([\d.]+)", original_prompt_text)
        if ppfd_match:
            data['TOTAL_PPFD_REQUIREMENT'] = ppfd_match.group(1).strip()

        rankings_match = re.search(r"- EUR/PPFD rankings by hour: ({.*?})", original_prompt_text, re.DOTALL)
        if rankings_match:
            data['EUR_PPFD_RANKINGS_JSON'] = rankings_match.group(1).strip()

        capacities_match = re.search(r"- Max PPFD capacity by hour: ({.*?})", original_prompt_text, re.DOTALL)
        if capacities_match:
            data['MAX_CAPACITY_JSON'] = capacities_match.group(1).strip()

        required_keys = ['DATE', 'TOTAL_PPFD_REQUIREMENT', 'EUR_PPFD_RANKINGS_JSON', 'MAX_CAPACITY_JSON']
        missing_keys = [key for key in required_keys if key not in data or not data[key] or data[key].startswith("ErrorExtractingDate")]
        
        if missing_keys:
            print(f"Warning: Could not extract all required fields from ORIGINAL prompt. Missing/Error: {missing_keys}")
            print(f"Original prompt snippet (first 500 chars):\n{original_prompt_text[:500]}...")
            print(f"Extracted data so far: {data}")
            # Try to find if it was a Context Dump structure that was missed before
            context_dump_match = re.search(r"Context Dump:(.*)", original_prompt_text, re.DOTALL)
            if context_dump_match:
                print("Note: A 'Context Dump:' section WAS found. Previous regex might have failed for it.")
                context_dump_content = context_dump_match.group(1).strip()
                if 'DATE' not in data or data['DATE'].startswith("ErrorExtractingDate"):
                    date_match_ctx = re.search(r"Date: (\d{4}-\d{2}-\d{2})", context_dump_content)
                    if date_match_ctx: data['DATE'] = date_match_ctx.group(1).strip()
                if 'TOTAL_PPFD_REQUIREMENT' not in data:
                    ppfd_match_ctx = re.search(r"Daily total PPFD requirement:\s*([\d.]+)", context_dump_content)
                    if ppfd_match_ctx: data['TOTAL_PPFD_REQUIREMENT'] = ppfd_match_ctx.group(1).strip()
                if 'EUR_PPFD_RANKINGS_JSON' not in data:
                    rankings_match_ctx = re.search(r"EUR/PPFD rankings by hour \(1=cheapest\): ({.*?})", context_dump_content, re.DOTALL)
                    if rankings_match_ctx: data['EUR_PPFD_RANKINGS_JSON'] = rankings_match_ctx.group(1).strip()
                if 'MAX_CAPACITY_JSON' not in data:
                    capacities_match_ctx = re.search(r"Max PPFD capacity by hour: ({.*?})", context_dump_content, re.DOTALL)
                    if capacities_match_ctx: data['MAX_CAPACITY_JSON'] = capacities_match_ctx.group(1).strip()
                
                missing_keys_after_ctx_check = [key for key in required_keys if key not in data or not data[key] or data[key].startswith("ErrorExtractingDate")]
                if not missing_keys_after_ctx_check:
                    print("Successfully extracted data after checking Context Dump as fallback.")
                else:
                    print(f"Still missing after Context Dump check: {missing_keys_after_ctx_check}. Data: {data}")
                    return None # Failed even with context dump fallback
            else: # No Context Dump either
                return None
        
        try:
            json.loads(data['EUR_PPFD_RANKINGS_JSON'])
            json.loads(data['MAX_CAPACITY_JSON'])
        except json.JSONDecodeError as e:
            print(f"Warning: Extracted rankings or capacities string from ORIGINAL prompt is not valid JSON: {e}")
            print(f"Rankings: {data.get('EUR_PPFD_RANKINGS_JSON')}")
            print(f"Capacities: {data.get('MAX_CAPACITY_JSON')}")
            return None

        return data
    except Exception as e:
        print(f"General error in extract_data_from_original_prompt: {e}")
        print(f"Prompt snippet: {original_prompt_text[:300]}...")
        return None

def main():
    try:
        with open(SOURCE_FILE_WITH_CORRECT_DATES, 'r', encoding='utf-8') as f:
            source_test_data = json.load(f) # Load from test_set.json
    except FileNotFoundError:
        print(f"Error: Source file with correct dates '{SOURCE_FILE_WITH_CORRECT_DATES}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{SOURCE_FILE_WITH_CORRECT_DATES}'.")
        return

    # We will build a new list of items for test_set_clod.json
    updated_test_data_for_clod = [] 
    updated_count = 0
    processed_count = 0

    for item in source_test_data:
        processed_count +=1
        if not item.get("messages"):
            print(f"Skipping item {processed_count} from source due to missing 'messages' field.")
            continue

        original_user_message_content = None
        assistant_message_content = None # We need to preserve the assistant response

        for message in item["messages"]:
            if message.get("role") == "user":
                original_user_message_content = message.get("content")
            elif message.get("role") == "assistant":
                assistant_message_content = message.get("content") # Capture assistant content
        
        if not original_user_message_content:
            print(f"Skipping item {processed_count} from source due to missing user message content.")
            continue
        
        if assistant_message_content is None: # Ensure assistant message exists
            print(f"Skipping item {processed_count} from source due to missing assistant message content.")
            continue

        extracted_info = extract_data_from_original_prompt(original_user_message_content)

        if extracted_info:
            try:
                new_prompt_content = NEW_PROMPT_TEMPLATE.format(
                    TOTAL_PPFD_REQUIREMENT=extracted_info['TOTAL_PPFD_REQUIREMENT'],
                    DATE=extracted_info['DATE'], # This should now be the correct date
                    EUR_PPFD_RANKINGS_JSON=extracted_info['EUR_PPFD_RANKINGS_JSON'],
                    MAX_CAPACITY_JSON=extracted_info['MAX_CAPACITY_JSON']
                )
                
                # Create the new item structure for test_set_clod.json
                new_clod_item = {
                    "messages": [
                        {"role": "user", "content": new_prompt_content},
                        {"role": "assistant", "content": assistant_message_content} # Keep original assistant response
                    ]
                }
                updated_test_data_for_clod.append(new_clod_item)
                updated_count += 1
            except KeyError as ke:
                print(f"Skipping item {processed_count} due to missing key '{ke}' during new prompt formatting. Extracted info from original: {extracted_info}")
                continue
        else:
            print(f"Could not create new prompt for item {processed_count} as data extraction from original prompt failed.")

    if updated_count > 0:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(updated_test_data_for_clod, f, indent=2, ensure_ascii=False)
            print(f"Successfully updated/created prompts for {updated_count}/{processed_count} items in '{OUTPUT_FILE}'.")
        except IOError:
            print(f"Error: Could not write updated data to '{OUTPUT_FILE}'.")
    else:
        print(f"No prompts were updated out of {processed_count} items processed from source. Please check extraction logic or source file content.")

if __name__ == "__main__":
    main() 