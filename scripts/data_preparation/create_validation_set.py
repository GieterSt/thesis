import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_validation_set():
    """Create a validation set with 72 different days from the same period"""
    
    # File paths
    base_file = "data/raw_data/model_data_prep.xlsx"
    test_file = "data/ground_truth/test_set_ground_truth_complete.xlsx"
    output_file = "data/ground_truth/validation_set_ground_truth_complete.xlsx"
    
    print("Loading data files...")
    
    # Read the files
    base_df = pd.read_excel(base_file)
    test_df = pd.read_excel(test_file)
    
    # Convert date columns to datetime
    base_df['date'] = pd.to_datetime(base_df['date'])
    test_df['date'] = pd.to_datetime(test_df['date'])
    
    # Get unique dates from both datasets
    base_dates = base_df['date'].unique()
    test_dates = test_df['date'].unique()
    
    print(f"Total available dates in base data: {len(base_dates)}")
    print(f"Dates used in test set: {len(test_dates)}")
    print(f"Date range in base data: {base_dates.min()} to {base_dates.max()}")
    print(f"Date range in test set: {test_dates.min()} to {test_dates.max()}")
    
    # Find available dates that are NOT in the test set
    available_dates = [date for date in base_dates if date not in test_dates]
    print(f"Available dates for validation set: {len(available_dates)}")
    
    if len(available_dates) < 72:
        print(f"WARNING: Only {len(available_dates)} dates available, but 72 requested!")
        validation_dates = available_dates
    else:
        # Randomly select 72 dates
        random.seed(42)  # For reproducibility
        validation_dates = random.sample(list(available_dates), 72)
    
    print(f"Selected {len(validation_dates)} dates for validation set")
    
    # Sort the dates
    validation_dates = sorted(validation_dates)
    
    # Extract data for the selected validation dates
    validation_df = base_df[base_df['date'].isin(validation_dates)].copy()
    
    print(f"Validation set shape: {validation_df.shape}")
    print(f"Expected shape for 72 days: {72 * 24} rows")
    
    # Verify we have 24 hours for each day
    hours_per_day = validation_df.groupby('date')['hour'].count()
    incomplete_days = hours_per_day[hours_per_day != 24]
    
    if len(incomplete_days) > 0:
        print(f"WARNING: Found {len(incomplete_days)} days with incomplete hour data:")
        print(incomplete_days)
    else:
        print("✓ All selected days have complete 24-hour data")
    
    # Sort by date and hour
    validation_df = validation_df.sort_values(['date', 'hour']).reset_index(drop=True)
    
    # Save to Excel file
    print(f"Saving validation set to {output_file}")
    validation_df.to_excel(output_file, index=False)
    
    # Print summary statistics to compare with test set
    print("\n=== VALIDATION SET SUMMARY ===")
    print(f"Date range: {validation_df['date'].min()} to {validation_df['date'].max()}")
    print(f"Total days: {validation_df['date'].nunique()}")
    print(f"Total rows: {len(validation_df)}")
    
    # Print some sample dates
    sample_dates = sorted(validation_df['date'].unique())[:10]
    print(f"First 10 dates: {[d.strftime('%Y-%m-%d') for d in sample_dates]}")
    
    if len(validation_df['date'].unique()) > 10:
        sample_dates = sorted(validation_df['date'].unique())[-10:]
        print(f"Last 10 dates: {[d.strftime('%Y-%m-%d') for d in sample_dates]}")
    
    # Compare basic statistics with test set
    print("\n=== COMPARISON WITH TEST SET ===")
    numeric_cols = ['EUR/PPFD', 'daily_total_ppfd_requirement', 'max_ppfd_to_addumol_m2_s', 'ppfd_allocated']
    
    print("Test Set Statistics:")
    print(test_df[numeric_cols].describe())
    
    print("\nValidation Set Statistics:")
    print(validation_df[numeric_cols].describe())
    
    return validation_df

if __name__ == "__main__":
    validation_set = create_validation_set()
    print("\n✓ Validation set creation completed!") 