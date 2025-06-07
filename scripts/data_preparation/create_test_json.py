import pandas as pd
import json
from datetime import datetime

def create_test_json():
    """Convert test Excel data to JSON input/output pairs grouped by day"""
    
    # File paths
    test_file = "data/ground_truth/test_set_ground_truth_complete.xlsx"
    output_file = "data/ground_truth/test_ground_truth.json"
    
    print("Loading test dataset...")
    
    # Read the test file
    df = pd.read_excel(test_file)
    
    print(f"Loaded {len(df)} rows from test dataset")
    print(f"Columns: {list(df.columns)}")
    
    # Convert date column to datetime if it's not already
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date to create one entry per day
    json_data = []
    
    print("Converting to JSON input/output pairs grouped by day...")
    
    for date, day_data in df.groupby('date'):
        date_str = date.strftime('%Y-%m-%d')
        
        # Sort by hour to ensure proper order
        day_data = day_data.sort_values('hour')
        
        # Verify we have 24 hours
        if len(day_data) != 24:
            print(f"Warning: Day {date_str} has {len(day_data)} hours instead of 24")
            continue
        
        # Create input structure for the full day
        hourly_inputs = []
        for _, row in day_data.iterrows():
            hourly_input = {
                "hour": int(row['hour']),
                "rank_eur_ppfd": int(row['RANK eur/ppfd']),
                "max_ppfd_to_add_umol_m2_s": float(row['max_ppfd_to_addumol_m2_s'])
            }
            hourly_inputs.append(hourly_input)
        
        input_data = {
            "date": date_str,
            "daily_total_ppfd_requirement": float(day_data.iloc[0]['daily_total_ppfd_requirement']),
            "hourly_data": hourly_inputs
        }
        
        # Create output structure for the full day
        hourly_outputs = []
        for _, row in day_data.iterrows():
            hourly_output = {
                "hour": int(row['hour']),
                "ppfd_allocated": float(row['ppfd_allocated']),
                "remaining_ppfd_after_hour": float(row['remaining_ppfd_after_hour'])
            }
            hourly_outputs.append(hourly_output)
        
        output_data = {
            "date": date_str,
            "hourly_results": hourly_outputs
        }
        
        # Combine into input/output pair
        json_pair = {
            "input": input_data,
            "output": output_data
        }
        
        json_data.append(json_pair)
    
    print(f"Created {len(json_data)} day-based input/output pairs")
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved test ground truth to: {output_file}")
    
    # Print sample data for verification
    print("\n=== SAMPLE INPUT/OUTPUT PAIRS ===")
    for i in range(min(2, len(json_data))):
        print(f"\nSample {i+1} - Date: {json_data[i]['input']['date']}")
        print("INPUT:")
        print(f"  date: {json_data[i]['input']['date']}")
        print(f"  daily_total_ppfd_requirement: {json_data[i]['input']['daily_total_ppfd_requirement']}")
        print(f"  hourly_data: {len(json_data[i]['input']['hourly_data'])} hours")
        print("  First 3 hours:")
        for j in range(min(3, len(json_data[i]['input']['hourly_data']))):
            hour_data = json_data[i]['input']['hourly_data'][j]
            print(f"    Hour {hour_data['hour']}: rank={hour_data['rank_eur_ppfd']}, max_ppfd={hour_data['max_ppfd_to_add_umol_m2_s']}")
        
        print("OUTPUT:")
        print(f"  date: {json_data[i]['output']['date']}")
        print(f"  hourly_results: {len(json_data[i]['output']['hourly_results'])} hours")
        print("  First 3 hours:")
        for j in range(min(3, len(json_data[i]['output']['hourly_results']))):
            hour_result = json_data[i]['output']['hourly_results'][j]
            print(f"    Hour {hour_result['hour']}: allocated={hour_result['ppfd_allocated']}, remaining={hour_result['remaining_ppfd_after_hour']}")
    
    # Print summary statistics
    print(f"\n=== SUMMARY STATISTICS ===")
    
    # Extract some statistics from the data
    total_hours = sum(len(item["input"]["hourly_data"]) for item in json_data)
    all_ppfd_allocated = [hour["ppfd_allocated"] for item in json_data for hour in item["output"]["hourly_results"]]
    all_daily_requirements = [item["input"]["daily_total_ppfd_requirement"] for item in json_data]
    
    print(f"Total days: {len(json_data)}")
    print(f"Total hours: {total_hours}")
    print(f"PPFD allocated - Min: {min(all_ppfd_allocated):.2f}, Max: {max(all_ppfd_allocated):.2f}")
    print(f"Daily requirements - Min: {min(all_daily_requirements):.2f}, Max: {max(all_daily_requirements):.2f}")
    
    return json_data

if __name__ == "__main__":
    test_json = create_test_json()
    print(f"\n✅ Test JSON ground truth creation completed!")
    print(f"📁 Output file: data/ground_truth/test_ground_truth.json") 