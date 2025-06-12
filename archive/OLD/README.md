# Data Preparation Workspace

This workspace is organized to maintain clean data versioning and script management for solar radiation data processing.

## Folder Structure

```
Data preparation/
├── data_versions/          # Current data files
│   ├── SSRD_data_latest.xlsx           # Latest version (v7 corrected)
│   ├── SSRD_data_v1_original.xlsx      # Original data
│   └── old/                            # Previous versions
│       ├── SSRD_data_v2_with_ppfd.xlsx
│       ├── SSRD_data_v3_with_ppfd_inside.xlsx
│       ├── SSRD_data_v4_with_natural_inside_dli.xlsx
│       ├── SSRD_data_v5_with_cumulative_dli.xlsx
│       ├── SSRD_data_v6_with_supplemental_dli_corrected.xlsx
│       ├── [Updated versions with different parameters]
│       └── ...
├── scripts/               # Python scripts for data processing
│   ├── process_data_with_versioning.py
│   ├── cascade_update_versions.py
│   ├── update_parameters.py
│   ├── analyze_supplemental_lighting.py
│   ├── show_cumulative_dli_example.py
│   └── ...
├── SSRD_data_2024-2025.xlsx  # Original working file
├── Electricity_data_2015-2025.csv
└── README.md
```

## Data Versioning System

### Naming Convention
- **v1_original**: Original data as received
- **v2_with_ppfd**: Added Natural Outside PPFD calculations
- **v3_with_ppfd_inside**: Added Indoor PPFD calculations
- **v4_with_natural_inside_dli**: Added Natural Inside DLI calculations
- **v5_with_cumulative_dli**: Added Cumulative Natural Inside DLI throughout the day
- **v6_with_supplemental_dli_corrected**: Added Supplemental DLI calculations (corrected)
- **v7_with_supplemental_ppfd_requirement_corrected**: Added Total Supplemental PPFD Requirement (corrected)
- **[version]_updated**: Updated versions with new parameters

### Version History
1. **v1_original**: Original SSRD data with 7 columns including redundant `date_str`
2. **v2_with_ppfd**: Cleaned data (removed `date_str`) + added PPFD calculations
   - Added: `ssrd_w_m2` (W/m²)
   - Added: `natural_outside_ppfd_umol_m2_s` (μmol/m²/s)
   - Formula: Natural Outside PPFD = SSRD (W/m²) × 2.04
3. **v3_with_ppfd_inside**: Added indoor PPFD calculations
   - Added: `ppfd_inside_umol_m2_s` (μmol/m²/s)
   - Formula: PPFD_inside = PPFD_outside × τ, where τ = 0.74 (default)
4. **v4_with_natural_inside_dli**: Added Natural Inside DLI calculations
   - Added: `natural_inside_dli_mol_m2_d` (mol/m²/d)
   - Formula: DLI = PPFD (μmol/m²/s) × photoperiod (h) × 3.6 × 10⁻³
5. **v5_with_cumulative_dli**: Added Cumulative Natural Inside DLI throughout the day
   - Added: `cumulative_natural_inside_dli_mol_m2` (mol/m²)
   - Resets at midnight, accumulates hourly throughout each day
6. **v6_with_supplemental_dli_corrected**: Added Supplemental DLI calculations (corrected)
   - Added: `supplemental_dli_needed_mol_m2_d` (mol/m²/d)
   - Formula: Supplemental DLI = max(0, Target DLI - Cumulative Natural DLI)
7. **v7_with_supplemental_ppfd_requirement_corrected**: Added Total Supplemental PPFD Requirement (corrected)
   - Added: `total_supplemental_ppfd_requirement_umol_m2_s_h` (μmol/m²/s·h)
   - Formula: Total Supplemental PPFD Requirement = Supplemental DLI × 277,778

## Scripts

### `update_parameters.py` ⭐ **NEW CASCADE UPDATE SYSTEM**
**Simple command-line tool to update parameters and cascade changes through all versions.**

```bash
# Change transmission factor
python scripts/update_parameters.py --tau 0.73

# Change target DLI
python scripts/update_parameters.py --target_dli 20

# Change photoperiod
python scripts/update_parameters.py --photoperiod 14

# Change multiple parameters
python scripts/update_parameters.py --tau 0.75 --target_dli 20 --photoperiod 16
```

