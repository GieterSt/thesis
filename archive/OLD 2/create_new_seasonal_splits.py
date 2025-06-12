import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np

# --- Configuration ---
COMPLETE_DATA_FILE = 'Complete_Merged_Dataset_2024_2025.xlsx'
TRAIN_SET_FILE = 'New_Training_Set_Seasonal_Split.xlsx'
VALIDATION_SET_FILE = 'New_Validation_Set_Seasonal_Split.xlsx'
TEST_SET_FILE = 'New_Test_Set_Seasonal_Split.xlsx'

RANDOM_STATE = 42
TEST_SET_RATIO = 0.10
VALIDATION_SET_RATIO_OF_REMAINDER = 0.20 / (1.0 - TEST_SET_RATIO) # e.g. 0.20 / 0.90

print("=== Starting New 70/20/10 Seasonal Data Split ===")

# --- 1. Load and Prepare Data ---
print(f"1. Loading dataset: {COMPLETE_DATA_FILE}...")
try:
    df_complete = pd.read_excel(COMPLETE_DATA_FILE)
except FileNotFoundError:
    print(f"   ❌ ERROR: Could not find input file: {COMPLETE_DATA_FILE}")
    exit()

df_complete['date'] = pd.to_datetime(df_complete['date'])
print(f"   Dataset loaded. Total records: {len(df_complete)}")

# Identify Usable Days (those with 24 hours of records)
print("\n2. Identifying usable days (with 24 hourly records)...")
hour_counts_per_day = df_complete.groupby(df_complete['date'].dt.date)['hour'].count()
usable_dates_series = hour_counts_per_day[hour_counts_per_day == 24].index
usable_dates = [pd.to_datetime(date_obj) for date_obj in usable_dates_series]

if not usable_dates:
    print("   ❌ ERROR: No usable days with 24 hourly records found. Cannot proceed.")
    exit()

N_usable_days = len(usable_dates)
print(f"   Found {N_usable_days} unique usable days with 24 hourly records.")

# --- 3. Define Seasons (Quarters) and Assign to Usable Days ---
print("\n3. Assigning seasons (quarters) and pre-calculating daily metrics...")

# Pre-calculate daily metrics for all usable days
daily_metrics_list = []
for date_val in usable_dates:
    day_data = df_complete[df_complete['date'].dt.date == date_val.date()]
    avg_price_day = day_data['EUR/PPFD'].mean() # Can be NaN if all EUR/PPFD are NaN for the day
    daily_req = day_data['total_supplemental_ppfd_requirement_umol_m2_s_h'].sum() # Sum of hourly requirements
    daily_metrics_list.append({
        'date': date_val,
        'avg_price': avg_price_day,
        'daily_requirement': daily_req
    })
df_daily_metrics = pd.DataFrame(daily_metrics_list)

def assign_quarter(date_obj):
    year = date_obj.year
    month = date_obj.month
    if year == 2024:
        if 1 <= month <= 3: return 'Q1_2024'
        elif 4 <= month <= 6: return 'Q2_2024'
        elif 7 <= month <= 9: return 'Q3_2024'
        elif 10 <= month <= 12: return 'Q4_2024'
    elif year == 2025:
        if 1 <= month <= 3: return 'Q1_2025'
        elif 4 <= month <= 6: return 'Q2_2025' # Covers April 1-15
    return 'Unknown'

usab_dates_df = pd.DataFrame({'date': usable_dates})
usab_dates_df['quarter'] = usab_dates_df['date'].apply(assign_quarter)

# Merge pre-calculated daily metrics into usab_dates_df
usab_dates_df = pd.merge(usab_dates_df, df_daily_metrics, on='date', how='left')

# Check if daily_requirement is now in usab_dates_df
if 'daily_requirement' not in usab_dates_df.columns:
    print("   ❌ ERROR: 'daily_requirement' column failed to merge into usable dates dataframe.")
    exit()
else:
    print("   ✅ 'daily_requirement' and other daily metrics merged into usable dates dataframe.")

print("   Distribution of usable days per quarter:")
print(usab_dates_df['quarter'].value_counts().sort_index())

# --- 4. Stratified Data Splitting ---
print("\n4. Performing stratified split (70% train, 20% validation, 10% test)..." )

