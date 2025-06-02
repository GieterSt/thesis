import pandas as pd

def remove_days_with_missing_ranks():
    file_path = '/Users/guidosteenbergen/Library/CloudStorage/OneDrive-Personal/Guido/Opleiding/Master BIM/Thesis/Data preparation/model_data_prep.xlsx'

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return

    if 'date' not in df.columns or 'RANK eur/ppfd' not in df.columns:
        print(f"Error: Required columns ('date' and/or 'RANK eur/ppfd') not found in the file.")
        print(f"Available columns are: {df.columns.tolist()}")
        return

    # Find rows where 'RANK eur/ppfd' is missing
    missing_rank_df = df[df['RANK eur/ppfd'].isna()]

    if missing_rank_df.empty:
        print("No missing values found in the 'RANK eur/ppfd' column. No days were removed.")
        return

    # Get the unique dates that have at least one missing rank
    dates_to_remove = missing_rank_df['date'].unique()
    num_dates_to_remove = len(dates_to_remove)

    print(f"Identified {num_dates_to_remove} unique day(s) with missing 'RANK eur/ppfd' values. These days will be removed.")
    # print(f"Dates to be removed: {dates_to_remove}") # Optional: for debugging

    # Filter out the rows belonging to these dates
    # The .isin() method checks for each date in df['date'] if it is present in dates_to_remove
    # The ~ negates this, so we keep rows where the date is NOT in dates_to_remove
    df_cleaned = df[~df['date'].isin(dates_to_remove)]
    
    original_row_count = len(df)
    cleaned_row_count = len(df_cleaned)
    rows_removed_count = original_row_count - cleaned_row_count

    try:
        df_cleaned.to_excel(file_path, index=False)
        print(f"Successfully removed {rows_removed_count} rows belonging to {num_dates_to_remove} day(s) from the dataset.")
        print(f"The cleaned dataset has been saved back to: {file_path}")
    except Exception as e:
        print(f"Error saving the cleaned file: {e}")

if __name__ == '__main__':
    remove_days_with_missing_ranks() 