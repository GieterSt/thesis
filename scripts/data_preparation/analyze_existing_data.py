import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def analyze_data_files():
    """Analyze the existing data files to understand structure and distribution"""
    
    # File paths
    base_file = "data/raw_data/model_data_prep.xlsx"
    test_file = "data/ground_truth/test_set_ground_truth_complete.xlsx"
    
    print("=== ANALYZING BASE DATA FILE ===")
    try:
        # Read the base data file
        base_df = pd.read_excel(base_file)
        print(f"Base file shape: {base_df.shape}")
        print(f"Base file columns: {list(base_df.columns)}")
        print("\nFirst few rows of base data:")
        print(base_df.head())
        print("\nBase data info:")
        print(base_df.info())
        
        # Check date columns
        date_columns = [col for col in base_df.columns if 'date' in col.lower() or 'time' in col.lower()]
        print(f"\nPotential date columns: {date_columns}")
        
        if date_columns:
            for col in date_columns:
                print(f"\nUnique values in {col} (first 10):")
                print(base_df[col].head(10))
        
    except Exception as e:
        print(f"Error reading base file: {e}")
    
    print("\n" + "="*50)
    print("=== ANALYZING TEST SET FILE ===")
    try:
        # Read the test set file
        test_df = pd.read_excel(test_file)
        print(f"Test file shape: {test_df.shape}")
        print(f"Test file columns: {list(test_df.columns)}")
        print("\nFirst few rows of test data:")
        print(test_df.head())
        print("\nTest data info:")
        print(test_df.info())
        
        # Check date columns
        date_columns = [col for col in test_df.columns if 'date' in col.lower() or 'time' in col.lower()]
        print(f"\nPotential date columns: {date_columns}")
        
        if date_columns:
            for col in date_columns:
                print(f"\nUnique values in {col} (first 10):")
                print(test_df[col].head(10))
                
        # Check for any statistical distributions
        numeric_columns = test_df.select_dtypes(include=[np.number]).columns
        print(f"\nNumeric columns: {list(numeric_columns)}")
        
        if len(numeric_columns) > 0:
            print("\nBasic statistics for numeric columns:")
            print(test_df[numeric_columns].describe())
            
    except Exception as e:
        print(f"Error reading test file: {e}")

if __name__ == "__main__":
    analyze_data_files() 