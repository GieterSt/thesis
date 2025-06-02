import json
import os
import pandas as pd
import datetime

def extract_and_augment_test_set_data():
    base_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/'
    test_set_path = os.path.join(base_path, 'test_set.json')
    source_data_path = os.path.join(base_path, 'Merged_Template_with_SSRD_Data.xlsx')
    output_excel_path = os.path.join(base_path, 'test_set_augmented_data.xlsx')

    try:
        with open(test_set_path, 'r', encoding='utf-8') as f:
            test_examples = json.load(f)
    except FileNotFoundError:
        print(f"Error: Test set file not found at {test_set_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {test_set_path}")
        return
    except Exception as e:
        print(f"Error reading test set file: {e}")
        return

    if not test_examples:
        print("Test set file is empty. No dates to extract.")
        return

    unique_dates = set()
    for i, example in enumerate(test_examples):
        try:
            user_content = example["messages"][0]["content"]
            date_line = user_content.split('\n', 1)[0]
            if date_line.startswith("Date: "):
                date_str = date_line.replace("Date: ", "").strip()
                datetime.datetime.strptime(date_str, "%Y-%m-%d") 
                unique_dates.add(date_str)
            else:
                print(f"Warning: Date line not found or not in expected format in example {i}. Skipping. Content: '{date_line[:50]}...'")
        except (IndexError, ValueError, KeyError) as e:
            print(f"Warning: Could not parse date or structure invalid for example {i}: {str(e)}. Example: {str(example)[:100]}... Skipping.")
            continue
    
    if not unique_dates:
        print("No valid dates found in the test set.")
        return
    print(f"Found {len(unique_dates)} unique dates in the test set.")

    date_hour_records = []
    for date_str in sorted(list(unique_dates)):
        for hour in range(24):
            date_hour_records.append({'date': date_str, 'hour': hour})
    
    df_test_skeleton = pd.DataFrame(date_hour_records)
    df_test_skeleton['date'] = df_test_skeleton['date'].astype(str)
    df_test_skeleton['hour'] = df_test_skeleton['hour'].astype(int)

    try:
        df_source_data = pd.read_excel(source_data_path)
    except FileNotFoundError:
        print(f"Error: Source data file not found at {source_data_path}")
        return
    except Exception as e:
        print(f"Error reading source data file: {e}")
        return

    print(f"Loaded {len(df_source_data)} rows from {source_data_path}")

    if 'date' in df_source_data.columns:
        if pd.api.types.is_datetime64_any_dtype(df_source_data['date']):
            df_source_data['date'] = df_source_data['date'].dt.strftime('%Y-%m-%d')
        df_source_data['date'] = df_source_data['date'].astype(str)
    else:
        print(f"Error: 'date' column not found in {source_data_path}")
        return
        
    if 'hour' in df_source_data.columns:
        df_source_data['hour'] = df_source_data['hour'].astype(int)
    else:
        print(f"Error: 'hour' column not found in {source_data_path}")
        return

    print("Merging test set skeleton with source data...")
    df_augmented_test_data = pd.merge(df_test_skeleton, df_source_data, on=['date', 'hour'], how='left')

    print(f"Augmented test dataset has {len(df_augmented_test_data)} rows.")

    try:
        df_augmented_test_data.to_excel(output_excel_path, index=False)
        print(f"Successfully created augmented test data Excel file: {output_excel_path}")
    except Exception as e:
        print(f"Error saving augmented Excel file: {e}")

if __name__ == '__main__':
    extract_and_augment_test_set_data() 