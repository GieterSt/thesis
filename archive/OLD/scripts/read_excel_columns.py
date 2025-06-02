import pandas as pd
import sys

def read_excel_columns(file_path):
    """Read Excel file and display all columns from all sheets"""
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(file_path)
        
        print(f"Excel file: {file_path}")
        print(f"Number of sheets: {len(excel_file.sheet_names)}")
        print("=" * 50)
        
        # Iterate through all sheets
        for sheet_name in excel_file.sheet_names:
            print(f"\nSheet: '{sheet_name}'")
            print("-" * 30)
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Shape: {df.shape} (rows, columns)")
            print(f"Columns ({len(df.columns)}):")
            
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")
            
            # Show first few rows to understand the data structure
            print(f"\nFirst 3 rows preview:")
            print(df.head(3).to_string())
            print("=" * 50)
            
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

if __name__ == "__main__":
    file_path = "SSRD_data_2024-2025.xlsx"
    read_excel_columns(file_path) 