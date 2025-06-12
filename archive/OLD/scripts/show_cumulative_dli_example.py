import pandas as pd
import matplotlib.pyplot as plt

def show_cumulative_dli_example(data_file, sample_date="2024-06-21"):
    """
    Show how cumulative DLI builds up throughout a sample day
    
    Args:
        data_file: Path to the Excel file with cumulative DLI data
        sample_date: Date to show as example (default: summer solstice)
    """
    try:
        # Read the data
        df = pd.read_excel(data_file)
        
        # Convert datetime column
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Filter for the sample date
        sample_day = df[df['datetime'].dt.date == pd.to_datetime(sample_date).date()]
        
        if sample_day.empty:
            print(f"No data found for {sample_date}")
            # Find available dates
            available_dates = df['datetime'].dt.date.unique()
            print(f"Available dates: {sorted(available_dates)[:10]}...")  # Show first 10
            # Use the first available date with significant light
            for date in sorted(available_dates):
                day_data = df[df['datetime'].dt.date == date]
                if day_data['ppfd_inside_umol_m2_s'].max() > 100:  # Find a day with good light
                    sample_day = day_data
                    sample_date = str(date)
                    print(f"Using {sample_date} instead (first day with good light)")
                    break
        
        if not sample_day.empty:
            print(f"\nCumulative DLI progression for {sample_date}:")
            print("=" * 60)
            print(f"{'Hour':>4} {'PPFD Inside':>12} {'Hourly DLI':>12} {'Cumulative DLI':>15}")
            print(f"{'':>4} {'(μmol/m²/s)':>12} {'(mol/m²)':>12} {'(mol/m²)':>15}")
            print("-" * 60)
            
            for _, row in sample_day.iterrows():
                hour = row['hour']
                ppfd = row['ppfd_inside_umol_m2_s']
                hourly_dli = ppfd * 1 * 3.6e-3  # PPFD × 1 hour × conversion factor
                cumulative = row['cumulative_natural_inside_dli_mol_m2']
                
                print(f"{hour:4d} {ppfd:12.1f} {hourly_dli:12.3f} {cumulative:15.3f}")
            
            # Summary statistics for the day
            max_cumulative = sample_day['cumulative_natural_inside_dli_mol_m2'].max()
            max_ppfd = sample_day['ppfd_inside_umol_m2_s'].max()
            daylight_hours = (sample_day['ppfd_inside_umol_m2_s'] > 10).sum()  # Hours with meaningful light
            
            print("=" * 60)
            print(f"Day Summary:")
            print(f"  Maximum PPFD: {max_ppfd:.1f} μmol/m²/s")
            print(f"  Total Daily DLI: {max_cumulative:.3f} mol/m²/d")
            print(f"  Daylight hours (>10 μmol/m²/s): {daylight_hours}")
            
            # Plant growth context
            print(f"\nPlant Growth Context:")
            if max_cumulative < 5:
                print(f"  Low light day - suitable for shade-tolerant plants")
            elif max_cumulative < 15:
                print(f"  Medium light day - good for houseplants and herbs")
            elif max_cumulative < 30:
                print(f"  High light day - excellent for most crops")
            else:
                print(f"  Very high light day - ideal for sun-loving, high-light crops")
        
        return sample_day
        
    except Exception as e:
        print(f"Error reading data: {e}")
        return None

if __name__ == "__main__":
    data_file = "data_versions/SSRD_data_v5_with_cumulative_dli.xlsx"
    show_cumulative_dli_example(data_file) 