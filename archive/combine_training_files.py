import os

def parse_training_file(file_content, entry_separator):
    data_map = {}
    # Normalize line endings and then split
    entries = file_content.replace('\r\n', '\n').split(entry_separator)
    for entry in entries:
        entry = entry.strip() # Remove leading/trailing whitespace including newlines from the block itself
        if not entry: # Skip if entry is empty after stripping
            continue
        lines = entry.split('\n', 1)
        if not lines:
            continue
        date_line = lines[0]
        if date_line.startswith("Date: "):
            date_str = date_line.replace("Date: ", "").strip()
            content = lines[1] if len(lines) > 1 else ""
            data_map[date_str] = content.strip() # Strip content too
    return data_map

def combine_training_files():
    base_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
    input_file_path = os.path.join(base_path, 'training_inputs.txt')
    output_file_path = os.path.join(base_path, 'training_outputs.txt')
    combined_file_path = os.path.join(base_path, 'training_data_combined.txt')

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            input_content_full = f.read()
        with open(output_file_path, 'r', encoding='utf-8') as f:
            output_content_full = f.read()
    except FileNotFoundError as e:
        print(f"Error: One or both input files not found: {e}")
        return
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    # Input entries are separated by \n\n; each item was `content + \n\n`
    # Output entries are separated by \n\n\n; each item was `content + \n\n\n`
    input_data_map = parse_training_file(input_content_full, '\n\n')
    output_data_map = parse_training_file(output_content_full, '\n\n\n')

    if not input_data_map:
        print(f"No data parsed from {input_file_path}. Check file content and separator.")
        return
    if not output_data_map:
        print(f"No data parsed from {output_file_path}. Check file content and separator.")
        return

    common_dates = sorted(list(set(input_data_map.keys()) & set(output_data_map.keys())))

    if not common_dates:
        print("No common dates found between input and output files. Combined file will be empty.")
        # Still create an empty file or just return might be better.
        # For now, let's write an empty file if it reaches here.

    successful_writes = 0
    with open(combined_file_path, 'w', encoding='utf-8') as f_combined:
        for i, date_str in enumerate(common_dates):
            input_block = input_data_map.get(date_str)
            output_block = output_data_map.get(date_str)

            if input_block is None or output_block is None: # Should not happen due to common_dates logic
                print(f"Warning: Missing data for date {date_str}. Skipping.")
                continue

            f_combined.write(f"Date: {date_str}\n")
            f_combined.write("Input:\n")
            f_combined.write(input_block)
            f_combined.write("\n\n") # Separator between input and output sections
            f_combined.write("Output:\n")
            f_combined.write(output_block)
            
            if i < len(common_dates) - 1: # Add separator for next full entry, but not for the last one
                 f_combined.write("\n\n\n") # Separator between combined entries (2 blank lines)
            successful_writes +=1
            
    print(f"Successfully combined {successful_writes} entries into: {combined_file_path}")
    if len(common_dates) != len(input_data_map) or len(common_dates) != len(output_data_map):
        print("Warning: Some entries from input or output files were not matched by date.")
        print(f"Input file entries: {len(input_data_map)}, Output file entries: {len(output_data_map)}, Matched entries: {len(common_dates)}")

if __name__ == '__main__':
    combine_training_files() 