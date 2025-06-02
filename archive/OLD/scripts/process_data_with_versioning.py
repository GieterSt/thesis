import pandas as pd
import os
from datetime import datetime

def process_excel_with_versioning(input_file, base_name, version_description, output_dir="data_versions", 
                                add_ppfd_inside=False, tau=0.74, add_dli=False, photoperiod=12, 
                                add_cumulative_dli=False, add_supplemental_dli=False, target_dli=17,
                                add_supplemental_ppfd_requirement=False):
    """
    Process Excel file and create a new version with proper naming
    
    Args:
        input_file: Path to input Excel file
        base_name: Base name for the output file (e.g., "SSRD_data")
        version_description: Description of what this version contains
        output_dir: Directory to save versioned files
        add_ppfd_inside: Whether to add PPFD_inside calculation
        tau: Transmission factor for PPFD_inside calculation (default 0.74)
        add_dli: Whether to add DLI calculation
        photoperiod: Photoperiod in hours for DLI calculation (default 12)
        add_cumulative_dli: Whether to add cumulative DLI throughout the day
        add_supplemental_dli: Whether to add supplemental DLI calculation
        target_dli: Target DLI for supplemental calculation (default 17 mol/m²/d)
        add_supplemental_ppfd_requirement: Whether to add total supplemental PPFD requirement
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the Excel file
        df = pd.read_excel(input_file)
        
        print(f"Processing: {input_file}")
        print(f"Original data shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")
        
        # Remove redundant date_str column if it exists
        if 'date_str' in df.columns:
            df = df.drop('date_str', axis=1)
            print(f"\nRemoved 'date_str' column")
        
        # Convert ssrd_kwh_m2 to W/m² if not already present
        if 'ssrd_w_m2' not in df.columns and 'ssrd_kwh_m2' in df.columns:
            df['ssrd_w_m2'] = df['ssrd_kwh_m2'] * 1000
            print(f"Added 'ssrd_w_m2' column (converted from kWh/m² to W/m²)")
        
        # Calculate Natural Outside PPFD if not already present
        if 'natural_outside_ppfd_umol_m2_s' not in df.columns and 'ssrd_w_m2' in df.columns:
            df['natural_outside_ppfd_umol_m2_s'] = df['ssrd_w_m2'] * 2.04
            print(f"Added 'natural_outside_ppfd_umol_m2_s' column (PPFD calculation)")
        
        # Calculate PPFD_inside if requested and outside PPFD exists
        if add_ppfd_inside and 'natural_outside_ppfd_umol_m2_s' in df.columns:
            if 'ppfd_inside_umol_m2_s' not in df.columns:
                df['ppfd_inside_umol_m2_s'] = df['natural_outside_ppfd_umol_m2_s'] * tau
                print(f"Added 'ppfd_inside_umol_m2_s' column (PPFD_inside = PPFD_outside × τ={tau})")
        
        # Calculate Natural Inside DLI if requested and inside PPFD exists
        if add_dli and 'ppfd_inside_umol_m2_s' in df.columns:
            if 'natural_inside_dli_mol_m2_d' not in df.columns:
                # DLI = PPFD (µmol m⁻² s⁻¹) × photoperiod (h) × 3.6 × 10⁻³
                df['natural_inside_dli_mol_m2_d'] = df['ppfd_inside_umol_m2_s'] * photoperiod * 3.6e-3
                print(f"Added 'natural_inside_dli_mol_m2_d' column (DLI = PPFD × {photoperiod}h × 3.6×10⁻³)")
        
        # Calculate Cumulative Natural Inside DLI throughout the day
        if add_cumulative_dli and 'ppfd_inside_umol_m2_s' in df.columns:
            if 'cumulative_natural_inside_dli_mol_m2' not in df.columns:
                # Ensure datetime column is properly formatted
                df['datetime'] = pd.to_datetime(df['datetime'])
                
                # Calculate hourly DLI contribution (PPFD × 1 hour × 3.6×10⁻³)
                hourly_dli = df['ppfd_inside_umol_m2_s'] * 1 * 3.6e-3
                
                # Create date column for grouping
                df['date'] = df['datetime'].dt.date
                
                # Calculate cumulative DLI within each day (resets at midnight)
                df['cumulative_natural_inside_dli_mol_m2'] = hourly_dli.groupby(df['date']).cumsum()
                
                # Remove the temporary date column
                df = df.drop('date', axis=1)
                
                print(f"Added 'cumulative_natural_inside_dli_mol_m2' column (cumulative DLI throughout each day)")
        
        # Calculate Supplemental DLI needed (based on total daily natural DLI)
        if add_supplemental_dli and 'ppfd_inside_umol_m2_s' in df.columns:
            if 'supplemental_dli_needed_mol_m2_d' not in df.columns:
                # Ensure datetime column is properly formatted
                df['datetime'] = pd.to_datetime(df['datetime'])
                
                # Calculate hourly DLI contribution (PPFD × 1 hour × 3.6×10⁻³)
                hourly_dli = df['ppfd_inside_umol_m2_s'] * 1 * 3.6e-3
                
                # Create date column for grouping
                df['date'] = df['datetime'].dt.date
                
                # Calculate total daily natural DLI for each day
                daily_natural_dli = hourly_dli.groupby(df['date']).transform('sum')
                
                # Supplemental DLI = Target DLI - Total Daily Natural DLI (minimum 0)
                df['supplemental_dli_needed_mol_m2_d'] = (target_dli - daily_natural_dli).clip(lower=0)
                
                # Remove the temporary date column
                df = df.drop('date', axis=1)
                
                print(f"Added 'supplemental_dli_needed_mol_m2_d' column (Target DLI {target_dli} - Total Daily Natural DLI, min 0)")
                print(f"Note: All hours of the same day show the same supplemental DLI value")
        
        # Calculate Total Supplemental PPFD Requirement
        if add_supplemental_ppfd_requirement and 'supplemental_dli_needed_mol_m2_d' in df.columns:
            if 'total_supplemental_ppfd_requirement_umol_m2_s_h' not in df.columns:
                # Total supplemental PPFD requirement = Supplemental DLI × 277,778
                df['total_supplemental_ppfd_requirement_umol_m2_s_h'] = df['supplemental_dli_needed_mol_m2_d'] * 277778
                print(f"Added 'total_supplemental_ppfd_requirement_umol_m2_s_h' column (Supplemental DLI × 277,778)")
        
        # Create output filename with version
        output_file = os.path.join(output_dir, f"{base_name}_{version_description}.xlsx")
        
        # Save the processed data
        df.to_excel(output_file, index=False)
        
        print(f"\nProcessed data shape: {df.shape}")
        print(f"Final columns: {list(df.columns)}")
        print(f"Saved to: {output_file}")
        
        # Show preview
        print(f"\nPreview of processed data:")
        print(df.head(3).to_string())
        
        # Show statistics for PPFD and DLI columns
        if 'natural_outside_ppfd_umol_m2_s' in df.columns:
            print(f"\nStatistics:")
            print(f"SSRD (W/m²) - Min: {df['ssrd_w_m2'].min():.2f}, Max: {df['ssrd_w_m2'].max():.2f}, Mean: {df['ssrd_w_m2'].mean():.2f}")
            print(f"Natural Outside PPFD (μmol/m²/s) - Min: {df['natural_outside_ppfd_umol_m2_s'].min():.2f}, Max: {df['natural_outside_ppfd_umol_m2_s'].max():.2f}, Mean: {df['natural_outside_ppfd_umol_m2_s'].mean():.2f}")
            
            if 'ppfd_inside_umol_m2_s' in df.columns:
                print(f"PPFD Inside (μmol/m²/s) - Min: {df['ppfd_inside_umol_m2_s'].min():.2f}, Max: {df['ppfd_inside_umol_m2_s'].max():.2f}, Mean: {df['ppfd_inside_umol_m2_s'].mean():.2f}")
                print(f"Transmission factor (τ): {tau}")
                
                if 'natural_inside_dli_mol_m2_d' in df.columns:
                    print(f"Natural Inside DLI (mol/m²/d) - Min: {df['natural_inside_dli_mol_m2_d'].min():.3f}, Max: {df['natural_inside_dli_mol_m2_d'].max():.3f}, Mean: {df['natural_inside_dli_mol_m2_d'].mean():.3f}")
                    print(f"Photoperiod: {photoperiod} hours")
                
                if 'cumulative_natural_inside_dli_mol_m2' in df.columns:
                    print(f"Cumulative Natural Inside DLI (mol/m²) - Min: {df['cumulative_natural_inside_dli_mol_m2'].min():.3f}, Max: {df['cumulative_natural_inside_dli_mol_m2'].max():.3f}, Mean: {df['cumulative_natural_inside_dli_mol_m2'].mean():.3f}")
                
                if 'supplemental_dli_needed_mol_m2_d' in df.columns:
                    print(f"Supplemental DLI Needed (mol/m²/d) - Min: {df['supplemental_dli_needed_mol_m2_d'].min():.3f}, Max: {df['supplemental_dli_needed_mol_m2_d'].max():.3f}, Mean: {df['supplemental_dli_needed_mol_m2_d'].mean():.3f}")
                    print(f"Target DLI: {target_dli} mol/m²/d")
                    
                    # Calculate percentage of time supplemental lighting is needed
                    supplemental_needed_hours = (df['supplemental_dli_needed_mol_m2_d'] > 0).sum()
                    total_hours = len(df)
                    percentage = (supplemental_needed_hours / total_hours) * 100
                    print(f"Hours requiring supplemental lighting: {supplemental_needed_hours}/{total_hours} ({percentage:.1f}%)")
                
                if 'total_supplemental_ppfd_requirement_umol_m2_s_h' in df.columns:
                    print(f"Total Supplemental PPFD Requirement (μmol/m²/s·h) - Min: {df['total_supplemental_ppfd_requirement_umol_m2_s_h'].min():.0f}, Max: {df['total_supplemental_ppfd_requirement_umol_m2_s_h'].max():.0f}, Mean: {df['total_supplemental_ppfd_requirement_umol_m2_s_h'].mean():.0f}")
        
        return df, output_file
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None, None

def list_data_versions(data_dir="data_versions"):
    """List all data versions in the data directory"""
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' does not exist")
        return
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    if not files:
        print(f"No Excel files found in '{data_dir}'")
        return
    
    print(f"\nData versions in '{data_dir}':")
    print("-" * 50)
    for i, file in enumerate(sorted(files), 1):
        file_path = os.path.join(data_dir, file)
        size = os.path.getsize(file_path) / 1024  # Size in KB
        print(f"{i:2d}. {file} ({size:.1f} KB)")

if __name__ == "__main__":
    # First, recreate v6 with corrected supplemental DLI calculation
    print("Creating corrected v6 with proper supplemental DLI calculation...")
    input_file = "data_versions/SSRD_data_v5_with_cumulative_dli.xlsx"
    
    df_v6, output_file_v6 = process_excel_with_versioning(
        input_file=input_file,
        base_name="SSRD_data",
        version_description="v6_with_supplemental_dli_corrected",
        add_ppfd_inside=True,
        tau=0.74,
        add_dli=True,
        photoperiod=12,
        add_cumulative_dli=True,
        add_supplemental_dli=True,
        target_dli=17
    )
    
    print("\n" + "="*70)
    print("Creating corrected v7 with proper PPFD requirement calculation...")
    
    # Then create v7 with corrected PPFD requirement
    df_v7, output_file_v7 = process_excel_with_versioning(
        input_file=output_file_v6,
        base_name="SSRD_data",
        version_description="v7_with_supplemental_ppfd_requirement_corrected",
        add_ppfd_inside=True,
        tau=0.74,
        add_dli=True,
        photoperiod=12,
        add_cumulative_dli=True,
        add_supplemental_dli=True,
        target_dli=17,
        add_supplemental_ppfd_requirement=True
    )
    
    # List all versions
    list_data_versions() 