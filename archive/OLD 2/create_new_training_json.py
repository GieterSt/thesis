import pandas as pd
import json
import numpy as np
import decimal

# --- Configuration ---
INPUT_EXCEL_FILE = 'New_Training_Set_Seasonal_Split.xlsx'
OUTPUT_JSON_FILE = 'New_LED_Optimization_Training_Data.json'
DECIMAL_PRECISION_DISPLAY = 10 # For display in think block and target_ppfd in prompt
MAX_THINK_STEPS_DISPLAY = 8

# --- Helper Functions (adapted from previous scripts) ---

def get_decimal_context(precision=30):
    ctx = decimal.Context()
    ctx.prec = precision
    return ctx

def format_float_precise(value, precision=DECIMAL_PRECISION_DISPLAY):
    if pd.isna(value) or value is None:
        return "0.0" # Or handle as error/NaN string if preferred
    # Use Decimal for precise intermediate formatting, then format as string
    # This helps control trailing zeros and scientific notation for very small/large numbers
    # if they are not already well-behaved floats.
    # For our purposes, standard float formatting should be fine if inputs are clean.
    return f"{value:.{precision}f}"

def run_optimization(daily_data_df, target_ppfd_total_day):
    # Ensure 'RANK eur/ppfd' is numeric, fill NaNs with a high rank (e.g., 99)
    # and handle potential non-integer ranks by converting to int after fillna
    daily_data_df['RANK eur/ppfd'] = pd.to_numeric(daily_data_df['RANK eur/ppfd'], errors='coerce').fillna(99).astype(int)
    
    # Sort by rank, then by original hour to break ties consistently
    sorted_hours = daily_data_df.sort_values(by=['RANK eur/ppfd', 'hour'])
    
    allocated_ppfd = {hour: decimal.Decimal('0.0') for hour in range(24)}
    remaining_target = decimal.Decimal(str(target_ppfd_total_day)) # Use Decimal for precision
    
    optimization_steps = []

    for _, row in sorted_hours.iterrows():
        hour = int(row['hour'])
        capacity_this_hour_val = row['max_ppfd_to_addumol_m2_s']
        if pd.isna(capacity_this_hour_val):
            capacity_this_hour_val = 0.0
        capacity_this_hour = decimal.Decimal(str(capacity_this_hour_val))
        
        rank = int(row['RANK eur/ppfd'])

        if remaining_target <= decimal.Decimal('0.0'):
            optimization_steps.append(f"Hour {hour} (rank {rank}, capacity {format_float_precise(capacity_this_hour_val)}): Allocation 0.0 PPFD (Target met) → Remaining: {format_float_precise(float(remaining_target))}")
            continue

        can_allocate = min(remaining_target, capacity_this_hour)
        
        if can_allocate > decimal.Decimal('0.0'):
            allocated_ppfd[hour] += can_allocate
            remaining_target -= can_allocate
        
        optimization_steps.append(f"Hour {hour} (rank {rank}, capacity {format_float_precise(capacity_this_hour_val)}): {format_float_precise(float(can_allocate))} PPFD → Remaining: {format_float_precise(float(remaining_target))}")

    total_allocated_sum = sum(allocated_ppfd.values())
    difference = decimal.Decimal(str(target_ppfd_total_day)) - total_allocated_sum
    
    # Clean very small differences
    if abs(difference) < decimal.Decimal('1e-9'): # Threshold for "zero"
        difference = decimal.Decimal('0.0')

    target_met = difference == decimal.Decimal('0.0') # or abs(difference) < threshold

    # Final allocated_ppfd for JSON output should be float strings
    final_allocated_ppfd_float_str = {f"hour_{h}": format_float_precise(float(v)) for h, v in allocated_ppfd.items()}
    
    return final_allocated_ppfd_float_str, float(total_allocated_sum), target_met, optimization_steps, float(difference)

