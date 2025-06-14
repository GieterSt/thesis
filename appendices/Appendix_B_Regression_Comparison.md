# Appendix B: Regression Model Comparison - Linear vs. Log-Linear Analysis

**Analysis Date**: June 8, 2025  
**Dataset**: LED Optimization LLM Performance (n=5 models)

## Table B.1: Regression Model Performance Comparison

| **Model Type** | **Equation** | **R²** | **Residual Std** | **Shapiro-Wilk p** |
|----------------|--------------|--------|------------------|-------------------|
| **Linear** | Performance = 11.36 + 0.095 × Parameters | 0.790 | 12.29 | 0.162 |
| **Log-Linear** | Performance = -29.13 + 33.86 × log₁₀(Parameters) | 0.994 | 2.15 | 0.432 |

## Statistical Tests
- Linear model F-statistic: 11.25 (p < 0.05)
- Log-linear residual standard deviation: 2.15
- Linear residual standard deviation: 12.29
- Outlier analysis: No outliers detected in either model (all z-scores < 2.0)

---
