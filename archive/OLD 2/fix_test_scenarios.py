import pandas as pd
import numpy as np

print('=== FIXING TEST SCENARIOS RANKING ERRORS ===')
print()

# Load the test scenarios
df = pd.read_excel('PPFD_Optimization_Test_Scenarios.xlsx', sheet_name='All_Scenarios')

print('1. Checking for ranking errors:')
print(f'Total records: {len(df)}')
print(f'Min rank: {df["RANK eur/ppfd"].min()}')
print(f'Max rank: {df["RANK eur/ppfd"].max()}')

# Find scenarios with invalid ranks
invalid_ranks = df[df['RANK eur/ppfd'] > 24]
print(f'Records with ranks > 24: {len(invalid_ranks)}')

if len(invalid_ranks) > 0:
    print('Scenarios with invalid ranks:')
    for scenario in invalid_ranks['scenario_id'].unique():
        scenario_data = df[df['scenario_id'] == scenario]
        max_rank = scenario_data['RANK eur/ppfd'].max()
        print(f'  Scenario {scenario}: max rank = {max_rank}')

print()
print('2. Fixing ranking errors:')

# Fix each scenario to ensure ranks are 1-24
fixed_df = df.copy()

for scenario_id in df['scenario_id'].unique():
    scenario_mask = fixed_df['scenario_id'] == scenario_id
    scenario_data = fixed_df[scenario_mask].copy()
    
    # Check if this scenario has invalid ranks
    if scenario_data['RANK eur/ppfd'].max() > 24:
        print(f'Fixing Scenario {scenario_id}...')
        
        # Get unique ranks and map them to 1-24
        unique_ranks = sorted(scenario_data['RANK eur/ppfd'].unique())
        
        # Create mapping from old ranks to new ranks (1-24)
        rank_mapping = {}
        for i, old_rank in enumerate(unique_ranks):
            new_rank = i + 1
            rank_mapping[old_rank] = new_rank
        
        # Apply the mapping
        fixed_df.loc[scenario_mask, 'RANK eur/ppfd'] = scenario_data['RANK eur/ppfd'].map(rank_mapping)
        
        print(f'  Mapped ranks: {unique_ranks} -> {list(range(1, len(unique_ranks) + 1))}')

print()
print('3. Validation after fix:')
print(f'Min rank: {fixed_df["RANK eur/ppfd"].min()}')
print(f'Max rank: {fixed_df["RANK eur/ppfd"].max()}')

# Check that each scenario has ranks 1-24
print('Checking each scenario has proper ranks:')
for scenario_id in fixed_df['scenario_id'].unique():
    scenario_data = fixed_df[fixed_df['scenario_id'] == scenario_id]
    ranks = sorted(scenario_data['RANK eur/ppfd'].unique())
    expected_ranks = list(range(1, 25))
    
    if ranks != expected_ranks:
        print(f'  ❌ Scenario {scenario_id}: ranks = {ranks}')
    else:
        print(f'  ✅ Scenario {scenario_id}: ranks 1-24 correct')

print()
print('4. Saving corrected test scenarios:')

# Create Excel file with multiple sheets
with pd.ExcelWriter('PPFD_Optimization_Test_Scenarios_FIXED.xlsx', engine='openpyxl') as writer:
    # All scenarios sheet
    fixed_df.to_excel(writer, sheet_name='All_Scenarios', index=False)
    
    # Individual scenario sheets
    for scenario_id in sorted(fixed_df['scenario_id'].unique()):
        scenario_data = fixed_df[fixed_df['scenario_id'] == scenario_id]
        sheet_name = f'Scenario_{scenario_id:02d}'
        scenario_data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Create updated summary
    summary_data = []
    for scenario_id in sorted(fixed_df['scenario_id'].unique()):
        scenario_data = fixed_df[fixed_df['scenario_id'] == scenario_id]
        
        summary_data.append({
            'Scenario_ID': scenario_id,
            'Description': f'Test scenario {scenario_id}',
            'Target_PPFD': scenario_data['total_supplemental_ppfd_requirement_umol_m2_s_h'].iloc[0],
            'Total_Available_Capacity': scenario_data['max_ppfd_to_addumol_m2_s'].sum(),
            'Min_Rank': scenario_data['RANK eur/ppfd'].min(),
            'Max_Rank': scenario_data['RANK eur/ppfd'].max(),
            'Capacity_Utilization_Required': f"{scenario_data['total_supplemental_ppfd_requirement_umol_m2_s_h'].iloc[0] / scenario_data['max_ppfd_to_addumol_m2_s'].sum() * 100:.1f}%"
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

# Also save as CSV
fixed_df.to_csv('PPFD_Optimization_Test_Scenarios_FIXED.csv', index=False)

print('✅ Saved corrected files:')
print('  - PPFD_Optimization_Test_Scenarios_FIXED.xlsx')
print('  - PPFD_Optimization_Test_Scenarios_FIXED.csv')
print()
print('The ranking errors have been fixed - all scenarios now have ranks 1-24 only.') 