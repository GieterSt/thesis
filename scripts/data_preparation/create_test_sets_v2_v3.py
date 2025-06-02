import json
import re

NEW_PROMPT_TEMPLATE_V3 = \
"""You are an LED scheduling optimizer for greenhouse operations.

ROLE: Expert greenhouse lighting scheduler who must minimize electricity costs while meeting exact daily PPFD requirements.

TASK: Create the most cost-efficient LED lighting schedule that allocates EXACTLY {daily_total_PPFD} PPFD-hours across a 24-hour period.

CRITICAL CONSTRAINTS:
- The sum of all hour allocations MUST equal EXACTLY {daily_total_PPFD} (precision to 3 decimal places)
- Each hour's allocation MUST NOT exceed its maximum capacity
- Hours with 0 capacity MUST have 0 allocation

ALGORITHM - Follow these steps precisely:
Step 1: Identify all hours with capacity > 0
Step 2: Sort these hours by EUR/PPFD ranking (1=cheapest, 24=most expensive)
Step 3: Starting with the cheapest hour, allocate min(remaining_requirement, hour_capacity)
Step 4: Update remaining_requirement after each allocation
Step 5: Continue until remaining_requirement = 0
Step 6: Verify total allocation equals EXACTLY {daily_total_PPFD}

EXAMPLE:
Input: Daily requirement: 500.000, Rankings: {{ \"hour_0\": 2, \"hour_1\": 1 }}, Capacities: {{ \"hour_0\": 300.0, \"hour_1\": 400.0 }}
Output: {{ \"allocation_PPFD_per_hour\": {{ \"hour_0\": 200.0, \"hour_1\": 300.0 }} }}

YOUR INPUT DATA:
Date: {date}
Daily total PPFD requirement: {daily_total_PPFD}
EUR/PPFD rankings by hour (1=cheapest): {rankings}
Max PPFD capacity by hour: {capacities}

OUTPUT FORMAT - Return ONLY this JSON structure with NO additional text:
{{
  \"allocation_PPFD_per_hour\": {{
    \"hour_0\": 0.0,
    \"hour_1\": 0.0,
    \"hour_2\": 0.0,
    \"hour_3\": 0.0,
    \"hour_4\": 0.0,
    \"hour_5\": 0.0,
    \"hour_6\": 0.0,
    \"hour_7\": 0.0,
    \"hour_8\": 0.0,
    \"hour_9\": 0.0,
    \"hour_10\": 0.0,
    \"hour_11\": 0.0,
    \"hour_12\": 0.0,
    \"hour_13\": 0.0,
    \"hour_14\": 0.0,
    \"hour_15\": 0.0,
    \"hour_16\": 0.0,
    \"hour_17\": 0.0,
    \"hour_18\": 0.0,
    \"hour_19\": 0.0,
    \"hour_20\": 0.0,
    \"hour_21\": 0.0,
    \"hour_22\": 0.0,
    \"hour_23\": 0.0
  }}
}}
"""

SOURCE_FILE = "test_set.json"
OUTPUT_FILE = "test_set_clod_v3.json"

