import pandas as pd
import os
from datetime import datetime
from process_data_with_versioning import process_excel_with_versioning, list_data_versions

def cascade_update_versions(base_input_file, updated_parameters, output_dir="data_versions"):
    """
    Update parameters and cascade changes through all dependent versions
    
    Args:
        base_input_file: Starting point file (e.g., "SSRD_data_v1_original.xlsx")
        updated_parameters: Dictionary of parameters to update
        output_dir: Directory containing data versions
    
    Example updated_parameters:
    {
        'tau': 0.73,  # Changed from 0.74
        'target_dli': 20,  # Changed from 17 (example: increase to 20)
        'photoperiod': 14  # Changed from 12
    }
    """
    
    # Default parameters
    default_params = {
        'tau': 0.74,
        'target_dli': 17,
        'photoperiod': 12
    }
    
    # Update with new parameters
    params = {**default_params, **updated_parameters}
    
    print(f"Cascading parameter updates through all versions...")
    print(f"Updated parameters: {updated_parameters}")
    print("=" * 70)
    
    # Define the version cascade sequence
    version_sequence = [
        {
            'input': base_input_file,
            'output': f"SSRD_data_v2_with_ppfd_updated",
            'description': 'v2 with updated PPFD calculations',
            'operations': {
                'add_ppfd_inside': False,
                'add_dli': False,
                'add_cumulative_dli': False,
                'add_supplemental_dli': False,
                'add_supplemental_ppfd_requirement': False
            }
        },
        {
            'input': f"{output_dir}/SSRD_data_v2_with_ppfd_updated.xlsx",
            'output': f"SSRD_data_v3_with_ppfd_inside_updated",
            'description': f'v3 with updated indoor PPFD (τ={params["tau"]})',
            'operations': {
                'add_ppfd_inside': True,
                'add_dli': False,
                'add_cumulative_dli': False,
                'add_supplemental_dli': False,
                'add_supplemental_ppfd_requirement': False
            }
        },
        {
            'input': f"{output_dir}/SSRD_data_v3_with_ppfd_inside_updated.xlsx",
            'output': f"SSRD_data_v4_with_natural_inside_dli_updated",
            'description': f'v4 with updated DLI (photoperiod={params["photoperiod"]}h)',
            'operations': {
                'add_ppfd_inside': True,
                'add_dli': True,
                'add_cumulative_dli': False,
                'add_supplemental_dli': False,
                'add_supplemental_ppfd_requirement': False
            }
        },
        {
            'input': f"{output_dir}/SSRD_data_v4_with_natural_inside_dli_updated.xlsx",
            'output': f"SSRD_data_v5_with_cumulative_dli_updated",
            'description': 'v5 with updated cumulative DLI',
            'operations': {
                'add_ppfd_inside': True,
                'add_dli': True,
                'add_cumulative_dli': True,
                'add_supplemental_dli': False,
                'add_supplemental_ppfd_requirement': False
            }
        },
        {
            'input': f"{output_dir}/SSRD_data_v5_with_cumulative_dli_updated.xlsx",
            'output': f"SSRD_data_v6_with_supplemental_dli_updated",
            'description': f'v6 with updated supplemental DLI (target={params["target_dli"]} mol/m²/d)',
            'operations': {
                'add_ppfd_inside': True,
                'add_dli': True,
                'add_cumulative_dli': True,
                'add_supplemental_dli': True,
                'add_supplemental_ppfd_requirement': False
            }
        },
        {
            'input': f"{output_dir}/SSRD_data_v6_with_supplemental_dli_updated.xlsx",
            'output': f"SSRD_data_v7_with_supplemental_ppfd_requirement_updated",
            'description': 'v7 with updated PPFD requirements',
            'operations': {
                'add_ppfd_inside': True,
                'add_dli': True,
                'add_cumulative_dli': True,
                'add_supplemental_dli': True,
                'add_supplemental_ppfd_requirement': True
            }
        }
    ]
    
    # Process each version in sequence
    created_files = []
    
    for i, version in enumerate(version_sequence, 1):
        print(f"\nStep {i}: Creating {version['description']}")
        print("-" * 50)
        
        try:
            df, output_file = process_excel_with_versioning(
                input_file=version['input'],
                base_name="SSRD_data",
                version_description=version['output'].split('_', 2)[2],  # Extract version part
                output_dir=output_dir,
                tau=params['tau'],
                target_dli=params['target_dli'],
                photoperiod=params['photoperiod'],
                **version['operations']
            )
            
            if output_file:
                created_files.append(output_file)
                print(f"✓ Successfully created: {output_file}")
            else:
                print(f"✗ Failed to create version {i}")
                break
                
        except Exception as e:
            print(f"✗ Error creating version {i}: {e}")
            break
    
    print("\n" + "=" * 70)
    print("CASCADE UPDATE SUMMARY")
    print("=" * 70)
    print(f"Updated parameters:")
    for param, value in updated_parameters.items():
        old_value = default_params.get(param, 'N/A')
        print(f"  {param}: {old_value} → {value}")
    
    print(f"\nCreated {len(created_files)} updated versions:")
    for file in created_files:
        file_size = os.path.getsize(file) / 1024
        print(f"  {os.path.basename(file)} ({file_size:.1f} KB)")
    
    return created_files

