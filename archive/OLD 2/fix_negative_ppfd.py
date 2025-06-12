import pandas as pd

# Define the input file base name and the column to fix
file_basename = "Complete_Merged_Dataset_2024_2025"
csv_file_path = f"{file_basename}.csv"
excel_file_path = f"{file_basename}.xlsx" # Added for Excel
column_to_fix = "total_supplemental_ppfd_requirement_umol_m2_s_h"

def fix_file(file_path, file_type='csv'):
    print(f"Processing {file_type} file: {file_path}...")
    try:
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type == 'excel':
            # Assuming the data is in the first sheet, adjust if needed
            df = pd.read_excel(file_path, sheet_name=0) 
        else:
            print(f"Unsupported file type: {file_type}")
            return
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if column_to_fix not in df.columns:
        print(f"Error: Column '{column_to_fix}' not found in {file_path}.")
        return

    # Convert column to numeric, coercing errors to NaN
    df[column_to_fix] = pd.to_numeric(df[column_to_fix], errors='coerce')

    # Fix negative values: set them to 0
    df[column_to_fix] = df[column_to_fix].apply(lambda x: 0 if pd.notna(x) and x < 0 else x)

    try:
        if file_type == 'csv':
            df.to_csv(file_path, index=False)
        elif file_type == 'excel':
            df.to_excel(file_path, index=False)
        
        print(f"Successfully fixed negative values in '{column_to_fix}' and saved to {file_path}")
    except Exception as e:
        print(f"Error saving the file {file_path}: {e}")

# Process the CSV file
fix_file(csv_file_path, file_type='csv')

# Process the Excel file
fix_file(excel_file_path, file_type='excel') 