import pandas as pd
import json
import re
import numpy as np

# --- Configuration ---
TRAINING_EXCEL_FILE = 'New_Training_Set_Seasonal_Split.xlsx'
TRAINING_JSON_FILE = 'New_LED_Optimization_Training_Data.json'

print(f"=== Checking PPFD Requirements in Training Data ===")

# --- 1. Analyze daily_requirement from Excel --- 
print(f"\n1. Analyzing '{TRAINING_EXCEL_FILE}'...")
try:
    df_excel = pd.read_excel(TRAINING_EXCEL_FILE)
except FileNotFoundError:
    print(f"   ❌ ERROR: Excel file not found: {TRAINING_EXCEL_FILE}")
    exit()

if 'daily_requirement' not in df_excel.columns:
    print(f"   ❌ ERROR: 'daily_requirement' column not found in {TRAINING_EXCEL_FILE}")
    excel_requirements = None
else:
    # Get unique daily requirements as each day has one value, repeated 24 times
    excel_requirements = df_excel.drop_duplicates(subset=['date'])['daily_requirement'].copy()
    excel_requirements.dropna(inplace=True) # Remove NaNs if any before stats

    if not excel_requirements.empty:
        print(f"   Found {len(excel_requirements)} unique daily_requirement values in Excel.")
        print(f"   Stats for 'daily_requirement' from Excel ({len(excel_requirements)} days):")
        print(f"     Min:    {excel_requirements.min():.4f}")
        print(f"     Max:    {excel_requirements.max():.4f}")
        print(f"     Mean:   {excel_requirements.mean():.4f}")
        print(f"     Median: {excel_requirements.median():.4f}")
        print(f"     Std Dev:{excel_requirements.std():.4f}")
        print(f"     90th Pctl: {excel_requirements.quantile(0.90):.4f}")
        print(f"     95th Pctl: {excel_requirements.quantile(0.95):.4f}")
        print(f"     99th Pctl: {excel_requirements.quantile(0.99):.4f}")
        # Check for NaNs that might have been missed or appeared if all were NaN
        if df_excel['daily_requirement'].isnull().any():
            print(f"     WARNING: Original 'daily_requirement' column in Excel contains {df_excel['daily_requirement'].isnull().sum()} NaN values.") 
    else:
        print("   No valid daily_requirement values found in Excel after dropping NaNs.")
        excel_requirements = None

# --- 2. Analyze PPFD requirements from JSON --- 
print(f"\n2. Analyzing '{TRAINING_JSON_FILE}'...")
json_ppfd_values = []
parsing_errors = 0
nan_values_in_json_prompt = 0

try:
    with open(TRAINING_JSON_FILE, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"   ❌ ERROR: JSON file not found: {TRAINING_JSON_FILE}")
    exit()
except json.JSONDecodeError:
    print(f"   ❌ ERROR: Could not decode JSON file: {TRAINING_JSON_FILE}")
    exit()

conversations = data.get("conversations", [])
if not conversations or len(conversations) % 2 != 0:
    print(f"   ❌ ERROR: 'conversations' array is missing, empty, or has an odd number of entries in JSON.")
    exit()

# Regex to extract the PPFD value
ppfd_pattern = re.compile(r"- Total supplemental PPFD-hours needed: ([-+]?\d*\.?\d+)")

num_user_prompts = 0
for i in range(0, len(conversations), 2): # Process user prompts
    if conversations[i]["from"] == "user":
        num_user_prompts += 1
        prompt_text = conversations[i]["value"]
        match = ppfd_pattern.search(prompt_text)
        if match:
            try:
                val_str = match.group(1)
                val = float(val_str)
                if np.isnan(val):
                    nan_values_in_json_prompt += 1
                else:
                    json_ppfd_values.append(val)
            except ValueError:
                print(f"   ⚠️ WARNING: Could not convert value '{match.group(1)}' to float from prompt: {prompt_text[:100]}...")
                parsing_errors += 1
        else:
            print(f"   ⚠️ WARNING: Could not find PPFD requirement pattern in user prompt: {prompt_text[:100]}...")
            parsing_errors += 1
    else:
        print(f"   ⚠️ WARNING: Expected a 'user' prompt at index {i}, but found '{conversations[i]['from']}'.")
        # This would indicate a structural issue with the JSON conversation pairs

print(f"   Processed {num_user_prompts} user prompts from JSON.")
if nan_values_in_json_prompt > 0:
    print(f"   ⚠️ WARNING: Found {nan_values_in_json_prompt} NaN values for PPFD in JSON prompts.")
if parsing_errors > 0:
    print(f"   ❌ Found {parsing_errors} parsing errors for PPFD values in JSON prompts.")

if json_ppfd_values:
    json_ppfd_series = pd.Series(json_ppfd_values)
    print(f"   Stats for 'Total supplemental PPFD-hours needed' from JSON ({len(json_ppfd_series)} values):")
    print(f"     Min:    {json_ppfd_series.min():.4f}")
    print(f"     Max:    {json_ppfd_series.max():.4f}")
    print(f"     Mean:   {json_ppfd_series.mean():.4f}")
    print(f"     Median: {json_ppfd_series.median():.4f}")
    print(f"     Std Dev:{json_ppfd_series.std():.4f}")
    print(f"     90th Pctl: {json_ppfd_series.quantile(0.90):.4f}")
    print(f"     95th Pctl: {json_ppfd_series.quantile(0.95):.4f}")
    print(f"     99th Pctl: {json_ppfd_series.quantile(0.99):.4f}")
else:
    print("   No valid PPFD requirement values extracted from JSON.")

print("\n=== Check Complete ===")

# --- Interpretation of "Extremely Large" ---
# Based on earlier thoughts: total_supplemental_ppfd_requirement_umol_m2_s_h (hourly need)
# If max hourly need is ~300-400 umol/m2/s, then daily sum (daily_requirement) for 24h is 300*24 = 7200 or 400*24 = 9600.
# Values above this, e.g., > 10000, might warrant closer inspection. 
# The stats above (especially Max and 99th percentile) will show if we are in this territory. 