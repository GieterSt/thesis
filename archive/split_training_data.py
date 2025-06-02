import json
import os
import random
import datetime
import math

def get_season(date_obj):
    """Determines the season for a given datetime.date object."""
    month = date_obj.month
    day = date_obj.day

    # Using (month, day) tuples for comparison
    # Spring: March 20 - June 20
    if (month == 3 and day >= 20) or (month == 4) or (month == 5) or (month == 6 and day <= 20):
        return "Spring"
    # Summer: June 21 - September 22
    elif (month == 6 and day >= 21) or (month == 7) or (month == 8) or (month == 9 and day <= 22):
        return "Summer"
    # Fall: September 23 - December 20
    elif (month == 9 and day >= 23) or (month == 10) or (month == 11) or (month == 12 and day <= 20):
        return "Fall"
    # Winter: December 21 - March 19
    else: # Covers Dec 21-31, Jan, Feb, Mar 1-19
        return "Winter"

def split_training_data():
    base_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
    source_json_path = os.path.join(base_path, 'final_training_dataset.json')
    
    train_output_path = os.path.join(base_path, 'training_set.json')
    val_output_path = os.path.join(base_path, 'validation_set.json')
    test_output_path = os.path.join(base_path, 'test_set.json')

    try:
        with open(source_json_path, 'r', encoding='utf-8') as f:
            all_examples = json.load(f)
    except FileNotFoundError:
        print(f"Error: Source JSON file not found at {source_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {source_json_path}")
        return
    except Exception as e:
        print(f"Error reading source file: {e}")
        return

    if not all_examples:
        print("Source JSON file is empty. No data to split.")
        return

    print(f"Loaded {len(all_examples)} examples from {source_json_path}")

    # Step 1 & 2: Extract Date and Assign Season
    examples_with_season = []
    for example in all_examples:
        try:
            user_content = example["messages"][0]["content"]
            date_line = user_content.split('\n', 1)[0]
            date_str = date_line.replace("Date: ", "").strip()
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            season = get_season(date_obj)
            examples_with_season.append({"data": example, "season": season, "date_str": date_str})
        except (IndexError, ValueError, KeyError) as e:
            print(f"Warning: Could not parse date or structure invalid for an example: {str(e)}. Example: {str(example)[:100]}... Skipping.")
            continue
    
    # Step 3: Group by Season
    seasonal_data = {"Winter": [], "Spring": [], "Summer": [], "Fall": []}
    for item in examples_with_season:
        seasonal_data[item["season"]].append(item["data"]) # Store original example data

    print("\n--- Initial counts per season ---")
    for season, data_list in seasonal_data.items():
        print(f"- {season}: {len(data_list)} examples")

    # Step 4: Handle Unequal Seasons (Equalize counts)
    min_count_per_season = float('inf')
    if any(seasonal_data.values()): # Check if there is any data at all
        min_count_per_season = min(len(data_list) for data_list in seasonal_data.values() if data_list) 
        # If some seasons are empty, min_count_per_season could be 0 if not careful
        # Let's ensure min_count is only from non-empty seasons, or 0 if all are empty (covered by initial check)
        non_empty_counts = [len(data_list) for data_list in seasonal_data.values() if data_list]
        if non_empty_counts:
            min_count_per_season = min(non_empty_counts)
        else:
            min_count_per_season = 0 # All seasons empty
            
    if min_count_per_season == 0 and any(non_empty_counts):
        print("Warning: At least one season has 0 examples, but others have data. Cannot proceed with balanced split based on 0.")
        # Decide how to handle: maybe skip equalization or error out. For now, let it proceed but counts will be 0 for splits.
    elif min_count_per_season > 0:
      print(f"\nEqualizing season counts to the minimum: {min_count_per_season} examples per season.")
      for season in seasonal_data:
          if len(seasonal_data[season]) > min_count_per_season:
              print(f"Sampling {min_count_per_season} from {season} (had {len(seasonal_data[season])})")
              random.shuffle(seasonal_data[season])
              seasonal_data[season] = seasonal_data[season][:min_count_per_season]
    else:
        print("No data in any season after grouping. Cannot proceed.")
        return

    print("\n--- Counts per season after equalization ---")
    total_equalized_examples = 0
    for season, data_list in seasonal_data.items():
        print(f"- {season}: {len(data_list)} examples")
        total_equalized_examples += len(data_list)
    print(f"Total examples after equalization: {total_equalized_examples}")

    if total_equalized_examples == 0:
        print("No examples left after equalization. Cannot create splits.")
        return

    # Step 5 & 6: Shuffle Within Each Season and Split
    train_set_parts, val_set_parts, test_set_parts = [], [], []

    print("\n--- Splitting each season (60/20/20) ---")
    for season, data_list in seasonal_data.items():
        if not data_list: # Should not happen if min_count_per_season > 0
            print(f"Skipping {season} as it has no data after equalization.")
            continue
        
        random.shuffle(data_list) # Step 5
        n = len(data_list)
        
        idx_train_end = math.floor(n * 0.6)
        idx_val_end = math.floor(n * 0.8) # 0.6 + 0.2

        train_items = data_list[0:idx_train_end]
        val_items = data_list[idx_train_end:idx_val_end]
        test_items = data_list[idx_val_end:n]
        
        train_set_parts.extend(train_items)
        val_set_parts.extend(val_items)
        test_set_parts.extend(test_items)
        print(f"- {season}: Train={len(train_items)}, Val={len(val_items)}, Test={len(test_items)}")

    # Step 7: Combine the Splits (already done by extend)
    # Step 8: Final Shuffle
    random.shuffle(train_set_parts)
    random.shuffle(val_set_parts)
    random.shuffle(test_set_parts)

    print("\n--- Final dataset sizes ---")
    print(f"- Training set: {len(train_set_parts)} examples")
    print(f"- Validation set: {len(val_set_parts)} examples")
    print(f"- Test set: {len(test_set_parts)} examples")

    # Step 9: Save the Datasets
    datasets_to_save = {
        train_output_path: train_set_parts,
        val_output_path: val_set_parts,
        test_output_path: test_set_parts
    }

    for path, data in datasets_to_save.items():
        try:
            with open(path, 'w', encoding='utf-8') as f_out:
                json.dump(data, f_out, indent=2)
            print(f"Successfully saved to: {path}")
        except Exception as e:
            print(f"Error saving file {path}: {e}")

if __name__ == '__main__':
    split_training_data() 