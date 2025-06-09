# Appendix C: Standard Deviation Calculations for Parameter Groups

**Analysis Date**: June 8, 2025  
**Purpose**: Definitive calculation of standard deviations for model performance clustering  
**Data Source**: LED Optimization LLM Performance Analysis (n=5 models)

## C.1 Overview

This appendix provides the complete step-by-step calculations for standard deviations used in the parameter-performance clustering analysis. These calculations resolve any ambiguity about the reported variability within parameter groups.

## C.2 Raw Performance Data

### Table C.1: Individual Model Performance

| **Model** | **Parameters** | **Hourly Success Rate (%)** | **Group** |
|-----------|----------------|----------------------------|-----------|
| Mistral 7B Instruct | 7B | 0.28538812785388123 | 7B |
| DeepSeek R1 Distill Qwen 7B | 7B | 0.7420091324200913 | 7B |
| Llama 3.3 70B Instruct | 70B | 29.45601851851852 | 70B |
| Claude 3.7 Sonnet | 200B | 48.26388888888889 | 200B+ |
| DeepSeek R1 0528 | 671B | 68.92361111111111 | 200B+ |

## C.3 Standard Deviation Calculations

### C.3.1 7B Parameter Models

**Step 1: Calculate Mean**
- Values: 0.285%, 0.742%
- Mean = (0.28538812785388123 + 0.7420091324200913) ÷ 2
- Mean = 0.513699130137986%

**Step 2: Calculate Deviations from Mean**
- Mistral 7B deviation: 0.285% - 0.514% = -0.228%
- DeepSeek 7B deviation: 0.742% - 0.514% = +0.228%

**Step 3: Calculate Sum of Squared Deviations**
- Squared deviations: (-0.228)² + (0.228)²
- Sum of squared deviations = 0.104251

**Step 4: Calculate Sample Standard Deviation**
- Sample variance = 0.104251 ÷ (2-1) = 0.104251
- Sample standard deviation = √0.104251 = **0.323**

### C.3.2 200B+ Parameter Models

**Step 1: Calculate Mean**
- Values: 48.264%, 68.924%
- Mean = (48.26388888888889 + 68.92361111111111) ÷ 2
- Mean = 58.594%

**Step 2: Calculate Deviations from Mean**
- Claude 200B deviation: 48.264% - 58.594% = -10.330%
- DeepSeek 671B deviation: 68.924% - 58.594% = +10.330%

**Step 3: Calculate Sum of Squared Deviations**
- Squared deviations: (-10.330)² + (10.330)²
- Sum of squared deviations = 213.412061

**Step 4: Calculate Sample Standard Deviation**
- Sample variance = 213.412061 ÷ (2-1) = 213.412061
- Sample standard deviation = √213.412061 = **14.609**

## C.4 Final Results Summary

### Table C.2: Parameter Group Statistics

| **Parameter Group** | **Mean (%)** | **Sample Standard Deviation** | **Coefficient of Variation** |
|-------------------|-------------|------------------------------|----------------------------|
| **7B Models** | 0.514 | **0.32** | 62.8% |
| **70B Model** | 29.456 | N/A (single model) | N/A |
| **200B+ Models** | 58.594 | **14.6** | 24.9% |

## C.5 Verification

### C.5.1 Calculation Method
- **Formula Used**: Sample standard deviation = √[Σ(xi - x̄)² ÷ (n-1)]
- **Degrees of Freedom**: n-1 = 1 for both groups (n=2 models each)
- **Rounding**: Results rounded to appropriate significant figures for reporting

### C.5.2 Quality Assurance
- **Manual Verification**: All calculations performed step-by-step
- **Cross-Check**: Results verified against raw data values
- **Consistency**: Values align with clustering analysis in main text

---

**Note**: These calculations provide the definitive standard deviation values for all references in the thesis. Any discrepancies with preliminary calculations have been resolved through this comprehensive analysis. 