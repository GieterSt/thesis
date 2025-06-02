import pandas as pd

# --- Configuration ---
COMPLETE_DATA_FILE = 'Complete_Merged_Dataset_2024_2025.xlsx'
COLUMN_TO_INSPECT = 'total_supplemental_ppfd_requirement_umol_m2_s_h'

print(f"=== Analyzing Hourly Requirement Column: {COLUMN_TO_INSPECT} ===")

try:
    df_complete = pd.read_excel(COMPLETE_DATA_FILE)
except FileNotFoundError:
    print(f"   ❌ ERROR: Could not find input file: {COMPLETE_DATA_FILE}")
    exit()

if COLUMN_TO_INSPECT not in df_complete.columns:
    print(f"   ❌ ERROR: Column '{COLUMN_TO_INSPECT}' not found in the dataset.")
    exit()

hourly_requirements = df_complete[COLUMN_TO_INSPECT].dropna()

if not hourly_requirements.empty:
    print(f"   Stats for '{COLUMN_TO_INSPECT}' (from {len(hourly_requirements)} non-NaN hourly records):")
    print(f"     Min:    {hourly_requirements.min():.4f}")
    print(f"     Max:    {hourly_requirements.max():.4f}")
    print(f"     Mean:   {hourly_requirements.mean():.4f}")
    print(f"     Median: {hourly_requirements.median():.4f}")
    print(f"     Std Dev:{hourly_requirements.std():.4f}")
    print(f"     1st Pctl:  {hourly_requirements.quantile(0.01):.4f}") # Check low values
    print(f"     10th Pctl: {hourly_requirements.quantile(0.10):.4f}")
    print(f"     90th Pctl: {hourly_requirements.quantile(0.90):.4f}")
    print(f"     99th Pctl: {hourly_requirements.quantile(0.99):.4f}")
    
    # Calculate what a sum of 24 max hourly values would be
    theoretical_max_daily_sum = hourly_requirements.max() * 24
    print(f"\n   Theoretical max daily sum (24 * max hourly value of {hourly_requirements.max():.4f}): {theoretical_max_daily_sum:.4f}")
else:
    print(f"   No valid (non-NaN) values found for column '{COLUMN_TO_INSPECT}'.")

print("\n=== Analysis Complete ===") 