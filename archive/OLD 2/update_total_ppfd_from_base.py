import pandas as pd

def update_column_from_base(base_file_path, target_file_path, standard_key_columns, base_actual_key_names, column_to_update):
    print(f"Processing target file: {target_file_path} using base file: {base_file_path}")

    try:
        # Read the base Excel file using actual names for key columns from base_actual_key_names
        df_base = pd.read_excel(base_file_path, sheet_name=0, usecols=base_actual_key_names + [column_to_update])
        print(f"Successfully read base file. Original base key columns used: {base_actual_key_names}. Columns read: {df_base.columns.tolist()}")
        
        # Rename base file key columns to standard names (e.g., 'datetime' -> 'date', 'date_str' -> 'hour')
        rename_map = {
            base_actual_key_names[0]: standard_key_columns[0], # e.g., 'datetime' to 'date'
            base_actual_key_names[1]: standard_key_columns[1]  # e.g., 'date_str' to 'hour'
        }
        df_base.rename(columns=rename_map, inplace=True)
        print(f"Renamed base key columns to standard names: {standard_key_columns}. Base columns now: {df_base.columns.tolist()}")

    except FileNotFoundError:
        print(f"Error: Base file {base_file_path} not found.")
        return
    except ValueError as e: 
        print(f"Error reading specified columns from base file {base_file_path} (usecols: {base_actual_key_names + [column_to_update]}): {e}")
        return
    except Exception as e:
        print(f"Error processing base file {base_file_path}: {e}")
        return

    # Standardize key columns in base DataFrame (now using standard_key_columns like ['date', 'hour'])
    try:
        date_col_name = standard_key_columns[0]
        if date_col_name in df_base.columns:
            # Clean the date string: convert to string, strip whitespace, then convert to datetime
            df_base[date_col_name] = df_base[date_col_name].astype(str).str.strip()
            df_base[date_col_name] = pd.to_datetime(df_base[date_col_name], errors='coerce')
            # Drop rows where date could not be parsed, as they cannot be merged
            df_base.dropna(subset=[date_col_name], inplace=True)
            df_base[date_col_name] = df_base[date_col_name].dt.strftime('%Y-%m-%d')
        
        hour_col_name = standard_key_columns[1]
        if len(standard_key_columns) > 1 and hour_col_name in df_base.columns:
            df_base[hour_col_name] = pd.to_numeric(df_base[hour_col_name], errors='coerce')
            # Optionally, drop rows where hour could not be parsed if it's critical for merging
            # df_base.dropna(subset=[hour_col_name], inplace=True)

    except Exception as e:
        print(f"Error standardizing key columns in base data (expected {standard_key_columns}): {e}")
        return

    is_excel = target_file_path.endswith('.xlsx')
    try:
        if is_excel:
            df_target = pd.read_excel(target_file_path, sheet_name=0)
        else:
            df_target = pd.read_csv(target_file_path)
        print(f"Successfully read target file: {target_file_path}")
    except FileNotFoundError:
        print(f"Error: Target file {target_file_path} not found.")
        return
    except Exception as e:
        print(f"Error reading target file {target_file_path}: {e}")
        return

    original_target_columns = df_target.columns.tolist()

    # Standardize key columns in target DataFrame (uses standard_key_columns like ['date', 'hour'])
    try:
        target_date_col = standard_key_columns[0]
        if target_date_col not in df_target.columns:
            print(f"Error: Standard key column '{target_date_col}' not found in target file {target_file_path}")
            return
        # Ensure target date column is also clean before attempting to_datetime
        df_target[target_date_col] = df_target[target_date_col].astype(str).str.strip()
        df_target[target_date_col] = pd.to_datetime(df_target[target_date_col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        target_hour_col = standard_key_columns[1]
        if len(standard_key_columns) > 1:
            if target_hour_col not in df_target.columns:
                print(f"Error: Standard key column '{target_hour_col}' not found in target file {target_file_path}")
                return
            df_target[target_hour_col] = pd.to_numeric(df_target[target_hour_col], errors='coerce')
    except Exception as e:
        print(f"Error standardizing key columns in target data for {target_file_path} (expected {standard_key_columns}): {e}")
        return

    # Perform the merge using standard_key_columns
    df_merged = pd.merge(df_target, df_base, on=standard_key_columns, how='left', suffixes=('', '_base'))

    base_value_col_suffixed = column_to_update + '_base'
    final_base_value_col = base_value_col_suffixed

    if base_value_col_suffixed not in df_merged.columns:
        if column_to_update in df_merged.columns and column_to_update in df_base.columns and column_to_update in df_target.columns:
            # This implies column_to_update was used directly by merge without suffix because it wasn't in target before merge, or names matched perfectly
            # However, the safer assumption for _base values is that they came from df_base.
            # If column_to_update from df_base is what we want, and it wasn't suffixed, it should exist in df_merged.
            # Let's check if the values from the _base version are present in the column_to_update (if no suffix happened)
            # This part is tricky. The suffixing handles ambiguity. If no suffix, then column_to_update should be the one from df_base if it was merged.
            # Safest is to assume that if _base isn't there, then column_to_update already contains base's values or there was no match for those rows.
            # The fillna later handles this: df_merged[column_to_update] = df_merged[base_value_col_suffixed].fillna(df_merged[column_to_update])
            # So, if base_value_col_suffixed is not found, it means the original value in column_to_update (from target) will be kept for unmatched rows by fillna.
            # And for matched rows, if column_to_update (from base) was merged without suffix, it means it overwrote or was the source.
             print(f"Warning: Column '{base_value_col_suffixed}' not found after merge. Update will rely on '{column_to_update}' possibly containing merged values or original target values.")
             final_base_value_col = column_to_update # Assume values from base are now in this column for matched rows
        # else:
            # print(f"Error: Critical column '{base_value_col_suffixed}' or suitable '{column_to_update}' (from base) not found after merge for {target_file_path}. Merge might have failed to bring in base data for this column.")
            # return # This might be too strict if some rows don't match and fillna is intended
    
    # Update the target column with values from the base column
    # If column_to_update was not in target, it's created by merge (potentially with _base values)
    # If column_to_update was in target, it's updated using values from base_value_col_suffixed, falling back to original if no match from base
    if column_to_update not in df_merged.columns and final_base_value_col in df_merged.columns:
        # This means original target didn't have column_to_update; it's purely from base
        df_merged[column_to_update] = df_merged[final_base_value_col]
    elif final_base_value_col in df_merged.columns: # final_base_value_col should always be checked
        # Ensure column_to_update exists before trying to fillna into it or assign to it.
        if column_to_update not in df_merged.columns:
             df_merged[column_to_update] = pd.Series(index=df_merged.index, dtype=object) # Create if not exists at all
        df_merged[column_to_update] = df_merged[final_base_value_col].fillna(df_merged[column_to_update])
    else:
        print(f"Warning: Neither '{column_to_update}' nor '{final_base_value_col}' were effectively found to update from. Skipping update for this column.")

    # Drop the suffixed column if it's different from the target column_to_update and exists
    if base_value_col_suffixed in df_merged.columns and base_value_col_suffixed != column_to_update:
        df_merged.drop(columns=[base_value_col_suffixed], inplace=True)
    
    # Reconstruct column order to match original target, adding new columns at the end
    final_ordered_columns = []
    existing_cols_in_merged = set(df_merged.columns)
    
    for col in original_target_columns:
        if col in existing_cols_in_merged:
            final_ordered_columns.append(col)
            if col in existing_cols_in_merged: # Check before removing, as it might have been removed if it was the updated col and not in original_target_columns
                 existing_cols_in_merged.remove(col)
    # Add the updated column if it's not already there (e.g., if it was a new column for the target)
    if column_to_update in df_merged.columns and column_to_update not in final_ordered_columns:
        final_ordered_columns.append(column_to_update)
        if column_to_update in existing_cols_in_merged:
            existing_cols_in_merged.remove(column_to_update)
            
    final_ordered_columns.extend(sorted(list(existing_cols_in_merged))) # Add any other new columns, sorted for consistency

    # Ensure all columns intended for saving are actually in df_merged
    df_to_save = df_merged[[col for col in final_ordered_columns if col in df_merged.columns]]

    try:
        if is_excel:
            df_to_save.to_excel(target_file_path, index=False)
        else:
            df_to_save.to_csv(target_file_path, index=False)
        print(f"Successfully updated '{column_to_update}' in {target_file_path} from base file.")
    except Exception as e:
        print(f"Error saving updated file {target_file_path}: {e}")

# --- Configuration ---
base_file_path = "/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/SSRD_data_2024-2025 copy.xlsx"
csv_target_path = "Complete_Merged_Dataset_2024_2025.csv"
excel_target_path = "Complete_Merged_Dataset_2024_2025.xlsx"

# Standard key column names to be used for merging (target files must have these)
standard_keys = ['date', 'hour']
# Actual key column names in the base Excel file
base_file_actual_keys = ['datetime', 'date_str'] 

column_to_be_updated = 'total_supplemental_ppfd_requirement_umol_m2_s_h'

# --- Run updates ---
update_column_from_base(base_file_path, excel_target_path, standard_keys, base_file_actual_keys, column_to_be_updated)
update_column_from_base(base_file_path, csv_target_path, standard_keys, base_file_actual_keys, column_to_be_updated)

print("Script finished.") 