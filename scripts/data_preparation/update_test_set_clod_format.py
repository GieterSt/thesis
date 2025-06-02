import json
import re
import os

BASE_PATH = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
FILE_TO_MODIFY = os.path.join(BASE_PATH, 'test_set_clod.json')

NEW_PROMPT_TEMPLATE = """I need you to create an optimal LED lighting schedule for a greenhouse growing lettuce.

Goal:
Create the most cost-efficient LED lighting schedule that allocates exactly {TOTAL_PPFD_REQUIREMENT} PPFD-hours across a 24-hour period while respecting all capacity constraints.

Return Format:
Return a JSON object with the key "allocation_PPFD_per_hour" containing a nested object with 24 hour keys (hour_0 through hour_23) and their corresponding PPFD allocation values. The values should be precise to 3 decimal places when needed. Your solution must allocate exactly the total required PPFD.

Warnings:
- Never allocate more than the maximum capacity for any hour
- Do not allocate any PPFD to hours with 0 capacity
- Ensure your total allocation equals exactly {TOTAL_PPFD_REQUIREMENT} PPFD-hours
- Use a greedy algorithm prioritizing hours with the lowest EUR/PPFD ranking first

Context Dump:
Date: {DATE}
Daily total PPFD requirement: {TOTAL_PPFD_REQUIREMENT}
EUR/PPFD rankings by hour (1=cheapest): {EUR_PPFD_RANKINGS_JSON}
Max PPFD capacity by hour: {MAX_CAPACITY_JSON}

This is a critical optimization task for greenhouse energy management. The optimal solution should follow a greedy approach, allocating PPFD to the cheapest hours first until the daily requirement is met.
"""

