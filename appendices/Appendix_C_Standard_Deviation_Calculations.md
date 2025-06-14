# Appendix C: Standard Deviation Calculations for Parameter Groups

**Analysis Date**: June 8, 2025  
**Data Source**: LED Optimization LLM Performance Analysis (n=5 models)

## C.2 Raw Performance Data

### Table C.1: Hourly Success Rates by Parameter Group

| **Model** | **Parameters (B)** | **Group** | **Hourly Success (%)** |
|-----------|-------------------|-----------|----------------------|
| Mistral 7B | 7 | 7B Models | 0.3 |
| DeepSeek R1 Distill | 7 | 7B Models | 0.7 |
| Llama 3.3 70B | 70 | 70B Model | 29.5 |
| Claude 3.7 Sonnet | 200 | 200B+ Models | 48.3 |
| DeepSeek R1 0528 | 671 | 200B+ Models | 68.9 |

## C.3 Standard Deviation Calculations

### C.3.1 7B Models Group (n=2)
- Values: 0.3%, 0.7%
- Mean (x̄) = (0.3 + 0.7) ÷ 2 = 0.514%
- Deviations: (0.3 - 0.514) = -0.214, (0.7 - 0.514) = 0.186
- Squared deviations: (-0.214)² = 0.046, (0.186)² = 0.035
- Sum of squared deviations = 0.046 + 0.035 = 0.081
- Sample standard deviation = √(0.081 ÷ 1) = 0.32%

### C.3.2 200B+ Models Group (n=2)
- Values: 48.3%, 68.9%
- Mean (x̄) = (48.3 + 68.9) ÷ 2 = 58.594%
- Deviations: (48.3 - 58.594) = -10.294, (68.9 - 58.594) = 10.306
- Squared deviations: (-10.294)² = 105.966, (10.306)² = 106.214
- Sum of squared deviations = 105.966 + 106.214 = 212.180
- Sample standard deviation = √(212.180 ÷ 1) = 14.6%

## C.4 Summary

### Table C.2: Parameter Group Statistics

| **Parameter Group** | **Mean (%)** | **Sample Standard Deviation** |
|-------------------|-------------|------------------------------|
| **7B Models** | 0.514 | 0.32 |
| **70B Model** | 29.456 | - |
| **200B+ Models** | 58.594 | 14.6 |

### Calculation Method
- Formula: Sample standard deviation = √[Σ(xi - x̄)² ÷ (n-1)]
- Degrees of Freedom: n-1 = 1 for groups with n=2 