def format_think_block(optimization_steps, target_ppfd, total_allocated, difference, target_met, total_system_capacity_day):
    # Use Decimal for precise calculations involving target_ppfd and total_system_capacity_day if they are not already
    dec_target_ppfd = decimal.Decimal(str(target_ppfd))
    dec_total_system_capacity_day = decimal.Decimal(str(total_system_capacity_day))
    dec_difference = decimal.Decimal(str(difference)) # 'difference' is target - allocated

    think_content = "Available hours: 0-23 (24 total).\\n"
    think_content += f"Maximum possible PPFD allocation for this day: {format_float_precise(float(dec_total_system_capacity_day))} PPFD-hours (sum of hourly capacities).\\n"
    think_content += f"Target PPFD needed: {format_float_precise(float(dec_target_ppfd))} PPFD-hours.\\n"

    if dec_target_ppfd > dec_total_system_capacity_day:
        think_content += "Status: IMPOSSIBLE - Target demand exceeds maximum possible system capacity for the day!\\n"
        if dec_total_system_capacity_day > decimal.Decimal('0.0'):
            factor = dec_target_ppfd / dec_total_system_capacity_day
            think_content += f"Target is approximately {factor:.2f} times the maximum capacity.\\n"
    else:
        think_content += "Status: Potentially Feasible - Target demand is within or equal to maximum system capacity.\\n"
    
    think_content += "\\n1. Sort hours by electricity cost (rank 1 = cheapest):\\n   Details captured in allocation steps below.\\n\\n2. Allocate PPFD to cheapest hours first, respecting hourly capacities:\\n" # Clarified title
    if len(optimization_steps) > MAX_THINK_STEPS_DISPLAY:
        for i in range(MAX_THINK_STEPS_DISPLAY):
            think_content += f"   {optimization_steps[i]}\n"
        think_content += "   ... (further allocation steps not shown to keep summary concise) ...\n"
        # Add the last step for clarity if it's not already shown
        if MAX_THINK_STEPS_DISPLAY < len(optimization_steps):
             think_content += f"   {optimization_steps[-1]}\n"
    else:
        for step in optimization_steps:
            think_content += f"   {step}\n"
    
    think_content += f"\\n3. Result:\\n"
    think_content += f"   Total allocated: {format_float_precise(total_allocated)} PPFD-hours\\n"
    think_content += f"   Target was: {format_float_precise(target_ppfd)} PPFD-hours\\n"
    
    # Report difference (Target - Allocated)
    diff_val_str = format_float_precise(float(dec_difference))
    if dec_difference == decimal.Decimal('0.0') or (abs(dec_difference) < decimal.Decimal('1e-9') and diff_val_str.startswith("0.000000000")): # Effectively zero
        think_content += f"   Outcome: Target achieved precisely (Difference: {diff_val_str}).\\n"
    elif dec_difference > decimal.Decimal('0.0'):
        think_content += f"   Outcome: Shortfall of {diff_val_str} PPFD-hours.\\n"
    else: # difference < 0
        think_content += f"   Outcome: Excess allocation of {format_float_precise(float(abs(dec_difference)))} PPFD-hours (Difference: {diff_val_str}).\\n"
        
    think_content += f"   Target met (strict): {'Yes' if target_met else 'No'}\\n" # target_met is based on difference == 0.0 after 1e-9 cleanup

    return f"<think>\\n{think_content}</think>"

print(f"Starting JSON generation for training data: {INPUT_EXCEL_FILE} -> {OUTPUT_JSON_FILE}")

# --- Main Script ---
try:
    df_source = pd.read_excel(INPUT_EXCEL_FILE)
except FileNotFoundError:
    print(f"❌ ERROR: Input file not found: {INPUT_EXCEL_FILE}")
    exit()

# Ensure 'daily_requirement' is present (it should be as per create_new_seasonal_splits.py)
if 'daily_requirement' not in df_source.columns:
    print(f"❌ ERROR: 'daily_requirement' column is missing from {INPUT_EXCEL_FILE}. This column is needed for 'target_ppfd'.")
    exit()


all_conversations = []
unique_dates = sorted(df_source['date'].unique())
print(f"Found {len(unique_dates)} unique dates to process.")