# Step 1: Split out Test set
intermediate_df, test_df = train_test_split(
    usab_dates_df,
    test_size=TEST_SET_RATIO,
    stratify=usab_dates_df['quarter'],
    random_state=RANDOM_STATE
)

# Step 2: Split out Validation set from the remainder
train_df, validation_df = train_test_split(
    intermediate_df,
    test_size=VALIDATION_SET_RATIO_OF_REMAINDER,
    stratify=intermediate_df['quarter'],
    random_state=RANDOM_STATE
)

train_dates = set(train_df['date'])
validation_dates = set(validation_df['date'])
test_dates = set(test_df['date'])

# --- 5. Verification ---
print("\n5. Verifying split...")
print(f"   Training set: {len(train_dates)} days")
print(f"   Validation set: {len(validation_dates)} days")
print(f"   Test set: {len(test_dates)} days")
print(f"   Total assigned days: {len(train_dates) + len(validation_dates) + len(test_dates)} (should be {N_usable_days})")

# Check for overlaps
overlap_train_val = train_dates.intersection(validation_dates)
overlap_train_test = train_dates.intersection(test_dates)
overlap_val_test = validation_dates.intersection(test_dates)
if overlap_train_val or overlap_train_test or overlap_val_test:
    print("   ❌ ERROR: Overlap found between datasets!")
    if overlap_train_val: print(f"      Train-Val overlap: {len(overlap_train_val)} days")
    if overlap_train_test: print(f"      Train-Test overlap: {len(overlap_train_test)} days")
    if overlap_val_test: print(f"      Val-Test overlap: {len(overlap_val_test)} days")
else:
    print("   ✅ SUCCESS: No overlaps found between datasets.")

print("\n   Seasonal distribution in Training Set:")
print(train_df['quarter'].value_counts().sort_index())
print("\n   Seasonal distribution in Validation Set:")
print(validation_df['quarter'].value_counts().sort_index())
print("\n   Seasonal distribution in Test Set:")
print(test_df['quarter'].value_counts().sort_index())

# --- 6. Create and Save Output Files ---
print("\n6. Creating and saving output Excel files...")

def create_output_file(dates_set, quarter_df, original_df, filename):
    set_dates_with_quarters = quarter_df[quarter_df['date'].isin(dates_set)]
    # Filter the original complete dataframe for these dates
    output_df = original_df[original_df['date'].isin(set_dates_with_quarters['date'])]
    # Merge quarter information (and now also daily_requirement etc. that are in set_dates_with_quarters)
    # output_df = pd.merge(output_df, set_dates_with_quarters, on='date', how='left')
    # The necessary columns like 'quarter' and 'daily_requirement' are already in set_dates_with_quarters
    # We need to merge these from set_dates_with_quarters to output_df, ensuring we don't duplicate 'hour' or other hourly columns
    
    # Select only the daily-level columns from set_dates_with_quarters to merge
    daily_cols_to_merge = ['date', 'quarter', 'avg_price', 'daily_requirement'] # Add any other daily metrics needed
    # Ensure these columns actually exist in set_dates_with_quarters
    daily_cols_present = [col for col in daily_cols_to_merge if col in set_dates_with_quarters.columns]

    output_df = pd.merge(output_df, set_dates_with_quarters[daily_cols_present], on='date', how='left')

    # Reorder columns to have 'date', 'hour', 'quarter', 'daily_requirement' first if they exist
    cols = list(output_df.columns)
    preferred_order = ['date', 'hour', 'quarter', 'daily_requirement', 'avg_price']
    new_order = [col for col in preferred_order if col in cols] + [col for col in cols if col not in preferred_order]
    output_df = output_df[new_order]
    
    output_df.to_excel(filename, index=False)
    print(f"   ✅ Saved {filename} with {len(output_df)} records ({len(dates_set)} days).")

# Create a combined DataFrame of all dates with their assigned quarters for easier merging
all_assigned_dates_quarters_df = pd.concat([train_df, validation_df, test_df])

create_output_file(train_dates, all_assigned_dates_quarters_df, df_complete, TRAIN_SET_FILE)
create_output_file(validation_dates, all_assigned_dates_quarters_df, df_complete, VALIDATION_SET_FILE)
create_output_file(test_dates, all_assigned_dates_quarters_df, df_complete, TEST_SET_FILE)

print("\n=== Data Splitting Process Complete ===") 