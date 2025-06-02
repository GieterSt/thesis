import pandas as pd

# --- Configuration ---
TEST_SET_SKELETON_FILE = 'test_set_date_hour_index.xlsx'
MODEL_DATA_PREP_FILE = 'old3/model_data_prep.xlsx'
OUTPUT_GROUND_TRUTH_FILE = 'test_set_ground_truth_complete.xlsx'

def main():
    print(f"Loading test set skeleton from: {TEST_SET_SKELETON_FILE}")
    try:
        test_skeleton_df = pd.read_excel(TEST_SET_SKELETON_FILE)
    except FileNotFoundError:
        print(f"Error: Test set skeleton file '{TEST_SET_SKELETON_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading {TEST_SET_SKELETON_FILE}: {e}")
        return

    print(f"Loading model data prep from: {MODEL_DATA_PREP_FILE}")
    try:
        model_data_df = pd.read_excel(MODEL_DATA_PREP_FILE)
    except FileNotFoundError:
        print(f"Error: Model data prep file '{MODEL_DATA_PREP_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading {MODEL_DATA_PREP_FILE}: {e}")
        return

    # Ensure date columns are in a consistent format for merging (string YYYY-MM-DD)
    # For test_skeleton_df:
    if pd.api.types.is_datetime64_any_dtype(test_skeleton_df['date']):
        test_skeleton_df['date'] = test_skeleton_df['date'].dt.strftime('%Y-%m-%d')
    else:
        try:
            test_skeleton_df['date'] = pd.to_datetime(test_skeleton_df['date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Warning: Could not standardize date format in {TEST_SET_SKELETON_FILE}. Proceeding with current format. Error: {e}")
            test_skeleton_df['date'] = test_skeleton_df['date'].astype(str)
            
    test_skeleton_df['hour'] = test_skeleton_df['hour'].astype(int)

    # For model_data_df:
    if pd.api.types.is_datetime64_any_dtype(model_data_df['date']):
        model_data_df['date'] = model_data_df['date'].dt.strftime('%Y-%m-%d')
    else:
        try:
            model_data_df['date'] = pd.to_datetime(model_data_df['date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Warning: Could not standardize date format in {MODEL_DATA_PREP_FILE}. Proceeding with current format. Error: {e}")
            model_data_df['date'] = model_data_df['date'].astype(str)
            
    model_data_df['hour'] = model_data_df['hour'].astype(int)

    print(f"Merging dataframes on 'date' and 'hour'...")
    # Perform a left merge to keep all rows from test_skeleton_df and add info from model_data_df
    complete_test_set_df = pd.merge(test_skeleton_df, model_data_df, on=['date', 'hour'], how='left')

    # Check if merge resulted in any matched rows
    if complete_test_set_df.empty:
        print("Warning: The merge resulted in an empty DataFrame. No matching date-hour pairs found.")
    elif complete_test_set_df[model_data_df.columns.drop(['date', 'hour'], errors='ignore')].isnull().all().all():
        print("Warning: Merge was successful, but all columns from model_data_prep.xlsx are NaN. This suggests no matching date-hour pairs were found.")
    else:
        print(f"Merge successful. Resulting dataframe shape: {complete_test_set_df.shape}")

    try:
        complete_test_set_df.to_excel(OUTPUT_GROUND_TRUTH_FILE, index=False)
        print(f"Successfully created complete test set ground truth: '{OUTPUT_GROUND_TRUTH_FILE}'")
    except Exception as e:
        print(f"Error writing output to {OUTPUT_GROUND_TRUTH_FILE}: {e}")

if __name__ == '__main__':
    main() 