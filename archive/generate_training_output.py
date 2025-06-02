import pandas as pd
import json

def generate_training_outputs():
    file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/model_data_prep.xlsx'
    all_output_strings = []

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return None

    required_cols = [
        'date', 'hour', 'RANK eur/ppfd', 'daily_total_ppfd_requirement',
        'max_ppfd_to_addumol_m2_s', 'ppfd_allocated',
        'remaining_ppfd_after_hour', 'cumulative_ppfd_allocated'
    ]
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found. Available: {df.columns.tolist()}")
            return None

    # Ensure data types
    try:
        df['hour'] = df['hour'].astype(int)
        df['RANK eur/ppfd'] = df['RANK eur/ppfd'].astype(int)
        for col_numeric in ['daily_total_ppfd_requirement', 'max_ppfd_to_addumol_m2_s',
                            'ppfd_allocated', 'remaining_ppfd_after_hour', 'cumulative_ppfd_allocated']:
            df[col_numeric] = pd.to_numeric(df[col_numeric])
    except Exception as e:
        print(f"Error converting column data types: {e}")
        return None

    grouped_by_day = df.groupby('date')

    for date_val, group in grouped_by_day:
        if len(group) != 24:
            print(f"Warning: Date {date_val} does not have 24 records. Skipping.")
            continue
        
        # Ensure hours 0-23 are present for safety, especially for JSON part
        group_for_json_check = group.sort_values(by='hour')
        if not all(group_for_json_check['hour'] == range(24)):
            print(f"Warning: Date {date_val} has missing or duplicate hours. Skipping this day.")
            continue

        # --- Construct <think> block --- 
        think_block_lines = ["<think>"]
        think_block_lines.append("I need to minimize electricity cost using a greedy algorithm.")

        # Step 1: Sort hours by rank
        think_block_lines.append("\nStep 1: Sort hours by electricity cost (rank 1 = cheapest):")
        rank_sorted_group = group.sort_values(by=['RANK eur/ppfd', 'hour'])
        for _, row in rank_sorted_group.iterrows():
            think_block_lines.append(f"  - hour_{int(row['hour'])}: rank {int(row['RANK eur/ppfd'])}")
        
        # Step 2: Allocate PPFD
        think_block_lines.append("\nStep 2: Allocate PPFD starting with cheapest hours:")
        daily_req_val = group['daily_total_ppfd_requirement'].iloc[0]
        think_block_lines.append(f"Total PPFD needed: {daily_req_val:.3f}\n")
        
        target_message_printed = False
        for _, row in rank_sorted_group.iterrows():
            hour_val = int(row['hour'])
            rank_val = int(row['RANK eur/ppfd'])
            alloc_val = row['ppfd_allocated']
            capacity_val = row['max_ppfd_to_addumol_m2_s']
            remain_val = row['remaining_ppfd_after_hour']
            
            alloc_desc = ""
            if alloc_val > 1e-6: # If allocated something (avoiding very small float residuals)
                if abs(alloc_val - capacity_val) < 1e-6:
                    alloc_desc = " (full capacity)"
            
            think_block_lines.append(f"  - hour_{hour_val} (rank {rank_val}): Allocate {alloc_val:.3f}{alloc_desc}, Remaining: {remain_val:.3f}")
            
            if abs(remain_val) < 1e-6 and not target_message_printed:
                # Check if this is the point target is met or if subsequent allocs are zero
                # More accurately, if the *next* item to process (if any) will get zero because target is met
                # Or if this current one made remaining zero.
                think_block_lines.append("Target reached! Remaining hours get 0 allocation.")
                target_message_printed = True # Print only once
        
        # If target message was not printed (e.g. all 24h used up to meet target exactly)
        # but remaining is indeed 0, ensure it's noted.
        if not target_message_printed and abs(rank_sorted_group['remaining_ppfd_after_hour'].iloc[-1]) < 1e-6 :
            # This case is tricky, the message fits best if there are hours that *will* get 0.
            # If the last ranked hour itself makes it zero, the message is still valid for any conceptual subsequent steps.
            think_block_lines.append("Target reached! Remaining hours get 0 allocation.")
            target_message_printed = True

        # Step 3: Summary
        think_block_lines.append("\nStep 3: Summary")
        total_allocated_val = rank_sorted_group['cumulative_ppfd_allocated'].iloc[-1] # Last value in sorted group is max
        active_hours_count = group[group['ppfd_allocated'] > 1e-6].shape[0]
        think_block_lines.append(f"  - Total allocated: {total_allocated_val:.3f}")
        think_block_lines.append(f"  - Active hours: {active_hours_count}/24")
        think_block_lines.append("</think>")
        
        think_block_string = "\n".join(think_block_lines)

        # --- Construct JSON block --- 
        hour_sorted_group = group.sort_values(by='hour')
        allocation_json_dict = {"allocation_PPFD_per_hour": {}}
        for _, row in hour_sorted_group.iterrows():
            allocation_json_dict["allocation_PPFD_per_hour"][f"hour_{int(row['hour'])}"] = round(row['ppfd_allocated'], 3)
        
        json_block_string = json.dumps(allocation_json_dict, indent=2)
        
        # Combine
        date_str = str(date_val)
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime('%Y-%m-%d')

        full_output_string = f"Date: {date_str}\n" + think_block_string + "\n\n" + json_block_string
        all_output_strings.append(full_output_string)

    return all_output_strings

if __name__ == '__main__':
    training_outputs = generate_training_outputs()
    if training_outputs:
        print(f"Successfully generated {len(training_outputs)} training output strings.")
        output_file_name = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/training_outputs.txt'
        try:
            with open(output_file_name, 'w') as f:
                for i, item in enumerate(training_outputs):
                    f.write(item)
                    if i < len(training_outputs) - 1: # Avoid extra newlines at the very end
                        f.write("\n\n\n") # Two newlines between entries means 3 newlines total
            print(f"Successfully saved training outputs to: {output_file_name}")
        except Exception as e:
            print(f"Error saving training outputs to file: {e}")

        print("\n--- Sample Training Output (First 1 displayed) ---")
        if training_outputs:
            print(training_outputs[0])
    else:
        print("Failed to generate training outputs.") 