def parse_existing_user_content(user_content_str):
    lines = user_content_str.split('\n')
    
    date_str = "UnknownDate"
    if lines and lines[0].startswith("Date: "):
        date_str = lines[0].replace("Date: ", "").strip()

    total_ppfd_requirement = None
    eur_ppfd_rankings_json_str = None
    max_capacity_json_str = None

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("- Daily total PPFD requirement:"):
            match_total_ppfd = re.search(r"Daily total PPFD requirement:\s*([\d\.]+)", stripped_line)
            if match_total_ppfd:
                total_ppfd_requirement = float(match_total_ppfd.group(1))
        elif stripped_line.startswith("- EUR/PPFD rankings by hour:"):
            eur_ppfd_rankings_json_str = stripped_line.replace("- EUR/PPFD rankings by hour:", "").strip()
        elif stripped_line.startswith("- Max PPFD capacity by hour:"):
            max_capacity_json_str = stripped_line.replace("- Max PPFD capacity by hour:", "").strip()

    if total_ppfd_requirement is None:
        raise ValueError(f"Could not parse TOTAL_PPFD_REQUIREMENT. Content: {user_content_str[:300]}")
    if eur_ppfd_rankings_json_str is None:
        raise ValueError(f"Could not parse EUR_PPFD_RANKINGS_JSON. Content: {user_content_str[:300]}")
    if max_capacity_json_str is None:
        raise ValueError(f"Could not parse MAX_CAPACITY_JSON. Content: {user_content_str[:300]}")

    try:
        # The strings are already JSON, so just load them.
        # Need to unescape the internal quotes if they exist from previous formatting
        eur_ppfd_rankings = json.loads(eur_ppfd_rankings_json_str.replace('\\"', '"'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding EUR_PPFD_RANKINGS_JSON: {e}. String was: {eur_ppfd_rankings_json_str}")
    
    try:
        max_capacity = json.loads(max_capacity_json_str.replace('\\"', '"'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding MAX_CAPACITY_JSON: {e}. String was: {max_capacity_json_str}")

    # Validation and ensuring all hour_X keys are present can still be useful
    # (though data from JSON string should already be in hour_X format)
    final_ranks = {}
    final_capacity = {}
    for h in range(24):
        hour_key_orig_rank = str(h) # Original keys in parsed JSON might be "0", "1" etc.
        hour_key_orig_cap = str(h)
        hour_key_target = f"hour_{h}"

        # Check if the key is already in "hour_X" format or just "X"
        if hour_key_target in eur_ppfd_rankings:
            final_ranks[hour_key_target] = eur_ppfd_rankings[hour_key_target]
        elif hour_key_orig_rank in eur_ppfd_rankings:
            final_ranks[hour_key_target] = eur_ppfd_rankings[hour_key_orig_rank]
        else:
            print(f"Warning: Date {date_str} - Rank for {hour_key_target} (or {hour_key_orig_rank}) missing. Setting to 999.")
            final_ranks[hour_key_target] = 999

        if hour_key_target in max_capacity:
            final_capacity[hour_key_target] = max_capacity[hour_key_target]
        elif hour_key_orig_cap in max_capacity:
            final_capacity[hour_key_target] = max_capacity[hour_key_orig_cap]
        else:
            print(f"Warning: Date {date_str} - Capacity for {hour_key_target} (or {hour_key_orig_cap}) missing. Setting to 0.0.")
            final_capacity[hour_key_target] = 0.0
            
    return date_str, total_ppfd_requirement, final_ranks, final_capacity

def transform_existing_assistant_content(assistant_content_str):
    try:
        json_payload_str = assistant_content_str
        think_tag_end = "</think>"
        if think_tag_end in assistant_content_str:
            parts = assistant_content_str.split(think_tag_end, 1)
            if len(parts) > 1:
                json_payload_str = parts[1].strip()
            else: # Only think tag, no JSON
                json_payload_str = "{}" 
        
        # Ensure we are parsing a valid JSON object string by finding the first '{'
        first_brace_index = json_payload_str.find('{')
        if first_brace_index == -1: # No JSON object found
             print(f"Warning: No JSON object found in assistant content after attempting to remove <think> block. Content snippet: {json_payload_str[:100]}")
             original_data = {"ppfd_allocated": {}} # Default to empty structure
        else:
            json_payload_str = json_payload_str[first_brace_index:]
            original_data = json.loads(json_payload_str)
        
        new_data_format = {"allocation_PPFD_per_hour": {}}
        
        allocations = original_data.get("ppfd_allocated", {})
        for hour_str_key, ppfd_value in allocations.items():
            try:
                # Standardize to hour_X format
                hour_int = int(hour_str_key) # Assuming keys are "0", "1", etc.
                new_data_format["allocation_PPFD_per_hour"][f"hour_{hour_int}"] = ppfd_value
            except ValueError:
                 # If key is already "hour_X" or some other format, try to keep it or log
                print(f"Warning: Could not parse hour key '{hour_str_key}' as int. Using as is or transformed if possible.")
                if hour_str_key.startswith("hour_"):
                    new_data_format["allocation_PPFD_per_hour"][hour_str_key] = ppfd_value
                else: # Attempt to make it hour_X if it's just a number as string
                    new_data_format["allocation_PPFD_per_hour"][f"hour_{hour_str_key}"] = ppfd_value


        return json.dumps(new_data_format, indent=2)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError in assistant content: {e}. Content snippet: {assistant_content_str[:200]}")
        # Return a valid empty JSON structure for the output if parsing fails
        return json.dumps({"allocation_PPFD_per_hour": {f"hour_{h}": 0 for h in range(24)}}, indent=2)
    except Exception as e:
        print(f"Generic error transforming assistant content: {e}. Content snippet: {assistant_content_str[:200]}")
        # Fallback to empty valid structure
        return json.dumps({"allocation_PPFD_per_hour": {f"hour_{h}": 0 for h in range(24)}}, indent=2)

def main():
    try:
        with open(FILE_TO_MODIFY, 'r', encoding='utf-8') as f:
            all_examples = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {FILE_TO_MODIFY}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {FILE_TO_MODIFY}. Error: {e}")
        return

    modified_examples_count = 0
    processed_examples = []

    for i, example in enumerate(all_examples):
        original_example_copy = json.loads(json.dumps(example)) # Deep copy for fallback
        try:
            print(f"Processing example {i+1}/{len(all_examples)}...")
            user_content_old = example["messages"][0]["content"]
            assistant_content_old = example["messages"][1]["content"]

            date, total_ppfd, ranks_dict, capacity_dict = parse_existing_user_content(user_content_old)
            
            ranks_json_str = json.dumps(ranks_dict) # ranks_dict keys are already "hour_X"
            capacity_json_str = json.dumps(capacity_dict) # capacity_dict keys are "hour_X"

            new_user_prompt = NEW_PROMPT_TEMPLATE.format(
                TOTAL_PPFD_REQUIREMENT=total_ppfd,
                DATE=date,
                EUR_PPFD_RANKINGS_JSON=ranks_json_str,
                MAX_CAPACITY_JSON=capacity_json_str
            )
            
            example["messages"][0]["content"] = new_user_prompt
            
            new_assistant_response_json_str = transform_existing_assistant_content(assistant_content_old)
            example["messages"][1]["content"] = new_assistant_response_json_str
            
            processed_examples.append(example)
            modified_examples_count +=1

        except Exception as e:
            print(f"Error processing example {i} (Original Date line: {original_example_copy.get('messages', [{}])[0].get('content', '').splitlines()[0 if original_example_copy.get('messages', [{}])[0].get('content', '') else -1]}): {type(e).__name__} - {e}")
            print("Adding original example due to error.")
            processed_examples.append(original_example_copy) # Add original back

    if not all_examples:
        print("No examples found in the input file.")
        return

    try:
        with open(FILE_TO_MODIFY, 'w', encoding='utf-8') as f:
            json.dump(processed_examples, f, indent=2)
        print(f"Successfully processed {len(processed_examples)} examples.")
        print(f"{modified_examples_count} examples were modified and saved to {FILE_TO_MODIFY}.")
        if len(processed_examples) - modified_examples_count > 0:
            print(f"{len(processed_examples) - modified_examples_count} examples were kept original due to errors.")
    except Exception as e:
        print(f"Error writing updated data to {FILE_TO_MODIFY}: {e}")

if __name__ == '__main__':
    main() 