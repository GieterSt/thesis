import pandas as pd
import numpy as np

print("=== VERIFYING STRATIFIED TEST SET ===")

# --- Configuration ---
TEST_SET_FILE = 'Stratified_Test_Set_Solar_Price_Seasonal.xlsx'
COMPLETE_DATA_FILE = 'Complete_Merged_Dataset_2024_2025.xlsx'
TRAINING_EXAMPLES_FILE = 'PPFD_Training_Examples_17_Cases.xlsx'
EXPECTED_TOTAL_DAYS = 96
EXPECTED_DAYS_PER_QUARTER = 24
N_SPOT_CHECK_DAYS = 3 # Number of days to pick for detailed data integrity checks

# --- 1. Load Datasets ---
print(f"1. Loading datasets...")
error_found = False

try:
    df_test = pd.read_excel(TEST_SET_FILE)
    df_complete = pd.read_excel(COMPLETE_DATA_FILE)
    df_training = pd.read_excel(TRAINING_EXAMPLES_FILE)
except FileNotFoundError as e:
    print(f"   ❌ ERROR: Could not find input file: {e.filename}")
    exit()

# Convert date columns to datetime objects for proper comparison
df_test['date'] = pd.to_datetime(df_test['date'])
df_complete['date'] = pd.to_datetime(df_complete['date'])
df_training['date'] = pd.to_datetime(df_training['date'])

print(f"   Test set loaded: {len(df_test)} records, {df_test['date'].nunique()} unique days.")
print(f"   Complete dataset loaded: {len(df_complete)} records.")
print(f"   Training examples loaded: {df_training['date'].nunique()} unique days.")

# --- 2. Verification Checks ---

# Test Set Size
print("\n2.1. Verifying test set size...")
num_unique_test_days = df_test['date'].nunique()
if num_unique_test_days == EXPECTED_TOTAL_DAYS:
    print(f"   ✅ SUCCESS: Test set contains {num_unique_test_days} unique days as expected.")
else:
    print(f"   ❌ ERROR: Expected {EXPECTED_TOTAL_DAYS} unique days, but found {num_unique_test_days}.")
    error_found = True

# Training Data Exclusion
print("\n2.2. Verifying exclusion of training data...")
training_dates_in_test = set(df_training['date'].dt.date).intersection(set(df_test['date'].dt.date))
if not training_dates_in_test:
    print(f"   ✅ SUCCESS: No training example dates found in the test set.")
else:
    print(f"   ❌ ERROR: Found {len(training_dates_in_test)} training dates in the test set: {training_dates_in_test}")
    error_found = True

# Seasonal Balance (Quarters)
print("\n2.3. Verifying seasonal balance (days per quarter)...")
quarter_counts = df_test.groupby('quarter')['date'].nunique()
print("   Days per quarter found:")
print(quarter_counts)
balanced = True
for quarter, count in quarter_counts.items():
    if count != EXPECTED_DAYS_PER_QUARTER:
        print(f"   ❌ ERROR: Quarter {quarter} has {count} days, expected {EXPECTED_DAYS_PER_QUARTER}.")
        balanced = False
        error_found = True
if balanced and len(quarter_counts) == 4: # Assuming 4 quarters
    print(f"   ✅ SUCCESS: All quarters have {EXPECTED_DAYS_PER_QUARTER} days.")
elif not balanced:
    pass # Error already printed
else:
    print(f"   ❌ ERROR: Expected 4 quarters, found {len(quarter_counts)}.")
    error_found = True
    
# Hourly Data Completeness
print("\n2.4. Verifying hourly data completeness (24 hours per day)...")
hours_per_day = df_test.groupby(df_test['date'].dt.date)['hour'].count()
incomplete_days = hours_per_day[hours_per_day != 24]
if incomplete_days.empty:
    print(f"   ✅ SUCCESS: All {num_unique_test_days} test days have 24 hourly records.")
else:
    print(f"   ❌ ERROR: Found {len(incomplete_days)} days with not exactly 24 hours:")
    print(incomplete_days)
    error_found = True