def compare_parameter_impact(original_file, updated_file, parameter_name):
    """
    Compare the impact of parameter changes between two versions
    """
    try:
        df_original = pd.read_excel(original_file)
        df_updated = pd.read_excel(updated_file)
        
        print(f"\nParameter Impact Analysis: {parameter_name}")
        print("-" * 50)
        
        # Compare key columns if they exist
        comparison_columns = [
            'ppfd_inside_umol_m2_s',
            'natural_inside_dli_mol_m2_d', 
            'cumulative_natural_inside_dli_mol_m2',
            'supplemental_dli_needed_mol_m2_d',
            'total_supplemental_ppfd_requirement_umol_m2_s_h'
        ]
        
        for col in comparison_columns:
            if col in df_original.columns and col in df_updated.columns:
                orig_mean = df_original[col].mean()
                updated_mean = df_updated[col].mean()
                change_pct = ((updated_mean - orig_mean) / orig_mean * 100) if orig_mean != 0 else 0
                
                print(f"{col}:")
                print(f"  Original mean: {orig_mean:.3f}")
                print(f"  Updated mean:  {updated_mean:.3f}")
                print(f"  Change: {change_pct:+.2f}%")
                print()
        
    except Exception as e:
        print(f"Error comparing files: {e}")

if __name__ == "__main__":
    # Example: Update transmission factor from 0.74 to 0.73
    updated_parameters = {
        'tau': 0.73,  # Changed transmission factor
        # 'target_dli': 20,  # Uncomment to change target DLI (example: 20)
        # 'photoperiod': 14  # Uncomment to change photoperiod
    }
    
    base_file = "data_versions/SSRD_data_v1_original.xlsx"
    
    # Run cascade update
    created_files = cascade_update_versions(base_file, updated_parameters)
    
    # Show comparison if files were created
    if len(created_files) >= 2:
        print("\n" + "=" * 70)
        print("PARAMETER IMPACT COMPARISON")
        print("=" * 70)
        
        # Compare v3 (indoor PPFD) impact
        original_v3 = "data_versions/SSRD_data_v3_with_ppfd_inside.xlsx"
        updated_v3 = "data_versions/SSRD_data_v3_with_ppfd_inside_updated.xlsx"
        
        if os.path.exists(original_v3) and os.path.exists(updated_v3):
            compare_parameter_impact(original_v3, updated_v3, "Transmission Factor (τ)")
    
    # List all versions
    print("\n" + "=" * 70)
    print("ALL DATA VERSIONS")
    print("=" * 70)
    list_data_versions() 