### `cascade_update_versions.py`
Advanced script for programmatic cascade updates with parameter impact analysis.

### `process_data_with_versioning.py`
Main script for processing data with proper versioning. Always creates new versions instead of overwriting existing files.

### `analyze_supplemental_lighting.py`
Comprehensive analysis of supplemental lighting requirements with seasonal patterns and energy estimates.

### `show_cumulative_dli_example.py`
Utility script to demonstrate how cumulative DLI builds up throughout a sample day.

## 🚀 CASCADE UPDATE SYSTEM

The cascade update system allows you to change parameters in early versions and automatically propagate those changes through all dependent versions.

### Key Features:
- **Automatic propagation**: Change one parameter, update all dependent versions
- **Parameter impact analysis**: See exactly how changes affect your data
- **Version preservation**: Original versions remain untouched
- **Smart dependencies**: Only updates versions that depend on changed parameters

### Supported Parameters:
- **`tau`** (transmission factor): Affects v3 onwards
- **`target_dli`** (target DLI): Affects v6 onwards  
- **`photoperiod`** (photoperiod): Affects v4 onwards

### Example Impact Analysis:
```
Parameter Impact Analysis: Transmission Factor (τ: 0.74 → 0.73)
--------------------------------------------------
ppfd_inside_umol_m2_s:
  Original mean: 130.236
  Updated mean:  128.476
  Change: -1.35%
```

## Usage Examples

### Basic Data Processing
```python
from scripts.process_data_with_versioning import process_excel_with_versioning

# Create a single version with specific parameters
df, output_file = process_excel_with_versioning(
    input_file="data_versions/SSRD_data_v1_original.xlsx",
    base_name="SSRD_data",
    version_description="v7_custom_parameters",
    add_ppfd_inside=True,
    tau=0.75,
    add_dli=True,
    photoperiod=14,
    add_cumulative_dli=True,
    add_supplemental_dli=True,
    target_dli=20,
    add_supplemental_ppfd_requirement=True
)
```

### Cascade Parameter Updates
```python
from scripts.cascade_update_versions import cascade_update_versions

# Update multiple parameters and cascade through all versions
updated_parameters = {
    'tau': 0.75,
    'target_dli': 20,
    'photoperiod': 14
}

created_files = cascade_update_versions(
    "data_versions/SSRD_data_v1_original.xlsx", 
    updated_parameters
)
```

### Command Line Updates
```bash
# Quick parameter updates from command line
python scripts/update_parameters.py --tau 0.75 --target_dli 20
```

## Data Columns (Current v7)

1. `datetime` - Full datetime timestamp
2. `month` - Month name
3. `month_num` - Month number (1-12)
4. `hour` - Hour of the day (0-23)
5. `day` - Day of the month
6. `ssrd_kwh_m2` - Original solar radiation data (kWh/m²)
7. `ssrd_w_m2` - Solar radiation in W/m²
8. `natural_outside_ppfd_umol_m2_s` - Natural Outside PPFD (μmol/m²/s)
9. `ppfd_inside_umol_m2_s` - Indoor PPFD (μmol/m²/s)
10. `natural_inside_dli_mol_m2_d` - Natural Inside DLI (mol/m²/d)
11. `cumulative_natural_inside_dli_mol_m2` - Cumulative Natural Inside DLI (mol/m²)
12. `supplemental_dli_needed_mol_m2_d` - Supplemental DLI needed (mol/m²/d)
13. `total_supplemental_ppfd_requirement_umol_m2_s_h` - Total Supplemental PPFD Requirement (μmol/m²/s·h)

## Light Calculations

### Natural Outside PPFD
```
Natural Outside PPFD (μmol/m²/s) = Surface Solar Radiation Downwards (W/m²) × 2.04
```

### Indoor PPFD
```
PPFD_inside (μmol/m²/s) = PPFD_outside (μmol/m²/s) × τ
where τ = transmission factor (default: 0.74)
```

### Natural Inside DLI (Daily Light Integral)
```
DLI (mol/m²/d) = PPFD (μmol/m²/s) × photoperiod (h) × 3.6 × 10⁻³
where photoperiod = hours (default: 12)
```