for i, day_date_np in enumerate(unique_dates):
    day_date = pd.to_datetime(day_date_np)
    date_str = day_date.strftime('%Y-%m-%d')
    
    daily_data_df = df_source[df_source['date'] == day_date].copy() # Use .copy() to avoid SettingWithCopyWarning
    
    if len(daily_data_df) != 24:
        print(f"⚠️ WARNING: Date {date_str} does not have 24 hours of data, found {len(daily_data_df)}. Skipping this day.")
        continue

    # Extract Target PPFD (daily_requirement)
    target_ppfd_total_day = daily_data_df['daily_requirement'].iloc[0]
    if pd.isna(target_ppfd_total_day):
        print(f"⚠️ WARNING: Target PPFD (daily_requirement) is NaN for {date_str}. Using 0.0 and skipping optimization for this day.")
        target_ppfd_total_day = 0.0
        # Create a minimal user prompt for this case, assistant part might be empty or indicate error
        ranks_dict = {f'hour_{h}': 99 for h in range(24)}
        capacity_list_raw = daily_data_df['max_ppfd_to_addumol_m2_s'].fillna(0.0).tolist()
        capacity_dict = {f'hour_{h}': capacity_list_raw[h] for h in range(len(capacity_list_raw))}
        
        # Calculate total system capacity even for NaN target case for think block consistency
        dec_total_system_capacity_day = sum(decimal.Decimal(str(cap)) for cap in capacity_list_raw if not pd.isna(cap))

        assistant_value = f"<think>\\nAvailable hours: 0-23 (24 total).\\n"
        assistant_value += f"Maximum possible PPFD allocation for this day: {format_float_precise(float(dec_total_system_capacity_day))} PPFD-hours (sum of hourly capacities).\\n"
        assistant_value += f"Target PPFD needed: {format_float_precise(target_ppfd_total_day)} PPFD-hours.\\n"
        assistant_value += "Status: ERROR - Target PPFD is NaN. Cannot perform optimization.\\n</think>"

    else:
        # Prepare data for user prompt
        ranks_list = daily_data_df['RANK eur/ppfd'].fillna(99).astype(int).tolist()
        ranks_dict = {f'hour_{h}': ranks_list[h] for h in range(len(ranks_list))}
        
        capacity_list_raw = daily_data_df['max_ppfd_to_addumol_m2_s'].fillna(0.0).tolist()
        capacity_dict = {f'hour_{h}': capacity_list_raw[h] for h in range(len(capacity_list_raw))} # raw floats for precise str() conversion

        # Calculate total system capacity for the day using Decimal for precision
        dec_total_system_capacity_day = sum(decimal.Decimal(str(cap)) for cap in capacity_list_raw if not pd.isna(cap))

        # Run optimization
        schedule, total_allocated, target_met, steps, difference = run_optimization(daily_data_df.copy(), target_ppfd_total_day) # Pass a copy for safety

        # Format assistant response
        think_block = format_think_block(steps, target_ppfd_total_day, total_allocated, difference, target_met, float(dec_total_system_capacity_day)) # Pass total_system_capacity_day
        
        assistant_schedule_json_str = json.dumps({
            "led_schedule": schedule,
            "total_allocated": format_float_precise(total_allocated),
            "target_met": target_met
        }, indent=2).replace("\n", "\\n") # Escape newlines for JSON string

        assistant_value = f"{think_block}\n\nOptimal LED Schedule:\n\n```json\n{assistant_schedule_json_str}\n```"

    # Construct user prompt
    target_ppfd_str_prompt = format_float_precise(target_ppfd_total_day, DECIMAL_PRECISION_DISPLAY)
    ranks_dict_str_prompt = str(ranks_dict)
    capacity_dict_str_prompt = str(capacity_dict) # str() will handle float precision adequately from raw floats

    user_prompt_value = (
        "Optimize LED lighting schedule:\n"
        f"- Total supplemental PPFD-hours needed: {target_ppfd_str_prompt}\n"
        f"- EUR/PPFD rankings by hour: {ranks_dict_str_prompt}\n"
        f"- Max PPFD capacity by hour: {capacity_dict_str_prompt}\n"
        "Allocate PPFD per hour to minimize cost."
    )

    conversation_entry = {
        "from": "user",
        "value": user_prompt_value
    }
    assistant_entry = {
        "from": "assistant",
        "value": assistant_value
    }
    all_conversations.append(conversation_entry)
    all_conversations.append(assistant_entry)

    if (i + 1) % 30 == 0: # Log progress every 30 days
        print(f"   Processed {i + 1}/{len(unique_dates)} days...")

# Final JSON structure (single object with one 'conversations' array)
output_json_data = {"conversations": all_conversations}

try:
    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(output_json_data, f, indent=2)
    print(f"✅ Successfully created JSON training file: {OUTPUT_JSON_FILE}")
    print(f"   Total days processed into JSON: {len(unique_dates)}")
except IOError as e:
    print(f"❌ ERROR: Could not write JSON file: {e}") 