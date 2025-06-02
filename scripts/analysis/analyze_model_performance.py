import json
import pandas as pd
import re
import numpy as np
from scipy.stats import ttest_rel # Added for paired t-test
from datetime import datetime # Added for date parsing

# --- Configuration ---
MODEL_RESULTS_FILE = 'meta-llama_llama-3.3-70b-instruct_free_results_v3_prompt.json' # Updated for Llama 3.3 V3 results
GROUND_TRUTH_FILE = 'test_set_ground_truth_complete.xlsx'

# Extract model name and suffix for the summary/comparison files
model_name_base = ""
if "_results_v3_prompt.json" in MODEL_RESULTS_FILE:
    model_name_base = MODEL_RESULTS_FILE.replace("_results_v3_prompt.json", "")
elif "_results_v2_prompt.json" in MODEL_RESULTS_FILE:
    model_name_base = MODEL_RESULTS_FILE.replace("_results_v2_prompt.json", "")
else:
    model_name_base = MODEL_RESULTS_FILE.replace("_results.json", "")

v2_suffix = "" # Re-evaluate suffix based on the new MODEL_RESULTS_FILE
if "_v2_prompt.json" in MODEL_RESULTS_FILE:
    v2_suffix = "_v2_prompt"
elif "_v3_prompt.json" in MODEL_RESULTS_FILE:
    v2_suffix = "_v3_prompt"

COMPARISON_OUTPUT_EXCEL_FILE = f'comparison_{model_name_base}{v2_suffix}_vs_ground_truth.xlsx'
ANALYSIS_SUMMARY_JSON_FILE = f'analysis_summary_{model_name_base}{v2_suffix}.json'
MODEL_NAME_FOR_SUMMARY = f"{model_name_base}{v2_suffix}"

def extract_date_from_prompt(prompt_text):
    """Extracts the date from the user prompt string."""
    if not prompt_text or not isinstance(prompt_text, str):
        return "UnknownDate"
    match = re.search(r"Context Dump:\nDate: (\d{4}-\d{2}-\d{2})", prompt_text)
    if match:
        return match.group(1)
    else:
        match_fallback = re.search(r"Date: (\d{4}-\d{2}-\d{2})", prompt_text)
        if match_fallback:
            return match_fallback.group(1)
    return "UnknownDate"