### Cumulative Natural Inside DLI
```
Cumulative DLI (mol/m²) = Σ(PPFD (μmol/m²/s) × 1 hour × 3.6 × 10⁻³)
Resets at midnight (00:00), accumulates throughout each day
```

### Supplemental DLI
```
Supplemental DLI (mol/m²/d) = max(0, Target DLI - Cumulative Natural DLI)
where Target DLI = target value (default: 17 mol/m²/d)
```

### Total Supplemental PPFD Requirement
```
Total Supplemental PPFD Requirement (μmol/m²/s·h) = Supplemental DLI × 277,778
Or: Supplemental DLI × 1,000,000 ÷ 3.6
```

## Default Parameters

- **Transmission factor (τ):** 0.74
- **Target DLI:** 17 mol/m²/d
- **Photoperiod:** 12 hours

## Applications

This comprehensive dataset and cascade update system enables:
- **Parameter sensitivity analysis:** Quickly test different scenarios
- **LED system design:** Size fixtures based on total PPFD-hour requirements
- **Lighting schedules:** Optimize when and how much supplemental light to provide
- **Energy cost analysis:** Calculate electricity costs for year-round crop production
- **Equipment procurement:** Determine LED fixture specifications and quantities
- **Operational planning:** Schedule lighting operations based on natural light availability
- **Economic modeling:** Compare natural vs. artificial lighting costs for different crops
- **Research applications:** Study parameter impacts on lighting requirements

## Supplemental Lighting Analysis Results

### Overall Requirements
- **87.1%** of hours require supplemental lighting
- **12.9%** of hours have sufficient natural light
- Average supplemental DLI needed: **12.610 mol/m²/d**
- Average total supplemental PPFD requirement: **3,502,906 μmol/m²/s·h**

### Seasonal Analysis
- **Winter:** 99.6% need supplement, avg 15.306 mol/m²/d
- **Spring:** 81.6% need supplement, avg 11.223 mol/m²/d  
- **Summer:** 67.9% need supplement, avg 9.227 mol/m²/d
- **Autumn:** 94.2% need supplement, avg 13.664 mol/m²/d

### Best/Worst Months
- **Best month:** June (avg 14.062 mol/m²/d natural, 64.4% need supplement)
- **Worst month:** December (avg 0.832 mol/m²/d natural, 100.0% need supplement)

### Energy Requirements (LED @ 2.5 μmol/J)
- Average daily energy: **0.117 kWh/m²**
- Maximum daily energy: **0.157 kWh/m²**
- Estimated annual energy: **55.1 kWh/m²**

## PPFD Requirement Context

The Total Supplemental PPFD Requirement provides crucial information for:
- **LED system sizing:** Determine total PPFD-hours needed per day
- **Light scheduling:** Distribute PPFD requirement across photoperiod
- **Equipment selection:** Size LED fixtures based on maximum requirements
- **Cost analysis:** Calculate operational costs based on PPFD-hour requirements

### Example PPFD Requirements:
- **Maximum requirement:** 4,722,226 μmol/m²/s·h (17 mol/m²/d × 277,778)
- **Average requirement:** 3,502,906 μmol/m²/s·h (12.610 mol/m²/d × 277,778)
- **Zero requirement:** When natural DLI ≥ 17 mol/m²/d

## DLI Context for Plant Growth

The Natural Inside DLI values provide important insights for plant cultivation:
- **Low DLI (0-5 mol/m²/d):** Suitable for low-light plants, shade-tolerant species
- **Medium DLI (5-15 mol/m²/d):** Good for many houseplants and herbs
- **High DLI (15-30+ mol/m²/d):** Required for high-light crops, fruiting plants
- **Target DLI (17 mol/m²/d):** Optimal for many commercial crops

## Applications

This comprehensive dataset enables:
- **LED system design:** Size fixtures based on total PPFD-hour requirements
- **Lighting schedules:** Optimize when and how much supplemental light to provide
- **Energy cost analysis:** Calculate electricity costs for year-round crop production
- **Equipment procurement:** Determine LED fixture specifications and quantities
- **Operational planning:** Schedule lighting operations based on natural light availability
- **Economic modeling:** Compare natural vs. artificial lighting costs for different crops
- **Climate control integration:** Coordinate lighting with heating/cooling systems 