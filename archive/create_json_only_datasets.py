import json
import os

def transform_to_json_only(source_path, target_path):
    """Reads a training data file, removes think tags from assistant responses, and saves to target_path."""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            original_examples = json.load(f)
    except FileNotFoundError:
        print(f"Error: Source file not found at {source_path}")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {source_path}")
        return False
    except Exception as e:
        print(f"Error reading source file {source_path}: {e}")
        return False

    if not original_examples:
        print(f"Source file {source_path} is empty or contains no examples.")
        # Create an empty JSON array file for consistency if target doesn't exist or is also empty
        try:
            with open(target_path, 'w', encoding='utf-8') as f_out:
                json.dump([], f_out, indent=2)
            print(f"Created empty JSON-only file: {target_path}")
        except Exception as e:
            print(f"Error creating empty file {target_path}: {e}")
        return True # Or False depending on desired behavior for empty source

    modified_examples = []
    think_tag_end = "</think>"
    processed_count = 0

    for i, example in enumerate(original_examples):
        try:
            if not (isinstance(example, dict) and 
                    "messages" in example and 
                    isinstance(example["messages"], list) and 
                    len(example["messages"]) == 2):
                print(f"Warning: Example {i} has unexpected structure. Skipping. Example: {str(example)[:100]}...")
                modified_examples.append(example) # Keep as is or skip
                continue

            assistant_message = example["messages"][1]
            if not (isinstance(assistant_message, dict) and "role" in assistant_message and 
                    assistant_message["role"] == "assistant" and "content" in assistant_message):
                print(f"Warning: Assistant message in example {i} has unexpected structure. Skipping. Example: {str(example)[:100]}...")
                modified_examples.append(example) # Keep as is or skip
                continue
            
            original_content = assistant_message["content"]
            
            think_end_index = original_content.find(think_tag_end)
            
            if think_end_index != -1:
                # Extract content after </think>
                json_only_content = original_content[think_end_index + len(think_tag_end):]
                # Remove leading/trailing whitespace (includes newlines)
                json_only_content = json_only_content.strip()
                
                # Basic validation: should start with { and end with }
                if json_only_content.startswith("{") and json_only_content.endswith("}"):
                    assistant_message["content"] = json_only_content
                    processed_count += 1
                else:
                    print(f"Warning: Content after </think> in example {i} does not look like JSON. Original content kept. Post-think content: '{json_only_content[:100]}...'")
            else:
                print(f"Warning: '</think>' tag not found in assistant message for example {i}. Original content kept.")
            
            modified_examples.append(example)

        except Exception as e:
            print(f"Error processing example {i}: {e}. Original example kept. Example: {str(example)[:100]}...")
            if example not in modified_examples: # Ensure it's added if error occurs mid-processing
                 modified_examples.append(example)

    try:
        with open(target_path, 'w', encoding='utf-8') as f_out:
            json.dump(modified_examples, f_out, indent=2)
        print(f"Successfully processed {len(original_examples)} examples. {processed_count} assistant responses modified.")
        print(f"JSON-only dataset saved to: {target_path}")
        return True
    except Exception as e:
        print(f"Error saving modified file to {target_path}: {e}")
        return False

def create_json_only_versions():
    base_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
    
    sets_to_transform = {
        "training_set.json": "training_set_json_only.json",
        "validation_set.json": "validation_set_json_only.json"
    }

    for source_name, target_name in sets_to_transform.items():
        source_file_path = os.path.join(base_path, source_name)
        target_file_path = os.path.join(base_path, target_name)
        print(f"\nProcessing {source_file_path} -> {target_file_path}...")
        transform_to_json_only(source_file_path, target_file_path)

if __name__ == '__main__':
    create_json_only_versions() 