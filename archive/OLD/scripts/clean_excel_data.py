import pandas as pd

def clean_excel_data(input_file, output_file):
    """Remove redundant date_str column, add PPFD calculation, and save cleaned Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(input_file)
        
        print(f"Original data shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")
        
        # Check if date_str column exists
        if 'date_str' in df.columns:
            # Remove the date_str column
            df_cleaned = df.drop('date_str', axis=1)
            print(f"\nRemoved 'date_str' column")
        else:
            df_cleaned = df
            print(f"\n'date_str' column not found")
        
        # Convert ssrd_kwh_m2 to W/m² (1 kWh/m² = 1000 Wh/m²)
        # Since this is hourly data, we need to convert kWh/m² to W/m²
        # For hourly data: W/m² = kWh/m² × 1000
        df_cleaned['ssrd_w_m2'] = df_cleaned['ssrd_kwh_m2'] * 1000
        
        # Calculate Natural Outside PPFD using the conversion factor
        # Natural Outside PPFD (μmol/m²/s) = Surface Solar Radiation Downwards (W/m²) × 2.04
        df_cleaned['natural_outside_ppfd_umol_m2_s'] = df_cleaned['ssrd_w_m2'] * 2.04
        
        print(f"Cleaned data shape: {df_cleaned.shape}")
        print(f"Cleaned columns: {list(df_cleaned.columns)}")
        
        # Save the cleaned data
        df_cleaned.to_excel(output_file, index=False)
        print(f"\nCleaned data saved to: {output_file}")
        
        # Show preview of cleaned data
        print(f"\nPreview of cleaned data:")
        print(df_cleaned.head(3).to_string())
        
        # Show some statistics for the new columns
        print(f"\nStatistics for new columns:")
        print(f"SSRD (W/m²) - Min: {df_cleaned['ssrd_w_m2'].min():.2f}, Max: {df_cleaned['ssrd_w_m2'].max():.2f}, Mean: {df_cleaned['ssrd_w_m2'].mean():.2f}")
        print(f"Natural Outside PPFD (μmol/m²/s) - Min: {df_cleaned['natural_outside_ppfd_umol_m2_s'].min():.2f}, Max: {df_cleaned['natural_outside_ppfd_umol_m2_s'].max():.2f}, Mean: {df_cleaned['natural_outside_ppfd_umol_m2_s'].mean():.2f}")
        
        return df_cleaned
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None

if __name__ == "__main__":
    input_file = "SSRD_data_2024-2025.xlsx"
    output_file = "SSRD_data_2024-2025_cleaned.xlsx"
    
    clean_excel_data(input_file, output_file) 