import json
import os

def format_for_training():
    base_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
    combined_file_path = os.path.join(base_path, 'training_data_combined.txt')
    final_json_output_path = os.path.join(base_path, 'final_training_dataset.json')

    all_training_examples = []

    try:
        with open(combined_file_path, 'r', encoding='utf-8') as f:
            full_content = f.read()
    except FileNotFoundError:
        print(f"Error: Combined file not found at {combined_file_path}")
        return
    except Exception as e:
        print(f"Error reading combined file: {e}")
        return

    # Entries are separated by three newlines \n\n\n (resulting in two blank lines)
    day_entries = full_content.strip().split('\n\n\n')

    for entry_str in day_entries:
        if not entry_str.strip():
            continue

        # Remove the Date line first
        lines = entry_str.split('\n', 1)
        if not lines[0].startswith("Date: "):
            print(f"Warning: Entry does not start with 'Date: '. Skipping: {lines[0][:50]}...")
            continue
        
        content_after_date = lines[1] if len(lines) > 1 else ""

        # Now content_after_date should be: "Input:\nUSER_CONTENT\n\nOutput:\nASSISTANT_CONTENT"
        parts = content_after_date.split("\n\nOutput:\n", 1)
        
        if len(parts) != 2:
            print(f"Warning: Could not split entry into Input/Output. Entry content (after date): {content_after_date[:100]}...")
            continue

        input_section = parts[0]
        assistant_content = parts[1].strip() # Assistant content is everything after the separator

        if not input_section.startswith("Input:\n"):
            print(f"Warning: Input section does not start with 'Input:\n'. Section: {input_section[:50]}...")
            continue
            
        user_content = input_section.replace("Input:\n", "", 1).strip()

        # Ensure no accidental leading/trailing newlines from the blocks themselves
        user_content = user_content.strip()
        assistant_content = assistant_content.strip()

        # Prepend the date line back to the user_content for split_training_data.py to parse
        date_str_for_content = lines[0].strip() # This is the "Date: YYYY-MM-DD" line

        training_example = {
            "messages": [
                {
                    "role": "user",
                    "content": f"{date_str_for_content}\n{user_content}" # Date prepended here
                },
                {
                    "role": "assistant",
                    "content": assistant_content
                }
            ]
        }
        all_training_examples.append(training_example)

    if not all_training_examples:
        print("No training examples were generated. Please check the input file and script logic.")
        return

    try:
        with open(final_json_output_path, 'w', encoding='utf-8') as f_json:
            json.dump(all_training_examples, f_json, indent=2) # indent=2 for pretty printing
        print(f"Successfully converted {len(all_training_examples)} entries to JSON format.")
        print(f"Final training dataset saved to: {final_json_output_path}")
    except Exception as e:
        print(f"Error writing final JSON file: {e}")

if __name__ == '__main__':
    format_for_training() 