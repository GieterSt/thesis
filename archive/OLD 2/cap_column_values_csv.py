import pandas as pd

# Define the file path, column to update, and the cap value
csv_file_path = "Complete_Merged_Dataset_2024_2025.csv"
column_to_cap = "max_ppfd_to_addumol_m2_s"
cap_value = 300

def cap_column_in_csv(file_path, column_name, upper_bound):
    print(f"Processing CSV file: {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in {file_path}.")
        return

    # Convert column to numeric, coercing errors to NaN
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')

    # Apply the cap: if value > upper_bound, set to upper_bound
    # This also handles NaN values correctly by not changing them unless they somehow become > upper_bound (which they won't)
    df[column_name] = df[column_name].apply(lambda x: upper_bound if pd.notna(x) and x > upper_bound else x)

    try:
        df.to_csv(file_path, index=False)
        print(f"Successfully capped values in column '{column_name}' at {upper_bound} in {file_path}")
    except Exception as e:
        print(f"Error saving the file {file_path}: {e}")

# Run the capping function
cap_column_in_csv(csv_file_path, column_to_cap, cap_value) 