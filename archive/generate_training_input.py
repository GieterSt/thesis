import pandas as pd
import json

def generate_nl_input():
    file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/model_data_prep.xlsx'
    output_training_data = []

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return None

    required_cols = ['date', 'daily_total_ppfd_requirement', 'hour', 
                     'RANK eur/ppfd', 'max_ppfd_to_addumol_m2_s']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found in the file.")
            print(f"Available columns: {df.columns.tolist()}")
            return None

    # Ensure correct data types
    try:
        df['hour'] = df['hour'].astype(int)
        df['RANK eur/ppfd'] = df['RANK eur/ppfd'].astype(int) # Assuming ranks are whole numbers after cleaning
        df['daily_total_ppfd_requirement'] = pd.to_numeric(df['daily_total_ppfd_requirement'])
        df['max_ppfd_to_addumol_m2_s'] = pd.to_numeric(df['max_ppfd_to_addumol_m2_s'])
    except Exception as e:
        print(f"Error converting column data types: {e}")
        return None

    grouped_by_day = df.groupby('date')

    for date_val, group in grouped_by_day:
        if len(group) != 24:
            print(f"Warning: Date {date_val} does not have exactly 24 hourly records (found {len(group)}). Skipping this day.")
            continue

        # Ensure hours 0-23 are present and sort by hour for consistent dictionary creation
        group = group.sort_values(by='hour')
        if not all(group['hour'] == range(24)):
            print(f"Warning: Date {date_val} has missing or duplicate hours. Skipping this day.")
            continue

        daily_requirement = group['daily_total_ppfd_requirement'].iloc[0]
        # Round to a reasonable number of decimal places if it's a float, e.g., 3
        if isinstance(daily_requirement, float):
            daily_requirement = round(daily_requirement, 3) 

        rankings_dict = {}
        capacity_dict = {}

        for _, row in group.iterrows():
            hour_key = f"hour_{int(row['hour'])}"
            rankings_dict[hour_key] = int(row['RANK eur/ppfd'])
            # Round capacity to a reasonable number of decimal places if it's a float, e.g., 4
            capacity = row['max_ppfd_to_addumol_m2_s']
            if isinstance(capacity, float):
                 capacity_dict[hour_key] = round(capacity, 4)
            else:
                 capacity_dict[hour_key] = capacity

        # Use json.dumps for proper dictionary string formatting, then remove surrounding quotes if any.
        # The template expects the dict format directly, not as a string representation of a dict.
        rankings_str = json.dumps(rankings_dict)
        capacity_str = json.dumps(capacity_dict)

        # Convert date_val to string if it's a pandas Timestamp or datetime object
        date_str = str(date_val)
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime('%Y-%m-%d')

        input_template = f"""Date: {date_str}
Optimize LED lighting schedule:
- Daily total PPFD requirement: {daily_requirement}
- EUR/PPFD rankings by hour: {rankings_str}
- Max PPFD capacity by hour: {capacity_str}
Allocate PPFD per hour to minimize cost."""
        output_training_data.append(input_template)

    return output_training_data

if __name__ == '__main__':
    training_inputs = generate_nl_input()
    if training_inputs:
        print(f"Successfully generated {len(training_inputs)} training input strings.")
        
        output_file_name = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/training_inputs.txt'
        try:
            with open(output_file_name, 'w') as f:
                for item in training_inputs:
                    f.write(item + "\n\n") # Add an extra newline for separation between entries
            print(f"Successfully saved training inputs to: {output_file_name}")
        except Exception as e:
            print(f"Error saving training inputs to file: {e}")

        print("\n--- Sample Training Inputs (First 2 displayed here) ---")
        for i, item in enumerate(training_inputs[:2]):
            print(f"\n--- Item {i+1} ---")
            print(item)
    else:
        print("Failed to generate training inputs.") 