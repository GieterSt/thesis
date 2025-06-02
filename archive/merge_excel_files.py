import pandas as pd

def merge_excel_files():
    # Define file paths
    source_file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/SSRD_data_2024-2025 copy.xlsx'
    target_file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/Template_with_Electricity_Data.xlsx'
    output_file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/Merged_Template_with_SSRD_Data.xlsx'

    # Read the source Excel file
    try:
        df_source = pd.read_excel(source_file_path)
    except FileNotFoundError:
        print(f"Error: Source file not found at {source_file_path}")
        return
    except Exception as e:
        print(f"Error reading source file: {e}")
        return

    # Read the target Excel file
    try:
        df_target = pd.read_excel(target_file_path)
    except FileNotFoundError:
        print(f"Error: Target file not found at {target_file_path}")
        return
    except Exception as e:
        print(f"Error reading target file: {e}")
        return

    # Columns to merge from the source file
    columns_to_merge = [
        'date_str', 
        'hour', 
        'total_supplemental_ppfd_requirement_umol_m2_s_h', 
        'max_ppfd_to_addumol_m2_s'
    ]

    # Check if all required columns exist in the source DataFrame
    missing_cols_source = [col for col in columns_to_merge if col not in df_source.columns]
    if missing_cols_source:
        print(f"Error: The following required columns are missing from the source file ({source_file_path}): {', '.join(missing_cols_source)}")
        # Print available columns for debugging
        print(f"Available columns in source file: {', '.join(df_source.columns)}")
        return
        
    df_source_selected = df_source[columns_to_merge].copy()

    # Rename 'date_str' to 'date' in the source selection for merging
    df_source_selected.rename(columns={'date_str': 'date'}, inplace=True)

    # Ensure 'date' and 'hour' columns in df_target exist
    if 'date' not in df_target.columns:
        print(f"Error: 'date' column missing in target file ({target_file_path}).")
        print(f"Available columns in target file: {', '.join(df_target.columns)}")
        return
    if 'hour' not in df_target.columns:
        print(f"Error: 'hour' column missing in target file ({target_file_path}).")
        print(f"Available columns in target file: {', '.join(df_target.columns)}")
        return
        
    # Convert merge key columns to a consistent type if necessary (e.g., string for date, int for hour)
    # This helps prevent merge issues due to data type mismatches.
    # Assuming 'date' in target and 'date_str' (now 'date') in source can be treated as objects/strings for merging.
    # If 'date' in target is datetime, ensure 'date' from source is also datetime or formatted as a string that matches.
    # For simplicity here, we'll assume direct matching is possible or pandas handles it.
    # It's good practice to explicitly convert:
    # df_target['date'] = pd.to_datetime(df_target['date']).dt.date.astype(str) # Example: if target date needs formatting
    # df_source_selected['date'] = pd.to_datetime(df_source_selected['date']).dt.date.astype(str) # Example

    # Drop duplicates from the source selection based on 'date' and 'hour', keeping the first occurrence
    df_source_selected.drop_duplicates(subset=['date', 'hour'], keep='first', inplace=True)

    # Perform the merge
    # Using a left merge to keep all rows from the target and add matching columns from the source
    df_merged = pd.merge(df_target, df_source_selected, on=['date', 'hour'], how='left')

    # Save the merged DataFrame to a new Excel file
    try:
        df_merged.to_excel(output_file_path, index=False)
        print(f"Successfully merged files. Output saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving merged file: {e}")

if __name__ == '__main__':
    merge_excel_files() 