# Data Integrity (Spot Check)
print(f"\n2.5. Performing data integrity spot checks for {N_SPOT_CHECK_DAYS} random days...")
if num_unique_test_days > 0:
    spot_check_dates = pd.Series(df_test['date'].unique()).sample(min(N_SPOT_CHECK_DAYS, num_unique_test_days), random_state=1)
    all_spot_checks_ok = True
    for check_date in spot_check_dates:
        print(f"      Checking date: {check_date.strftime('%Y-%m-%d')}...")
        test_day_data = df_test[df_test['date'] == check_date].sort_values(by='hour')
        complete_day_data = df_complete[df_complete['date'] == check_date].sort_values(by='hour')
        
        if len(test_day_data) != 24 or len(complete_day_data) != 24:
            print(f"         ❌ ERROR: Hourly data mismatch for spot check day {check_date.strftime('%Y-%m-%d')}. Test has {len(test_day_data)}, Complete has {len(complete_day_data)}.")
            all_spot_checks_ok = False
            error_found = True
            continue
            
        # Compare a few key values for a sample hour (e.g., hour 12)
        sample_hour = 12
        test_hour_data = test_day_data[test_day_data['hour'] == sample_hour].iloc[0]
        complete_hour_data = complete_day_data[complete_day_data['hour'] == sample_hour].iloc[0]
        
        columns_to_check = ['EUR/PPFD', 'max_ppfd_to_addumol_m2_s', 'total_supplemental_ppfd_requirement_umol_m2_s_h']
        hour_spot_check_ok = True
        for col in columns_to_check:
            val_test = test_hour_data[col]
            val_complete = complete_hour_data[col]
            if pd.isna(val_test) and pd.isna(val_complete):
                continue # Both are NaN, considered matching
            if not np.isclose(val_test, val_complete, equal_nan=True):
                print(f"            ❌ ERROR: Mismatch for {check_date.strftime('%Y-%m-%d')} hour {sample_hour}, column '{col}'. Test: {val_test}, Complete: {val_complete}")
                hour_spot_check_ok = False
                all_spot_checks_ok = False
                error_found = True
        if hour_spot_check_ok:
            print(f"         ✅ Data for hour {sample_hour} matches original dataset.")
    if all_spot_checks_ok:
        print(f"   ✅ SUCCESS: All {min(N_SPOT_CHECK_DAYS, num_unique_test_days)} spot-checked days have consistent data with the original dataset.")
else:
    print("   Skipping spot checks as there are no unique days in the test set to check.")

# Stratification Column Consistency
print(f"\n2.6. Verifying stratification column consistency for {N_SPOT_CHECK_DAYS} random days...")
if num_unique_test_days > 0:
    # Using the same spot_check_dates for this test
    all_strat_cols_consistent = True
    strat_cols_to_check = ['quarter', 'solar_stratum', 'price_stratum', 'stratify_col', 'avg_price', 'daily_requirement']
    for check_date in spot_check_dates:
        print(f"      Checking stratification columns for date: {check_date.strftime('%Y-%m-%d')}...")
        test_day_data = df_test[df_test['date'] == check_date]
        day_strat_consistent = True
        for col in strat_cols_to_check:
            if test_day_data[col].nunique() > 1:
                print(f"         ❌ ERROR: Column '{col}' is not consistent across all hours for day {check_date.strftime('%Y-%m-%d')}. Values: {test_day_data[col].unique()}")
                day_strat_consistent = False
                all_strat_cols_consistent = False
                error_found = True
        if day_strat_consistent:
            print(f"         ✅ Stratification columns are consistent for this day.")
    if all_strat_cols_consistent:
        print(f"   ✅ SUCCESS: Stratification columns are consistent across all hours for {min(N_SPOT_CHECK_DAYS, num_unique_test_days)} spot-checked days.")
else:
     print("   Skipping stratification column consistency checks as there are no unique days.")

# Absence of Critical NaNs
print("\n2.7. Checking for unexpected NaN values in critical columns...")
critical_columns_for_nans = ['date', 'hour', 'EUR/PPFD', 'RANK eur/ppfd', 'total_supplemental_ppfd_requirement_umol_m2_s_h', 'max_ppfd_to_addumol_m2_s']
found_critical_nan = False
for col in critical_columns_for_nans:
    if col not in df_test.columns:
        print(f"   ❌ ERROR: Critical column '{col}' is missing from the test set.")
        error_found = True
        found_critical_nan = True # Treat missing column as a NaN problem
        continue
    nan_count = df_test[col].isna().sum()
    if nan_count > 0:
        # Allow NaNs in EUR/PPFD and RANK eur/ppfd as per original data characteristics for some hours/days
        if col in ['EUR/PPFD', 'RANK eur/ppfd']:
            print(f"   ⚠️ INFO: Column '{col}' has {nan_count} NaN values. This might be acceptable if original data also had them.")
        else:
            print(f"   ❌ ERROR: Critical column '{col}' has {nan_count} NaN values.")
            error_found = True
            found_critical_nan = True
if not found_critical_nan:
    print(f"   ✅ SUCCESS: No unexpected NaNs found in strictly critical columns (date, hour, requirements, capacity). EUR/PPFD and RANK might have NaNs as per original data.")

print("\n--- Verification Complete ---")
if error_found:
    print("   ❌ One or more verification checks failed. Please review the errors above.")
else:
    print("   ✅ All verification checks passed successfully! The test set appears to be correct and consistent.") 