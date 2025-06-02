import pandas as pd

def calculate_ppfd_allocation():
    input_file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/Merged_Template_with_SSRD_Data.xlsx'
    output_file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/model_data_prep.xlsx'

    try:
        df = pd.read_excel(input_file_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # Verify necessary columns
    required_columns = ['date', 'hour', 'RANK eur/ppfd', 
                        'total_supplemental_ppfd_requirement_umol_m2_s_h', 
                        'max_ppfd_to_addumol_m2_s']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        print(f"Available columns: {df.columns.tolist()}")
        return

    # Ensure data types for key columns
    try:
        df['hour'] = pd.to_numeric(df['hour'])
        df['RANK eur/ppfd'] = pd.to_numeric(df['RANK eur/ppfd'])
        df['total_supplemental_ppfd_requirement_umol_m2_s_h'] = pd.to_numeric(df['total_supplemental_ppfd_requirement_umol_m2_s_h'])
        df['max_ppfd_to_addumol_m2_s'] = pd.to_numeric(df['max_ppfd_to_addumol_m2_s'])
    except ValueError as e:
        print(f"Error converting column types: {e}. Please check data.")
        return

    df['ppfd_allocated'] = 0.0  # Initialize the new column
    df['remaining_ppfd_after_hour'] = 0.0 # Initialize the new countdown column
    df['cumulative_ppfd_allocated'] = 0.0 # Initialize the new cumulative column

    # Group by date and process each day
    for date_val, group in df.groupby('date'):
        # Calculate total daily PPFD requirement for this day
        # If 'total_supplemental_ppfd_requirement_umol_m2_s_h' represents the daily total repeated for each hour,
        # taking the mean() will give that daily total. If it's truly an hourly requirement, .sum() would be correct.
        # Based on the feedback, .mean() (or .iloc[0] if consistency is guaranteed) is likely what's needed.
        daily_total_requirement = group['total_supplemental_ppfd_requirement_umol_m2_s_h'].fillna(0).mean()
        
        # Sort hours by rank, then by hour for tie-breaking
        sorted_group = group.sort_values(by=['RANK eur/ppfd', 'hour'])
        
        remaining_needed = daily_total_requirement
        current_cumulative_for_day = 0.0 # Initialize cumulative for the current day
        
        for index, row in sorted_group.iterrows():
            current_capacity = row['max_ppfd_to_addumol_m2_s']
            # Handle potential NaN in capacity, treat as 0 if so
            if pd.isna(current_capacity):
                current_capacity = 0.0
                
            allocation_for_this_hour = 0.0
            
            if remaining_needed > 0:
                if remaining_needed > current_capacity:
                    allocation_for_this_hour = current_capacity
                else:
                    allocation_for_this_hour = remaining_needed
            
            df.loc[index, 'ppfd_allocated'] = allocation_for_this_hour
            remaining_needed -= allocation_for_this_hour
            # Ensure remaining_needed doesn't go significantly negative due to float precision
            if remaining_needed < 1e-9: # A small threshold for zero
                 remaining_needed = 0
            
            df.loc[index, 'remaining_ppfd_after_hour'] = remaining_needed # Store the countdown value

            current_cumulative_for_day += allocation_for_this_hour
            df.loc[index, 'cumulative_ppfd_allocated'] = current_cumulative_for_day # Store cumulative

    # Rename the ambiguous column for clarity in the output file
    df.rename(columns={'total_supplemental_ppfd_requirement_umol_m2_s_h': 'daily_total_ppfd_requirement'}, inplace=True)

    try:
        df.to_excel(output_file_path, index=False)
        print(f"Successfully calculated ppfd_allocated. Output saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")

if __name__ == '__main__':
    calculate_ppfd_allocation() 