import pandas as pd
import json
import numpy as np
import decimal

# --- Configuration ---
INPUT_EXCEL_FILE = 'New_Test_Set_Seasonal_Split.xlsx' # Changed
OUTPUT_JSON_FILE = 'New_LED_Optimization_Test_Inputs.json' # Changed
DECIMAL_PRECISION_DISPLAY = 10

def format_float_precise(value, precision=DECIMAL_PRECISION_DISPLAY):
    if pd.isna(value) or value is None:
        return "0.0"
    return f"{value:.{precision}f}"

print(f"Starting JSON generation for test inputs: {INPUT_EXCEL_FILE} -> {OUTPUT_JSON_FILE}") # Changed

# --- Main Script ---
try:
    df_source = pd.read_excel(INPUT_EXCEL_FILE)
except FileNotFoundError:
    print(f"❌ ERROR: Input file not found: {INPUT_EXCEL_FILE}")
    exit()

if 'daily_requirement' not in df_source.columns:
    print(f"❌ ERROR: 'daily_requirement' column is missing from {INPUT_EXCEL_FILE}.")
    exit()

all_conversations = []
unique_dates = sorted(df_source['date'].unique())
print(f"Found {len(unique_dates)} unique dates to process.")

for i, day_date_np in enumerate(unique_dates):
    day_date = pd.to_datetime(day_date_np)
    date_str = day_date.strftime('%Y-%m-%d')
    daily_data_df = df_source[df_source['date'] == day_date].copy()
    
    if len(daily_data_df) != 24:
        print(f"⚠️ WARNING: Date {date_str} does not have 24 hours of data, found {len(daily_data_df)}. Skipping this day.")
        continue

    target_ppfd_total_day = daily_data_df['daily_requirement'].iloc[0]
    if pd.isna(target_ppfd_total_day):
        print(f"⚠️ WARNING: Target PPFD (daily_requirement) is NaN for {date_str}. Using 0.0.")
        target_ppfd_total_day = 0.0
    
    ranks_list = daily_data_df['RANK eur/ppfd'].fillna(99).astype(int).tolist()
    ranks_dict = {f'hour_{h}': ranks_list[h] for h in range(len(ranks_list))}
    
    capacity_list_raw = daily_data_df['max_ppfd_to_addumol_m2_s'].fillna(0.0).tolist()
    # Ensure capacity_dict uses precise string representation of floats later
    capacity_dict = {f'hour_{h}': capacity_list_raw[h] for h in range(len(capacity_list_raw))}

    target_ppfd_str_prompt = format_float_precise(target_ppfd_total_day, DECIMAL_PRECISION_DISPLAY)
    ranks_dict_str_prompt = str(ranks_dict) 
    capacity_dict_str_prompt = str(capacity_dict) # str() should be fine here

    user_prompt_value = (
        "Optimize LED lighting schedule:\n"
        f"- Total supplemental PPFD-hours needed: {target_ppfd_str_prompt}\n"
        f"- EUR/PPFD rankings by hour: {ranks_dict_str_prompt}\n"
        f"- Max PPFD capacity by hour: {capacity_dict_str_prompt}\n"
        "Allocate PPFD per hour to minimize cost."
    )

    # For test inputs, the assistant's response is typically empty or a placeholder
    # as these are inputs for the model to generate a response for.
    assistant_value = "" 

    conversation_entry = {"from": "user", "value": user_prompt_value}
    assistant_entry = {"from": "assistant", "value": assistant_value}
    all_conversations.append(conversation_entry)
    all_conversations.append(assistant_entry)

    if (i + 1) % 10 == 0: # Log progress
        print(f"   Processed {i + 1}/{len(unique_dates)} days...")

output_json_data = {"conversations": all_conversations}

try:
    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(output_json_data, f, indent=2)
    print(f"✅ Successfully created JSON test input file: {OUTPUT_JSON_FILE}") # Changed
    print(f"   Total days processed into JSON: {len(unique_dates)}")
except IOError as e:
    print(f"❌ ERROR: Could not write JSON file: {e}") 