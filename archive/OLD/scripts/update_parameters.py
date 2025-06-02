#!/usr/bin/env python3
"""
Simple script to update parameters and cascade changes through all data versions.

Usage examples:
    python update_parameters.py --tau 0.73
    python update_parameters.py --target_dli 20 --photoperiod 14
    python update_parameters.py --tau 0.75 --target_dli 20 --photoperiod 16
"""

import argparse
from cascade_update_versions import cascade_update_versions, compare_parameter_impact
import os

def main():
    parser = argparse.ArgumentParser(
        description="Update parameters and cascade changes through all data versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tau 0.73                    # Change transmission factor to 0.73
  %(prog)s --target_dli 20               # Change target DLI to 20 mol/m²/d
  %(prog)s --photoperiod 14              # Change photoperiod to 14 hours
  %(prog)s --tau 0.75 --target_dli 20 --photoperiod 16  # Change multiple parameters
        """
    )
    
    parser.add_argument('--tau', type=float, 
                       help='Transmission factor (default: 0.74)')
    parser.add_argument('--target_dli', type=float,
                       help='Target DLI in mol/m²/d (default: 17)')
    parser.add_argument('--photoperiod', type=float,
                       help='Photoperiod in hours (default: 12)')
    parser.add_argument('--base_file', type=str,
                       default='data_versions/SSRD_data_v1_original.xlsx',
                       help='Base file to start cascade from')
    parser.add_argument('--no_comparison', action='store_true',
                       help='Skip parameter impact comparison')
    
    args = parser.parse_args()
    
    # Build updated parameters dictionary
    updated_parameters = {}
    
    if args.tau is not None:
        updated_parameters['tau'] = args.tau
    if args.target_dli is not None:
        updated_parameters['target_dli'] = args.target_dli
    if args.photoperiod is not None:
        updated_parameters['photoperiod'] = args.photoperiod
    
    if not updated_parameters:
        print("No parameters specified to update!")
        print("Use --help to see available options.")
        return
    
    # Check if base file exists
    if not os.path.exists(args.base_file):
        print(f"Error: Base file '{args.base_file}' not found!")
        return
    
    print("🚀 PARAMETER CASCADE UPDATE")
    print("=" * 50)
    print(f"Base file: {args.base_file}")
    print(f"Parameters to update: {updated_parameters}")
    print()
    
    # Run cascade update
    created_files = cascade_update_versions(args.base_file, updated_parameters)
    
    # Show parameter impact comparison
    if not args.no_comparison and created_files:
        print("\n🔍 PARAMETER IMPACT ANALYSIS")
        print("=" * 50)
        
        # Compare different versions based on what was updated
        comparisons = []
        
        if 'tau' in updated_parameters:
            original_v3 = "data_versions/SSRD_data_v3_with_ppfd_inside.xlsx"
            updated_v3 = "data_versions/SSRD_data_v3_with_ppfd_inside_updated.xlsx"
            if os.path.exists(original_v3) and os.path.exists(updated_v3):
                comparisons.append((original_v3, updated_v3, f"Transmission Factor (τ: 0.74 → {updated_parameters['tau']})"))
        
        if 'target_dli' in updated_parameters:
            original_v6 = "data_versions/SSRD_data_v6_with_supplemental_dli_corrected.xlsx"
            updated_v6 = "data_versions/SSRD_data_v6_with_supplemental_dli_updated.xlsx"
            if os.path.exists(original_v6) and os.path.exists(updated_v6):
                comparisons.append((original_v6, updated_v6, f"Target DLI (17 → {updated_parameters['target_dli']} mol/m²/d)"))
        
        if 'photoperiod' in updated_parameters:
            original_v4 = "data_versions/SSRD_data_v4_with_natural_inside_dli.xlsx"
            updated_v4 = "data_versions/SSRD_data_v4_with_natural_inside_dli_updated.xlsx"
            if os.path.exists(original_v4) and os.path.exists(updated_v4):
                comparisons.append((original_v4, updated_v4, f"Photoperiod (12 → {updated_parameters['photoperiod']} hours)"))
        
        for original, updated, description in comparisons:
            compare_parameter_impact(original, updated, description)
    
    print("\n✅ CASCADE UPDATE COMPLETE!")
    print(f"Created {len(created_files)} updated versions with new parameters.")
    print("\nUpdated files:")
    for file in created_files:
        print(f"  📄 {os.path.basename(file)}")

if __name__ == "__main__":
    main() 