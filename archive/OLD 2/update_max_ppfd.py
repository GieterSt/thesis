import pandas as pd

# Define the file path and column to update
excel_file_path = "Complete_Merged_Dataset_2024_2025.xlsx"
column_to_update = "max_ppfd_to_addumol_m2_s"
old_value = 360
new_value = 300

def update_excel_column(file_path, column_name, old_val, new_val):
    print(f"Processing Excel file: {file_path}...")
    try:
        # Read the Excel file, assuming data is in the first sheet
        df = pd.read_excel(file_path, sheet_name=0)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in {file_path}.")
        return

    # Ensure the column is numeric to handle potential string representations of numbers
    # Coerce errors will turn non-numeric values into NaN, which won't match old_val (unless old_val is also NaN)
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')

    # Replace the old value with the new value
    # We check for both integer and float versions of old_val for robustness
    df[column_name] = df[column_name].replace({float(old_val): float(new_val), int(old_val): int(new_val)})
    # An alternative way for direct replacement, which might be less robust with types:
    # df.loc[df[column_name] == old_val, column_name] = new_val
    # df.loc[df[column_name] == float(old_val), column_name] = float(new_val) # for cases where it might be float

    try:
        df.to_excel(file_path, index=False)
        print(f"Successfully updated column '{column_name}' from {old_val} to {new_val} in {file_path}")
    except Exception as e:
        print(f"Error saving the file {file_path}: {e}")

# Run the update function
update_excel_column(excel_file_path, column_to_update, old_value, new_value) 