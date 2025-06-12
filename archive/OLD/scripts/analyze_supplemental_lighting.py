import pandas as pd
import numpy as np

def analyze_supplemental_lighting(data_file, target_dli=17):
    """
    Analyze supplemental lighting requirements throughout the year
    
    Args:
        data_file: Path to the Excel file with supplemental DLI data
        target_dli: Target DLI value used for calculations
    """
    try:
        # Read the data
        df = pd.read_excel(data_file)
        
        # Convert datetime column
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        print(f"Supplemental Lighting Analysis (Target DLI: {target_dli} mol/m²/d)")
        print("=" * 70)
        
        # Overall statistics
        total_hours = len(df)
        supplemental_needed_hours = (df['supplemental_dli_needed_mol_m2_d'] > 0).sum()
        percentage_needing_supplement = (supplemental_needed_hours / total_hours) * 100
        
        print(f"Overall Statistics:")
        print(f"  Total hours analyzed: {total_hours:,}")
        print(f"  Hours requiring supplemental lighting: {supplemental_needed_hours:,} ({percentage_needing_supplement:.1f}%)")
        print(f"  Hours with sufficient natural light: {total_hours - supplemental_needed_hours:,} ({100 - percentage_needing_supplement:.1f}%)")
        print(f"  Average supplemental DLI needed: {df['supplemental_dli_needed_mol_m2_d'].mean():.3f} mol/m²/d")
        print(f"  Maximum supplemental DLI needed: {df['supplemental_dli_needed_mol_m2_d'].max():.3f} mol/m²/d")
        
        # Monthly analysis
        print(f"\nMonthly Analysis:")
        print("-" * 70)
        print(f"{'Month':<12} {'Natural DLI':<12} {'Supplement':<12} {'% Need':<8} {'Avg Supplement':<15}")
        print(f"{'':12} {'Avg (mol/m²/d)':<12} {'Hours':<12} {'Lighting':<8} {'DLI (mol/m²/d)':<15}")
        print("-" * 70)
        
        monthly_stats = []
        for month_num in range(1, 13):
            month_data = df[df['month_num'] == month_num]
            if not month_data.empty:
                month_name = month_data['month'].iloc[0]
                avg_natural_dli = month_data['natural_inside_dli_mol_m2_d'].mean()
                supplement_hours = (month_data['supplemental_dli_needed_mol_m2_d'] > 0).sum()
                total_month_hours = len(month_data)
                percent_need_supplement = (supplement_hours / total_month_hours) * 100
                avg_supplement_needed = month_data['supplemental_dli_needed_mol_m2_d'].mean()
                
                monthly_stats.append({
                    'month': month_name,
                    'month_num': month_num,
                    'avg_natural_dli': avg_natural_dli,
                    'supplement_hours': supplement_hours,
                    'percent_need': percent_need_supplement,
                    'avg_supplement': avg_supplement_needed
                })
                
                print(f"{month_name:<12} {avg_natural_dli:<12.3f} {supplement_hours:<12} {percent_need_supplement:<8.1f} {avg_supplement_needed:<15.3f}")
        
        # Seasonal analysis
        print(f"\nSeasonal Analysis:")
        print("-" * 50)
        seasons = {
            'Winter': [12, 1, 2],
            'Spring': [3, 4, 5], 
            'Summer': [6, 7, 8],
            'Autumn': [9, 10, 11]
        }
        
        for season, months in seasons.items():
            season_data = df[df['month_num'].isin(months)]
            if not season_data.empty:
                avg_natural = season_data['natural_inside_dli_mol_m2_d'].mean()
                supplement_hours = (season_data['supplemental_dli_needed_mol_m2_d'] > 0).sum()
                total_season_hours = len(season_data)
                percent_need = (supplement_hours / total_season_hours) * 100
                avg_supplement = season_data['supplemental_dli_needed_mol_m2_d'].mean()
                
                print(f"{season:<8}: Natural DLI {avg_natural:.3f}, {percent_need:.1f}% need supplement, avg {avg_supplement:.3f} mol/m²/d")
        
        # Energy implications
        print(f"\nEnergy Implications:")
        print("-" * 50)
        
        # Estimate energy requirements (rough calculation)
        # Assuming LED efficiency of ~2.5 μmol/J and 12-hour photoperiod
        led_efficiency = 2.5  # μmol/J
        hours_per_day = 12
        
        # Convert supplemental DLI to daily energy requirement
        df['daily_energy_kwh_m2'] = (df['supplemental_dli_needed_mol_m2_d'] * 1e6) / (led_efficiency * 3600 * hours_per_day) / 1000
        
        avg_daily_energy = df['daily_energy_kwh_m2'].mean()
        max_daily_energy = df['daily_energy_kwh_m2'].max()
        annual_energy = df['daily_energy_kwh_m2'].sum() / 24  # Convert hourly to daily totals
        
        print(f"Estimated LED energy requirements (2.5 μmol/J efficiency):")
        print(f"  Average daily energy: {avg_daily_energy:.3f} kWh/m²")
        print(f"  Maximum daily energy: {max_daily_energy:.3f} kWh/m²")
        print(f"  Estimated annual energy: {annual_energy:.1f} kWh/m²")
        
        # Best and worst months for natural light
        if monthly_stats:
            monthly_df = pd.DataFrame(monthly_stats)
            best_month = monthly_df.loc[monthly_df['avg_natural_dli'].idxmax()]
            worst_month = monthly_df.loc[monthly_df['avg_natural_dli'].idxmin()]
            
            print(f"\nBest/Worst Months for Natural Light:")
            print("-" * 50)
            print(f"Best month:  {best_month['month']} (avg {best_month['avg_natural_dli']:.3f} mol/m²/d, {best_month['percent_need']:.1f}% need supplement)")
            print(f"Worst month: {worst_month['month']} (avg {worst_month['avg_natural_dli']:.3f} mol/m²/d, {worst_month['percent_need']:.1f}% need supplement)")
        
        return df
        
    except Exception as e:
        print(f"Error analyzing data: {e}")
        return None

if __name__ == "__main__":
    data_file = "data_versions/SSRD_data_v6_with_supplemental_dli.xlsx"
    analyze_supplemental_lighting(data_file) 