def extract_data_from_original_prompt(original_prompt_text):
    data = {}
    try:
        date_match = re.search(r"Date: (\d{4}-\d{2}-\d{2})", original_prompt_text)
        if date_match:
            data['date'] = date_match.group(1).strip()
        else:
            # Fallback for prompts that might have date in a different part or if regex fails
            # This part might need adjustment based on actual prompt structures if date is elsewhere
            # For now, assuming it's consistently "Date: YYYY-MM-DD"
            print(f"Warning: Date not found with primary regex in prompt: {original_prompt_text[:200]}")
            data['date'] = "UnknownDate"


        ppfd_match = re.search(r"- Daily total PPFD requirement: ([\d.]+)", original_prompt_text)
        if ppfd_match:
            data['daily_total_PPFD'] = ppfd_match.group(1).strip()
        else:
            # Fallback if the primary regex fails
            ppfd_match_alt = re.search(r"Daily total PPFD requirement:\s*([\d.]+)", original_prompt_text, re.IGNORECASE)
            if ppfd_match_alt:
                data['daily_total_PPFD'] = ppfd_match_alt.group(1).strip()
            else:
                print(f"Warning: Daily total PPFD requirement not found in prompt: {original_prompt_text[:300]}")
                return None


        rankings_match = re.search(r"- EUR/PPFD rankings by hour: ({.*?})", original_prompt_text, re.DOTALL)
        if rankings_match:
            data['rankings'] = rankings_match.group(1).strip()
        else:
             # Fallback if the primary regex fails
            rankings_match_alt = re.search(r"EUR/PPFD rankings by hour \(1=cheapest\):\s*({.*?})", original_prompt_text, re.DOTALL | re.IGNORECASE)
            if rankings_match_alt:
                data['rankings'] = rankings_match_alt.group(1).strip()
            else:
                print(f"Warning: EUR/PPFD rankings not found in prompt: {original_prompt_text[:400]}")
                return None

        capacities_match = re.search(r"- Max PPFD capacity by hour: ({.*?})", original_prompt_text, re.DOTALL)
        if capacities_match:
            data['capacities'] = capacities_match.group(1).strip()
        else:
            # Fallback if the primary regex fails
            capacities_match_alt = re.search(r"Max PPFD capacity by hour:\s*({.*?})", original_prompt_text, re.DOTALL | re.IGNORECASE)
            if capacities_match_alt:
                data['capacities'] = capacities_match_alt.group(1).strip()
            else:
                print(f"Warning: Max PPFD capacity not found in prompt: {original_prompt_text[:500]}")
                return None

        # Validate that extracted strings are valid JSON
        try:
            json.loads(data['rankings'])
            json.loads(data['capacities'])
        except json.JSONDecodeError as e:
            print(f"Warning: Extracted rankings or capacities string is not valid JSON: {e}")
            print(f"Rankings: {data.get('rankings')}")
            print(f"Capacities: {data.get('capacities')}")
            return None
        if data['date'] == "UnknownDate": # If date extraction failed, consider it a failure
             print("Error: Date extraction failed, cannot proceed for this item.")
             return None


        return data
    except Exception as e:
        print(f"General error in extract_data_from_original_prompt: {e}")
        print(f"Prompt snippet: {original_prompt_text[:300]}...")
        return None

def main():
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Source file '{SOURCE_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{SOURCE_FILE}'.")
        return

    updated_items = []
    updated_count = 0
    processed_count = 0

    for item_index, item in enumerate(source_data):
        processed_count += 1
        original_user_prompt = None
        original_assistant_response = None

        if not item.get("messages"):
            print(f"Skipping item {item_index+1} from source: 'messages' field missing.")
            continue

        for message in item["messages"]:
            if message.get("role") == "user":
                original_user_prompt = message.get("content")
            elif message.get("role") == "assistant":
                original_assistant_response = message.get("content")
        
        if not original_user_prompt:
            print(f"Skipping item {item_index+1}: User prompt content missing.")
            continue
        if not original_assistant_response:
            print(f"Skipping item {item_index+1}: Assistant response content missing.")
            continue

        extracted_info = extract_data_from_original_prompt(original_user_prompt)

        if extracted_info:
            try:
                # Ensure daily_total_PPFD is formatted to 3 decimal places for the prompt
                daily_ppfd_float = float(extracted_info['daily_total_PPFD'])
                formatted_daily_ppfd = f"{daily_ppfd_float:.3f}"

                new_prompt_content = NEW_PROMPT_TEMPLATE_V3.format(
                    date=extracted_info['date'],
                    daily_total_PPFD=formatted_daily_ppfd,
                    rankings=extracted_info['rankings'],
                    capacities=extracted_info['capacities']
                )
                
                updated_item = {
                    "messages": [
                        {"role": "user", "content": new_prompt_content},
                        {"role": "assistant", "content": original_assistant_response} 
                    ]
                }
                updated_items.append(updated_item)
                updated_count += 1
            except KeyError as ke:
                print(f"Skipping item {item_index+1} due to missing key '{ke}' during new prompt formatting. Extracted: {extracted_info}")
            except ValueError as ve:
                print(f"Skipping item {item_index+1} due to ValueError (likely in PPFD formatting): {ve}. Extracted: {extracted_info}")

        else:
            print(f"Could not create new prompt for item {item_index+1} from source (extraction failed). Original prompt snippet: {original_user_prompt[:200]}...")

    if updated_count > 0:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(updated_items, f, indent=2, ensure_ascii=False)
            print(f"Successfully created v3 prompts for {updated_count}/{processed_count} items in '{OUTPUT_FILE}'.")
        except IOError:
            print(f"Error: Could not write updated data to '{OUTPUT_FILE}'.")
    else:
        print(f"No v3 prompts were created out of {processed_count} items. Check extraction logic or source file '{SOURCE_FILE}'.")

if __name__ == "__main__":
    main() 