import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_training_set():
    """Create a training set from all dates not used in test or validation sets"""
    
    # File paths
    base_file = "data/raw_data/model_data_prep.xlsx"
    test_file = "data/ground_truth/test_set_ground_truth_complete.xlsx"
    validation_file = "data/ground_truth/validation_set_ground_truth_complete.xlsx"
    output_file = "data/ground_truth/training_set_ground_truth_complete.xlsx"
    
    print("Loading data files...")
    
    # Read the files
    base_df = pd.read_excel(base_file)
    test_df = pd.read_excel(test_file)
    validation_df = pd.read_excel(validation_file)
    
    # Convert date columns to datetime
    base_df['date'] = pd.to_datetime(base_df['date'])
    test_df['date'] = pd.to_datetime(test_df['date'])
    validation_df['date'] = pd.to_datetime(validation_df['date'])
    
    # Get unique dates from all datasets
    base_dates = set(base_df['date'].unique())
    test_dates = set(test_df['date'].unique())
    validation_dates = set(validation_df['date'].unique())
    
    print(f"Total available dates in base data: {len(base_dates)}")
    print(f"Dates used in test set: {len(test_dates)}")
    print(f"Dates used in validation set: {len(validation_dates)}")
    
    # Check for any overlap between test and validation (there shouldn't be any)
    overlap_dates = test_dates.intersection(validation_dates)
    if overlap_dates:
        print(f"WARNING: Found {len(overlap_dates)} overlapping dates between test and validation!")
        print(f"Overlapping dates: {sorted(overlap_dates)}")
    else:
        print("✓ No overlap between test and validation sets")
    
    # Find dates that are NOT in either test or validation sets
    used_dates = test_dates.union(validation_dates)
    training_dates = base_dates - used_dates
    
    print(f"Dates used in test + validation: {len(used_dates)}")
    print(f"Remaining dates for training set: {len(training_dates)}")
    
    # Sort the training dates
    training_dates = sorted(list(training_dates))
    
    # Extract data for the training dates
    training_df = base_df[base_df['date'].isin(training_dates)].copy()
    
    print(f"Training set shape: {training_df.shape}")
    print(f"Expected shape for {len(training_dates)} days: {len(training_dates) * 24} rows")
    
    # Verify we have 24 hours for each day
    hours_per_day = training_df.groupby('date')['hour'].count()
    incomplete_days = hours_per_day[hours_per_day != 24]
    
    if len(incomplete_days) > 0:
        print(f"WARNING: Found {len(incomplete_days)} days with incomplete hour data:")
        print(incomplete_days.head(10))  # Show first 10 incomplete days
        if len(incomplete_days) > 10:
            print(f"... and {len(incomplete_days) - 10} more")
    else:
        print("✓ All training days have complete 24-hour data")
    
    # Sort by date and hour
    training_df = training_df.sort_values(['date', 'hour']).reset_index(drop=True)
    
    # Save to Excel file
    print(f"Saving training set to {output_file}")
    training_df.to_excel(output_file, index=False)
    
    # Print summary statistics
    print("\n=== TRAINING SET SUMMARY ===")
    print(f"Date range: {training_df['date'].min()} to {training_df['date'].max()}")
    print(f"Total days: {training_df['date'].nunique()}")
    print(f"Total rows: {len(training_df)}")
    
    # Print some sample dates
    if len(training_dates) >= 10:
        sample_dates = training_dates[:10]
        print(f"First 10 dates: {[d.strftime('%Y-%m-%d') for d in sample_dates]}")
        
        sample_dates = training_dates[-10:]
        print(f"Last 10 dates: {[d.strftime('%Y-%m-%d') for d in sample_dates]}")
    else:
        print(f"All training dates: {[d.strftime('%Y-%m-%d') for d in training_dates]}")
    
    # Compare basic statistics with test and validation sets
    print("\n=== COMPARISON WITH TEST AND VALIDATION SETS ===")
    numeric_cols = ['EUR/PPFD', 'daily_total_ppfd_requirement', 'max_ppfd_to_addumol_m2_s', 'ppfd_allocated']
    
    print("Test Set Statistics:")
    print(test_df[numeric_cols].describe())
    
    print("\nValidation Set Statistics:")
    print(validation_df[numeric_cols].describe())
    
    print("\nTraining Set Statistics:")
    print(training_df[numeric_cols].describe())
    
    # Print dataset split summary
    print("\n=== DATASET SPLIT SUMMARY ===")
    total_days = len(base_dates)
    test_days = len(test_dates)
    validation_days = len(validation_dates)
    training_days = len(training_dates)
    
    print(f"Total available days: {total_days}")
    print(f"Test set days: {test_days} ({test_days/total_days*100:.1f}%)")
    print(f"Validation set days: {validation_days} ({validation_days/total_days*100:.1f}%)")
    print(f"Training set days: {training_days} ({training_days/total_days*100:.1f}%)")
    print(f"Total used: {test_days + validation_days + training_days} ({(test_days + validation_days + training_days)/total_days*100:.1f}%)")
    
    return training_df, training_days

if __name__ == "__main__":
    training_set, num_training_days = create_training_set()
    print(f"\n✅ Training set creation completed!")
    print(f"🎯 Training set contains {num_training_days} days of data") 