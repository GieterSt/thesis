import pandas as pd
import json
import numpy as np

# --- Configuration ---
TEST_SET_EXCEL_FILE = 'Stratified_Test_Set_Solar_Price_Seasonal.xlsx'
OUTPUT_JSON_FILE = 'LED_Optimization_Test_Inputs.json'
DECIMAL_PRECISION_FLOAT = 10

print(f"Starting conversion of {TEST_SET_EXCEL_FILE} to {OUTPUT_JSON_FILE}...")

# --- 1. Load Data ---
try:
    df_test_set = pd.read_excel(TEST_SET_EXCEL_FILE)
except FileNotFoundError:
    print(f"❌ ERROR: Input file not found: {TEST_SET_EXCEL_FILE}")
    exit()

# --- 2. Prepare Data ---
df_test_set['date'] = pd.to_datetime(df_test_set['date'])

# Ensure required columns are present
required_columns = ['date', 'hour', 'daily_requirement', 'RANK eur/ppfd', 'max_ppfd_to_addumol_m2_s']
missing_columns = [col for col in required_columns if col not in df_test_set.columns]
if missing_columns:
    print(f"❌ ERROR: Missing required columns in the Excel file: {', '.join(missing_columns)}")
    exit()

all_test_cases_json = []
unique_dates = sorted(df_test_set['date'].unique())

print(f"Found {len(unique_dates)} unique dates to process.")

# --- 3. Process Each Day ---
for i, day_date in enumerate(unique_dates):
    day_data = df_test_set[df_test_set['date'] == day_date].sort_values(by='hour')

    if len(day_data) != 24:
        print(f"⚠️ WARNING: Date {day_date.strftime('%Y-%m-%d')} does not have 24 hours of data, found {len(day_data)}. Skipping this day.")
        continue

    date_str = day_date.strftime('%Y-%m-%d')

    # Extract Target PPFD (daily_requirement)
    # daily_requirement should be the same for all hours of the day
    target_ppfd = day_data['daily_requirement'].iloc[0]
    if pd.isna(target_ppfd):
        print(f"⚠️ WARNING: Target PPFD (daily_requirement) is NaN for {date_str}. Using 0.0.")
        target_ppfd = 0.0
    target_ppfd_str = f"{target_ppfd:.{DECIMAL_PRECISION_FLOAT}f}"

    # Extract Hourly Ranks
    # Fill NaN ranks with 99 and convert to int
    ranks_list = day_data['RANK eur/ppfd'].fillna(99).astype(int).tolist()
    # ranks_list_str = str(ranks_list) # Standard list string representation: [1, 2, 3]
    ranks_dict = {f'hour_{h}': ranks_list[h] for h in range(len(ranks_list))}
    ranks_dict_str = str(ranks_dict)

    # Extract Hourly Capacity
    # Fill NaN capacities with 0.0
    capacity_list_raw = day_data['max_ppfd_to_addumol_m2_s'].fillna(0.0).tolist()
    # capacity_list_str = f"[{\', \'.join(f\'{c:.{DECIMAL_PRECISION_FLOAT}f}\' for c in capacity_list_raw)}]"
    capacity_dict = {f'hour_{h}': capacity_list_raw[h] for h in range(len(capacity_list_raw))} # Using raw floats
    capacity_dict_str = str(capacity_dict)

    # --- 4. Construct JSON Structure ---
    # user_prompt_value = (
    #     f"Please optimize LED usage for {date_str}. "
    #     f"Target PPFD: {target_ppfd_str}, "
    #     f"Hourly Ranks: {ranks_list_str}, "
    #     f"Hourly Capacity: {capacity_list_str}"
    # )

    user_prompt_value = (
        "Optimize LED lighting schedule:\\n"
        f"- Total supplemental PPFD-hours needed: {target_ppfd_str}\\n"
        f"- EUR/PPFD rankings by hour: {ranks_dict_str}\\n"
        f"- Max PPFD capacity by hour: {capacity_dict_str}\\n"
        "Allocate PPFD per hour to minimize cost."
    )

    conversation_entry = {
        "conversations": [
            {
                "from": "user",
                "value": user_prompt_value
            },
            {
                "from": "assistant",
                "value": "" # Placeholder for model's output
            }
        ]
    }
    all_test_cases_json.append(conversation_entry)
    if (i + 1) % 10 == 0:
        print(f"Processed {i+1}/{len(unique_dates)} days...")


# --- 5. Save JSON ---
try:
    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(all_test_cases_json, f, indent=2)
    print(f"✅ Successfully created JSON test input file: {OUTPUT_JSON_FILE}")
    print(f"Total test cases generated: {len(all_test_cases_json)}")
except IOError as e:
    print(f"❌ ERROR: Could not write JSON file: {e}") 