def main():
    # --- 1. Load Model Results & Calculate JSON Success Rate ---
    try:
        with open(MODEL_RESULTS_FILE, 'r', encoding='utf-8') as f:
            model_results_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: Model results file '{MODEL_RESULTS_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{MODEL_RESULTS_FILE}'.")
        return

    valid_json_output_count = 0
    total_items = len(model_results_json)
    model_allocations_list = []

    print(f"Processing {total_items} items from '{MODEL_RESULTS_FILE}'...")

    for item_index, result_item in enumerate(model_results_json):
        item_num = result_item.get("item_index", item_index + 1)
        prompt = result_item.get("original_user_prompt")
        date_str = extract_date_from_prompt(prompt)
        model_response_raw = result_item.get("openrouter_model_response")
        
        hourly_allocations_dict = None
        is_valid_json_for_allocation = False

        if isinstance(model_response_raw, str):
            try:
                parsed_response = json.loads(model_response_raw)
                if isinstance(parsed_response, dict):
                    # Check for primary and alternative key names
                    if "allocation_PPFD_per_hour" in parsed_response:
                        hourly_allocations_dict = parsed_response.get("allocation_PPFD_per_hour")
                    elif "allocation PPFD_per_hour" in parsed_response: # Alternative key
                        hourly_allocations_dict = parsed_response.get("allocation PPFD_per_hour")
                    
                    if hourly_allocations_dict is not None and isinstance(hourly_allocations_dict, dict):
                         valid_json_output_count += 1
                         is_valid_json_for_allocation = True
            except json.JSONDecodeError:
                pass # Will be handled by hourly_allocations_dict remaining None
        elif isinstance(model_response_raw, dict):
            # Check for primary and alternative key names
            if "allocation_PPFD_per_hour" in model_response_raw:
                hourly_allocations_dict = model_response_raw.get("allocation_PPFD_per_hour")
            elif "allocation PPFD_per_hour" in model_response_raw: # Alternative key
                hourly_allocations_dict = model_response_raw.get("allocation PPFD_per_hour")

            if hourly_allocations_dict is not None and isinstance(hourly_allocations_dict, dict):
                valid_json_output_count += 1
                is_valid_json_for_allocation = True

        for hour in range(24):
            hour_key = f"hour_{hour}"
            ppfd_value = None
            if is_valid_json_for_allocation and hourly_allocations_dict:
                raw_val = hourly_allocations_dict.get(hour_key)
                if raw_val is not None:
                    try:
                        ppfd_value = float(raw_val)
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert model PPFD value '{raw_val}' to float for item {item_num}, date {date_str}, hour {hour_key}.")
                        ppfd_value = np.nan # Use NaN for unconvertible values
                else: # missing hour key in allocation
                    ppfd_value = np.nan


            model_allocations_list.append({
                'date': date_str,
                'hour': hour,
                'ppfd_allocated_by_model': ppfd_value
            })
            
    model_allocations_df = pd.DataFrame(model_allocations_list)
    model_allocations_df['hour'] = model_allocations_df['hour'].astype(int)
    # Ensure date is string for merging, or convert both to datetime
    model_allocations_df['date'] = model_allocations_df['date'].astype(str)


    # --- 2. Load Ground Truth Data ---
    try:
        ground_truth_df_raw = pd.read_excel(GROUND_TRUTH_FILE)
    except FileNotFoundError:
        print(f"Error: Ground truth file '{GROUND_TRUTH_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading {GROUND_TRUTH_FILE}: {e}")
        return
        
    # Define columns to keep for the ground truth, including the EUR/PPFD column
    # The user specified the column name as 'EUR/PPFD'
    EUR_PPFD_COL_NAME = 'EUR/PPFD' # Using the name from the provided image
    gt_cols_to_keep = [
        'date', 'hour', 'ppfd_allocated', 
        EUR_PPFD_COL_NAME
    ]

    # Check if these columns exist in the raw ground truth data
    missing_cols = [col for col in gt_cols_to_keep if col not in ground_truth_df_raw.columns]
    if missing_cols:
        print(f"Error: The following required columns for cost calculation are missing in {GROUND_TRUTH_FILE}: {missing_cols}")
        print(f"Available columns are: {ground_truth_df_raw.columns.tolist()}")
        # Attempt to find a similar column if the exact EUR/PPFD is missing
        potential_eur_ppfd_cols = [col for col in ground_truth_df_raw.columns if 'EUR' in col.upper() and 'PPFD' in col.upper()]
        if potential_eur_ppfd_cols:
            print(f"Found potential alternative EUR/PPFD columns: {potential_eur_ppfd_cols}. Please verify and update script.")
        return
        
    ground_truth_df = ground_truth_df_raw[gt_cols_to_keep].copy()
    ground_truth_df.rename(columns={'ppfd_allocated': 'ppfd_allocated_ground_truth'}, inplace=True)
    
    # Ensure EUR/PPFD is numeric, coercing errors to NaN
    ground_truth_df[EUR_PPFD_COL_NAME] = pd.to_numeric(ground_truth_df[EUR_PPFD_COL_NAME], errors='coerce')

    # Ensure date is string 'YYYY-MM-DD' and hour is int for merging
    if pd.api.types.is_datetime64_any_dtype(ground_truth_df['date']):
        ground_truth_df['date'] = ground_truth_df['date'].dt.strftime('%Y-%m-%d')
    else: # If it's already string, try to ensure format or handle potential errors
        try:
            ground_truth_df['date'] = pd.to_datetime(ground_truth_df['date']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Warning: Could not parse dates in ground truth to YYYY-MM-DD. Merge might fail or be incorrect: {e}")
            ground_truth_df['date'] = ground_truth_df['date'].astype(str) # Fallback to string
            
    ground_truth_df['hour'] = ground_truth_df['hour'].astype(int)

    print("\n--- Debug: Ground Truth DF Info ---")
    print(f"Ground truth DF shape: {ground_truth_df.shape}")
    print(f"Ground truth DF head:\n{ground_truth_df.head()}")
    print(f"Ground truth DF unique dates (first 5): {ground_truth_df['date'].unique()[:5]}")
    print(f"Ground truth DF data types:\n{ground_truth_df.dtypes}")

    print("\n--- Debug: Model Allocations DF Info ---")
    print(f"Model allocations DF shape: {model_allocations_df.shape}")
    print(f"Model allocations DF head:\n{model_allocations_df.head()}")
    print(f"Model allocations DF unique dates (first 5): {model_allocations_df['date'].unique()[:5]}")
    print(f"Model allocations DF data types:\n{model_allocations_df.dtypes}")

    # --- 3. Merge Model and Ground Truth ---
    comparison_df = pd.merge(model_allocations_df, ground_truth_df, on=['date', 'hour'], how='left')

    print("\n--- Debug: Comparison DF Info (Post-Merge) ---")
    print(f"Comparison DF shape: {comparison_df.shape}")
    print(f"Comparison DF head:\n{comparison_df.head()}")
    print(f"Number of rows with non-NaN ground truth: {comparison_df['ppfd_allocated_ground_truth'].notna().sum()}")

    # --- Derive Season from Date for Seasonal Analysis ---
    def get_season(date_val):
        if pd.isna(date_val):
            return None
        try:
            # Ensure date_val is a datetime object if it's a string
            if isinstance(date_val, str):
                date_obj = pd.to_datetime(date_val).date() # Convert to standard Python date
            elif hasattr(date_val, 'month'): # covers datetime.date and pd.Timestamp
                date_obj = date_val
            else:
                return None # Cannot determine month

            month = date_obj.month
            if month in [12, 1, 2]:
                return "Winter"
            elif month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            elif month in [9, 10, 11]:
                return "Autumn"
            else:
                return None # Should not happen
        except Exception as e:
            print(f"Warning: Could not derive season for date {date_val}: {e}")
            return None

    # Ensure the 'date' column in comparison_df is in datetime format for season derivation
    try:
        comparison_df['date_dt'] = pd.to_datetime(comparison_df['date'])
        comparison_df['season'] = comparison_df['date_dt'].apply(get_season)
    except Exception as e:
        print(f"Error converting comparison_df['date'] to datetime or applying get_season: {e}")
        print("Skipping seasonal analysis due to date conversion issues.")
        comparison_df['season'] = None # Ensure column exists to prevent downstream errors

    # --- 4. Perform Correspondence Analysis ---
    # Ensure numeric types for comparison and calculations
    comparison_df['ppfd_allocated_by_model'] = pd.to_numeric(comparison_df['ppfd_allocated_by_model'], errors='coerce')
    comparison_df['ppfd_allocated_ground_truth'] = pd.to_numeric(comparison_df['ppfd_allocated_ground_truth'], errors='coerce')

    # Ensure EUR/PPFD column is numeric in comparison_df as well after merge and fillna for safety before calculations
    if EUR_PPFD_COL_NAME in comparison_df.columns:
        comparison_df[EUR_PPFD_COL_NAME] = pd.to_numeric(comparison_df[EUR_PPFD_COL_NAME], errors='coerce')
    else:
        print(f"Error: '{EUR_PPFD_COL_NAME}' column missing from comparison_df after merge. Check merge logic.")
        return

    # Exact Hourly Matches (using np.isclose for float comparison)
    # Fill NaN with a value that won't match (e.g. -np.inf) or handle NaNs before comparison if isclose doesn't like them.
    # np.isclose handles NaNs by returning False if one is NaN and the other isn't. If both are NaN, it's True.
    # We want a match only if both are non-NaN and close.
    
    # Create a mask for valid (non-NaN) pairs for comparison
    valid_model_data = comparison_df['ppfd_allocated_by_model'].notna()
    valid_ground_truth_data = comparison_df['ppfd_allocated_ground_truth'].notna()
    both_valid = valid_model_data & valid_ground_truth_data
    
    comparison_df['exact_match'] = False # Initialize column
    comparison_df.loc[both_valid, 'exact_match'] = np.isclose(
        comparison_df.loc[both_valid, 'ppfd_allocated_by_model'],
        comparison_df.loc[both_valid, 'ppfd_allocated_ground_truth']
    )
    
    num_exact_hourly_matches = comparison_df['exact_match'].sum()
    # Total entries for percentage should be where ground truth is available for a fair comparison
    total_hourly_comparisons = len(comparison_df[comparison_df['ppfd_allocated_ground_truth'].notna()])


    percentage_exact_hourly_matches = (num_exact_hourly_matches / total_hourly_comparisons) * 100 if total_hourly_comparisons > 0 else 0

    # Exact Daily Matches
    num_exact_daily_matches = 0
    total_days_in_comparison = 0
    if not comparison_df.empty and 'date' in comparison_df.columns:
        daily_match_check = comparison_df.groupby('date').apply(
            lambda x: x['exact_match'].all() if x['ppfd_allocated_ground_truth'].notna().all() and len(x) == 24 else False
        )
        num_exact_daily_matches = daily_match_check.sum()
        total_days_in_comparison = daily_match_check.count() # Counts days where ground truth for all 24h was available
    
    percentage_exact_daily_matches = (num_exact_daily_matches / total_days_in_comparison) * 100 if total_days_in_comparison > 0 else 0

    # Error Metrics (MAE and RMSE)
    # Use only rows where both model and ground truth have valid numeric data
    # The 'both_valid' mask already identifies these rows.
    
    mae = np.nan
    rmse = np.nan
    if both_valid.sum() > 0:
        errors = comparison_df.loc[both_valid, 'ppfd_allocated_by_model'] - comparison_df.loc[both_valid, 'ppfd_allocated_ground_truth']
        mae = errors.abs().mean()
        rmse = np.sqrt((errors**2).mean())

    # Calculate Daily Total PPFD MAE
    daily_total_ppfd_mae = np.nan
    if not comparison_df.empty:
        # Group by date and sum PPFD for model and ground truth
        # Ensure we only sum where both model and ground truth are valid for that hour
        # Create columns for daily sums, initialize with NaN
        daily_sums = comparison_df[both_valid].groupby('date').agg(
            daily_model_ppfd_sum=('ppfd_allocated_by_model', 'sum'),
            daily_ground_truth_ppfd_sum=('ppfd_allocated_ground_truth', 'sum'),
            valid_hours_count=('ppfd_allocated_by_model', 'count') # Count of hours with valid data for the day
        ).reset_index()

        # We only want to compare days where all 24 hours of ground truth were available
        # and the model also provided data for those 24 hours.
        # The 'both_valid' mask at hourly level handles this implicitly when summing.
        # If a day has fewer than 24 valid_hours_count, it means some original data was missing.
        # However, the prompt asks the model to allocate a *specific total*. The ground truth also reflects this.
        # So, we sum what we have for each day from both sources.
        
        # Filter for days where ground truth sum is not zero (to avoid division by zero if calculating relative errors later)
        # and model sum is also available (though 'both_valid' should ensure ppfd_allocated_by_model isn't NaN if ppfd_allocated_ground_truth is not NaN)
        # For MAE, we can directly calculate the difference of sums.
        
        relevant_daily_sums = daily_sums[daily_sums['daily_ground_truth_ppfd_sum'].notna() & daily_sums['daily_model_ppfd_sum'].notna()]

        if not relevant_daily_sums.empty:
            daily_errors = (relevant_daily_sums['daily_model_ppfd_sum'] - relevant_daily_sums['daily_ground_truth_ppfd_sum']).abs()
            daily_total_ppfd_mae = daily_errors.mean()

            # Further analysis of daily PPFD differences
            relevant_daily_sums['ppfd_sum_difference'] = relevant_daily_sums['daily_model_ppfd_sum'] - relevant_daily_sums['daily_ground_truth_ppfd_sum']
            
            tolerance = 1.0 # Define a tolerance for 'exact' match of daily totals
            days_model_under_allocated = (relevant_daily_sums['ppfd_sum_difference'] < -tolerance).sum()
            days_model_over_allocated = (relevant_daily_sums['ppfd_sum_difference'] > tolerance).sum()
            days_model_approx_match = ((relevant_daily_sums['ppfd_sum_difference'] >= -tolerance) & (relevant_daily_sums['ppfd_sum_difference'] <= tolerance)).sum()
            
            average_daily_ppfd_difference = relevant_daily_sums['ppfd_sum_difference'].mean()
            std_dev_daily_ppfd_difference = relevant_daily_sums['ppfd_sum_difference'].std()
            total_ppfd_under_allocated = relevant_daily_sums.loc[relevant_daily_sums['ppfd_sum_difference'] < -tolerance, 'ppfd_sum_difference'].sum()
            total_ppfd_over_allocated = relevant_daily_sums.loc[relevant_daily_sums['ppfd_sum_difference'] > tolerance, 'ppfd_sum_difference'].sum()
            net_cumulative_ppfd_difference = relevant_daily_sums['ppfd_sum_difference'].sum()

    # Calculate Daily Total PPFD MAE as a percentage
    average_daily_ground_truth_ppfd_total = np.nan
    daily_total_ppfd_mae_percentage = np.nan

    if 'relevant_daily_sums' in locals() and not relevant_daily_sums.empty:
        average_daily_ground_truth_ppfd_total = relevant_daily_sums['daily_ground_truth_ppfd_sum'].mean()
        if average_daily_ground_truth_ppfd_total != 0 and not np.isnan(daily_total_ppfd_mae):
            daily_total_ppfd_mae_percentage = (daily_total_ppfd_mae / average_daily_ground_truth_ppfd_total) * 100

    # --- Cost Analysis ---
    total_cost_ground_truth = np.nan
    total_cost_model = np.nan
    cost_difference_percentage = np.nan

    # Calculate hourly costs
    # Fill NaN in EUR/PPFD with a value that results in NaN cost if PPFD is present, or handle explicitly.
    # For simplicity, if EUR/PPFD is NaN, cost will be NaN. sum() later will treat NaNs as 0 by default if not skipped.
    comparison_df['cost_gt_hourly'] = comparison_df[EUR_PPFD_COL_NAME] * comparison_df['ppfd_allocated_ground_truth'].fillna(0)
    comparison_df['cost_model_hourly'] = comparison_df[EUR_PPFD_COL_NAME] * comparison_df['ppfd_allocated_by_model'].fillna(0)

    # Sum total costs. .sum() will treat NaNs as 0 unless all are NaN for a column.
    total_cost_ground_truth = comparison_df['cost_gt_hourly'].sum()
    total_cost_model = comparison_df['cost_model_hourly'].sum()
    
    # Warning if EUR/PPFD was NaN for any hour where PPFD was allocated
    if comparison_df[comparison_df[EUR_PPFD_COL_NAME].isna() & (comparison_df['ppfd_allocated_ground_truth'].fillna(0) > 0)].shape[0] > 0:
        print(f"Warning: Ground truth cost calculation encountered missing '{EUR_PPFD_COL_NAME}' for some hours with allocation. These contribute 0 to total cost.")
    if comparison_df[comparison_df[EUR_PPFD_COL_NAME].isna() & (comparison_df['ppfd_allocated_by_model'].fillna(0) > 0)].shape[0] > 0:
        print(f"Warning: Model cost calculation encountered missing '{EUR_PPFD_COL_NAME}' for some hours with allocation. These contribute 0 to total cost.")

    # Calculate daily costs for std dev calculation
    if EUR_PPFD_COL_NAME in comparison_df.columns:
        daily_costs_df = comparison_df.groupby('date').agg(
            daily_gt_cost=('cost_gt_hourly', 'sum'),
            daily_model_cost=('cost_model_hourly', 'sum')
        ).reset_index()
        daily_costs_df['daily_cost_difference'] = daily_costs_df['daily_model_cost'] - daily_costs_df['daily_gt_cost']
        std_dev_daily_cost_difference = daily_costs_df['daily_cost_difference'].std()
    else:
        std_dev_daily_cost_difference = np.nan

    t_statistic_daily_costs = np.nan
    p_value_daily_costs = np.nan

    if EUR_PPFD_COL_NAME in comparison_df.columns and not daily_costs_df.empty:
        # Perform paired t-test on daily costs if enough data points
        if len(daily_costs_df) >= 2: # t-test needs at least 2 observations
            # Drop rows with NaN in either cost column before t-test to avoid errors
            valid_daily_costs_for_ttest = daily_costs_df[['daily_model_cost', 'daily_gt_cost']].dropna()
            if len(valid_daily_costs_for_ttest) >= 2:
                t_stat, p_val = ttest_rel(valid_daily_costs_for_ttest['daily_model_cost'], valid_daily_costs_for_ttest['daily_gt_cost'])
                t_statistic_daily_costs = t_stat
                p_value_daily_costs = p_val
            else:
                print("Warning: Not enough valid (non-NaN) paired daily cost observations for t-test after dropping NaNs.")
        else:
            print("Warning: Not enough daily cost observations for t-test.")
    else:
        std_dev_daily_cost_difference = np.nan

    if not np.isnan(total_cost_ground_truth) and not np.isnan(total_cost_model):
        if total_cost_ground_truth != 0:
            cost_difference_percentage = ((total_cost_model - total_cost_ground_truth) / total_cost_ground_truth) * 100
        elif total_cost_model != 0: # Ground truth cost is 0, but model cost is not
            cost_difference_percentage = float('inf')
        else: # Both are 0
            cost_difference_percentage = 0.0

    # --- 5. Output Results ---
    print("\n--- Overall Analysis Summary ---")
    json_success_rate = (valid_json_output_count / total_items) * 100 if total_items > 0 else 0
    print(f"JSON Output Success Rate: {valid_json_output_count}/{total_items} examples ({json_success_rate:.2f}%) had a valid JSON structure with allocations.")
    print(f"Exact Hourly Allocations Match: {num_exact_hourly_matches}/{total_hourly_comparisons} hours ({percentage_exact_hourly_matches:.2f}%) matched ground truth.")
    print(f"Exact Daily Allocations Match: {num_exact_daily_matches}/{total_days_in_comparison} days ({percentage_exact_daily_matches:.2f}%) matched ground truth for all 24 hours.")
    print(f"Mean Absolute Error (MAE): {mae:.4f} (calculated on {both_valid.sum()} hourly entries with valid data for both model and ground truth)")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f} (calculated on {both_valid.sum()} hourly entries with valid data for both model and ground truth)")
    print(f"Daily Total PPFD Mean Absolute Error (MAE): {daily_total_ppfd_mae:.4f} (calculated on {len(relevant_daily_sums) if 'relevant_daily_sums' in locals() else 0} days with complete data)")
    print(f"Average Daily Ground Truth PPFD Total: {average_daily_ground_truth_ppfd_total:.2f}")
    print(f"Daily Total PPFD MAE as Percentage of Average Daily Ground Truth: {daily_total_ppfd_mae_percentage:.2f}%")
    print("\n--- Daily PPFD Allocation Bias Analysis ---")
    if 'relevant_daily_sums' in locals() and not relevant_daily_sums.empty:
        print(f"  Days model UNDER-allocated total PPFD (by > {tolerance} unit): {days_model_under_allocated}")
        print(f"  Days model OVER-allocated total PPFD (by > {tolerance} unit): {days_model_over_allocated}")
        print(f"  Days model APPROXIMATELY MATCHED total PPFD (within +/- {tolerance} unit): {days_model_approx_match}")
        print(f"  Average daily difference (Model - Ground Truth): {average_daily_ppfd_difference:.2f} PPFD units")
        print(f"  Standard Deviation of daily PPFD difference: {std_dev_daily_ppfd_difference:.2f} PPFD units")
        print(f"  Cumulative PPFD UNDER-allocated across days: {total_ppfd_under_allocated:.2f} PPFD units")
        print(f"  Cumulative PPFD OVER-allocated across days: {total_ppfd_over_allocated:.2f} PPFD units")
        print(f"  Net Cumulative PPFD difference (Model - GT): {net_cumulative_ppfd_difference:.2f} PPFD units")
    else:
        print("  Daily PPFD bias analysis could not be performed (no relevant daily sums).")

    print(f"\n--- Cost Analysis ---")
    print(f"Total Ground Truth Cost: {total_cost_ground_truth:.4f} EUR")
    print(f"Total Model Allocation Cost: {total_cost_model:.4f} EUR")
    print(f"Cost Difference (Model vs Ground Truth): {cost_difference_percentage:.2f}%")
    print(f"Standard Deviation of daily COST difference (Model - GT): {std_dev_daily_cost_difference:.4f} EUR")
    print(f"Paired t-test for daily costs (Model vs GT): t-statistic = {t_statistic_daily_costs:.4f}, p-value = {p_value_daily_costs:.4f}")

    # --- Seasonal Performance Analysis ---
    SEASON_COL_NAME = 'season' # Define it here for use in this section
    print("\n--- Seasonal Performance Analysis ---")
    seasonal_summary = {}
    if SEASON_COL_NAME in comparison_df.columns and comparison_df[SEASON_COL_NAME].notna().any():
        unique_seasons = comparison_df[SEASON_COL_NAME].dropna().unique()

        if len(unique_seasons) == 0:
            print("  No valid season data found in comparison_df.")
        else:
            for season in unique_seasons:
                print(f"\n  --- Season: {season} ---")
                seasonal_df = comparison_df[comparison_df[SEASON_COL_NAME] == season].copy()
                
                if seasonal_df.empty:
                    print("    No data for this season.")
                    seasonal_summary[season] = {"error": "No data for this season", "date_range": "N/A"}
                    continue

                # Determine date range for the season from the test data
                min_date_season = seasonal_df['date_dt'].min().strftime('%Y-%m-%d')
                max_date_season = seasonal_df['date_dt'].max().strftime('%Y-%m-%d')
                date_range_str = f"{min_date_season} to {max_date_season}"

                # Recalculate Daily Total PPFD MAE for the season
                s_daily_total_ppfd_mae = np.nan
                s_average_daily_ground_truth_ppfd_total = np.nan
                s_daily_total_ppfd_mae_percentage = np.nan
                s_days_model_under_allocated = 0
                s_days_model_over_allocated = 0
                s_days_model_approx_match = 0
                s_average_daily_ppfd_difference = np.nan
                s_total_cost_ground_truth_season = np.nan
                s_total_cost_model_season = np.nan
                s_cost_difference_percentage_season = np.nan

                s_both_valid = seasonal_df['ppfd_allocated_by_model'].notna() & seasonal_df['ppfd_allocated_ground_truth'].notna()
                if not seasonal_df.empty and s_both_valid.sum() > 0:
                    s_daily_sums = seasonal_df[s_both_valid].groupby('date').agg(
                        daily_model_ppfd_sum=('ppfd_allocated_by_model', 'sum'),
                        daily_ground_truth_ppfd_sum=('ppfd_allocated_ground_truth', 'sum')
                    ).reset_index()
                    
                    s_relevant_daily_sums = s_daily_sums[s_daily_sums['daily_ground_truth_ppfd_sum'].notna() & s_daily_sums['daily_model_ppfd_sum'].notna()]

                    if not s_relevant_daily_sums.empty:
                        s_daily_errors = (s_relevant_daily_sums['daily_model_ppfd_sum'] - s_relevant_daily_sums['daily_ground_truth_ppfd_sum']).abs()
                        s_daily_total_ppfd_mae = s_daily_errors.mean()
                        
                        s_average_daily_ground_truth_ppfd_total = s_relevant_daily_sums['daily_ground_truth_ppfd_sum'].mean()
                        if s_average_daily_ground_truth_ppfd_total != 0 and not np.isnan(s_daily_total_ppfd_mae):
                            s_daily_total_ppfd_mae_percentage = (s_daily_total_ppfd_mae / s_average_daily_ground_truth_ppfd_total) * 100

                        s_relevant_daily_sums['ppfd_sum_difference'] = s_relevant_daily_sums['daily_model_ppfd_sum'] - s_relevant_daily_sums['daily_ground_truth_ppfd_sum']
                        s_days_model_under_allocated = (s_relevant_daily_sums['ppfd_sum_difference'] < -tolerance).sum()
                        s_days_model_over_allocated = (s_relevant_daily_sums['ppfd_sum_difference'] > tolerance).sum()
                        s_days_model_approx_match = ((s_relevant_daily_sums['ppfd_sum_difference'] >= -tolerance) & (s_relevant_daily_sums['ppfd_sum_difference'] <= tolerance)).sum()
                        s_average_daily_ppfd_difference = s_relevant_daily_sums['ppfd_sum_difference'].mean()

                # Recalculate Cost Analysis for the season
                if EUR_PPFD_COL_NAME in seasonal_df.columns:
                    seasonal_df['cost_gt_hourly_season'] = seasonal_df[EUR_PPFD_COL_NAME] * seasonal_df['ppfd_allocated_ground_truth'].fillna(0)
                    seasonal_df['cost_model_hourly_season'] = seasonal_df[EUR_PPFD_COL_NAME] * seasonal_df['ppfd_allocated_by_model'].fillna(0)
                    s_total_cost_ground_truth_season = seasonal_df['cost_gt_hourly_season'].sum()
                    s_total_cost_model_season = seasonal_df['cost_model_hourly_season'].sum()

                    if not np.isnan(s_total_cost_ground_truth_season) and not np.isnan(s_total_cost_model_season):
                        if s_total_cost_ground_truth_season != 0:
                            s_cost_difference_percentage_season = ((s_total_cost_model_season - s_total_cost_ground_truth_season) / s_total_cost_ground_truth_season) * 100
                        elif s_total_cost_model_season != 0:
                            s_cost_difference_percentage_season = float('inf')
                        else:
                            s_cost_difference_percentage_season = 0.0
                
                print(f"    Daily Total PPFD MAE: {s_daily_total_ppfd_mae:.4f}")
                print(f"    Daily Total PPFD MAE %: {s_daily_total_ppfd_mae_percentage:.2f}%")
                print(f"    Days model UNDER-allocated: {s_days_model_under_allocated}")
                print(f"    Days model OVER-allocated: {s_days_model_over_allocated}")
                print(f"    Days model APPROX MATCHED: {s_days_model_approx_match}")
                print(f"    Average Daily PPFD Difference: {s_average_daily_ppfd_difference:.2f}")
                print(f"    Total Ground Truth Cost: {s_total_cost_ground_truth_season:.2f} EUR")
                print(f"    Total Model Cost: {s_total_cost_model_season:.2f} EUR")
                print(f"    Cost Difference %: {s_cost_difference_percentage_season:.2f}%")
                print(f"    Date Range (in test data): {date_range_str}")

                seasonal_summary[season] = {
                    "date_range": date_range_str,
                    "daily_total_ppfd_mae": round(s_daily_total_ppfd_mae, 4) if not np.isnan(s_daily_total_ppfd_mae) else None,
                    "daily_total_ppfd_mae_percentage": round(s_daily_total_ppfd_mae_percentage, 2) if not np.isnan(s_daily_total_ppfd_mae_percentage) else None,
                    "days_model_under_allocated": int(s_days_model_under_allocated),
                    "days_model_over_allocated": int(s_days_model_over_allocated),
                    "days_model_approx_match": int(s_days_model_approx_match),
                    "average_daily_ppfd_difference_ppfd_units": round(s_average_daily_ppfd_difference, 2) if not np.isnan(s_average_daily_ppfd_difference) else None,
                    "total_ground_truth_cost_eur": round(s_total_cost_ground_truth_season, 2) if not np.isnan(s_total_cost_ground_truth_season) else None,
                    "total_model_allocation_cost_eur": round(s_total_cost_model_season, 2) if not np.isnan(s_total_cost_model_season) else None,
                    "cost_difference_percentage": round(s_cost_difference_percentage_season, 2) if not np.isnan(s_cost_difference_percentage_season) else None
                }
    else:
        print("  Season column not found in comparison_df. Skipping seasonal analysis.")

    # --- 6. Save Comparison DataFrame ---
    try:
        comparison_df.to_excel(COMPARISON_OUTPUT_EXCEL_FILE, index=False)
        print(f"\nSuccessfully saved comparison data to '{COMPARISON_OUTPUT_EXCEL_FILE}'.")
    except Exception as e:
        print(f"\nError writing comparison DataFrame to Excel file '{COMPARISON_OUTPUT_EXCEL_FILE}': {e}")

    # --- 7. Generate JSON Summary Output ---
    summary_data = {
        "model_info": {
            "model_name": MODEL_NAME_FOR_SUMMARY,
            "number_of_test_items": total_items
        },
        "json_output_quality": {
            "valid_json_rate_percentage": round(json_success_rate, 2),
            "valid_json_count": int(valid_json_output_count),
            "total_items": int(total_items)
        },
        "ppfd_allocation_accuracy": {
            "hourly_level": {
                "exact_match_rate_percentage": round(percentage_exact_hourly_matches, 2),
                "exact_match_count": int(num_exact_hourly_matches),
                "total_hourly_comparisons": int(total_hourly_comparisons),
                "mae_hourly": round(mae, 4),
                "rmse_hourly": round(rmse, 4)
            },
            "daily_level": {
                "exact_match_rate_percentage": round(percentage_exact_daily_matches, 2),
                "exact_match_count": int(num_exact_daily_matches) if 'num_exact_daily_matches' in locals() and not isinstance(num_exact_daily_matches, bool) else (1 if num_exact_daily_matches is True else 0 if num_exact_daily_matches is False else None),
                "total_days_in_comparison": int(total_days_in_comparison) if 'total_days_in_comparison' in locals() else None,
                "daily_total_ppfd_mae": round(daily_total_ppfd_mae, 4) if 'daily_total_ppfd_mae' in locals() and not np.isnan(daily_total_ppfd_mae) else None,
                "average_daily_ground_truth_ppfd_total": round(average_daily_ground_truth_ppfd_total, 2) if 'average_daily_ground_truth_ppfd_total' in locals() and not np.isnan(average_daily_ground_truth_ppfd_total) else None,
                "daily_total_ppfd_mae_percentage": round(daily_total_ppfd_mae_percentage, 2) if 'daily_total_ppfd_mae_percentage' in locals() and not np.isnan(daily_total_ppfd_mae_percentage) else None
            }
        },
        "daily_ppfd_allocation_bias": {
            "tolerance_for_approx_match_ppfd_units": float(tolerance),
            "days_model_under_allocated": int(days_model_under_allocated) if 'days_model_under_allocated' in locals() else None,
            "days_model_over_allocated": int(days_model_over_allocated) if 'days_model_over_allocated' in locals() else None,
            "days_model_approx_match": int(days_model_approx_match) if 'days_model_approx_match' in locals() else None,
            "average_daily_difference_ppfd_units": round(average_daily_ppfd_difference, 2) if 'average_daily_ppfd_difference' in locals() and not np.isnan(average_daily_ppfd_difference) else None,
            "std_dev_daily_ppfd_difference_ppfd_units": round(std_dev_daily_ppfd_difference, 2) if 'std_dev_daily_ppfd_difference' in locals() and not np.isnan(std_dev_daily_ppfd_difference) else None,
            "cumulative_ppfd_under_allocated": round(total_ppfd_under_allocated, 2) if 'total_ppfd_under_allocated' in locals() and not np.isnan(total_ppfd_under_allocated) else None,
            "cumulative_ppfd_over_allocated": round(total_ppfd_over_allocated, 2) if 'total_ppfd_over_allocated' in locals() and not np.isnan(total_ppfd_over_allocated) else None,
            "net_cumulative_ppfd_difference": round(net_cumulative_ppfd_difference, 2) if 'net_cumulative_ppfd_difference' in locals() and not np.isnan(net_cumulative_ppfd_difference) else None
        },
        "cost_analysis": {
            "total_ground_truth_cost_eur": round(total_cost_ground_truth, 4) if not np.isnan(total_cost_ground_truth) else None,
            "total_model_allocation_cost_eur": round(total_cost_model, 4) if not np.isnan(total_cost_model) else None,
            "cost_difference_absolute_eur": round(total_cost_model - total_cost_ground_truth, 4) if not np.isnan(total_cost_model - total_cost_ground_truth) else None,
            "cost_difference_percentage": round(cost_difference_percentage, 2) if 'cost_difference_percentage' in locals() and not np.isnan(cost_difference_percentage) else None,
            "std_dev_daily_cost_difference_eur": round(std_dev_daily_cost_difference, 4) if 'std_dev_daily_cost_difference' in locals() and not np.isnan(std_dev_daily_cost_difference) else None,
            "paired_t_test_daily_costs": {
                "t_statistic": round(t_statistic_daily_costs, 4) if 't_statistic_daily_costs' in locals() and not np.isnan(t_statistic_daily_costs) else None,
                "p_value": round(p_value_daily_costs, 4) if 'p_value_daily_costs' in locals() and not np.isnan(p_value_daily_costs) else None
            }
        },
        "seasonal_performance_analysis": seasonal_summary if 'seasonal_summary' in locals() and seasonal_summary else {}
    }

    try:
        with open(ANALYSIS_SUMMARY_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully saved analysis summary to '{ANALYSIS_SUMMARY_JSON_FILE}'.")
    except Exception as e:
        print(f"\nError writing analysis summary to JSON file '{ANALYSIS_SUMMARY_JSON_FILE}': {e}")

if __name__ == '__main__':
    main() 