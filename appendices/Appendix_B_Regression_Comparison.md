# Appendix B: Regression Model Comparison - Linear vs. Log-Linear Analysis

**Analysis Date**: June 8, 2025  
**Dataset**: LED Optimization LLM Performance (n=5 models)  
**Purpose**: Model selection justification for parameter-performance scaling relationship

## B.1 Overview

This appendix compares linear and log-linear regression approaches for modeling the relationship between model parameters and hourly success rate. The comparison demonstrates why the log-linear model was selected for the main analysis in Chapter 4.

## B.2 Model Comparison Summary

### Table B.1: Regression Model Performance Comparison

| **Model Type** | **Equation** | **R²** | **Residual Std** | **Shapiro-Wilk p** |
|----------------|--------------|--------|------------------|-------------------|
| **Linear** | Performance = 11.36 + 0.095 × Parameters | 0.790 | 12.29 | 0.162 |
| **Log-Linear** | Performance = -29.13 + 33.86 × log₁₀(Parameters) | **0.994** | **2.15** | 0.432 |

## B.3 Model Selection Rationale

### B.3.1 Goodness of Fit
The log-linear model explains **99.4%** of the variance in performance compared to **79.0%** for the linear model, representing a substantial improvement in explanatory power.

### B.3.2 Residual Analysis
- **Log-linear residual standard deviation**: 2.15
- **Linear residual standard deviation**: 12.29
- **Improvement**: 83% reduction in residual variation

### B.3.3 Normality of Residuals
Both models pass the Shapiro-Wilk test for normality:
- Linear model: p = 0.162 (non-significant, residuals are normal)
- Log-linear model: p = 0.432 (non-significant, residuals are normal)

## B.4 Theoretical Justification

### B.4.1 Scaling Law Literature
The log-linear relationship aligns with established scaling laws in machine learning literature, where model capabilities often scale logarithmically with parameter count.

### B.4.2 Diminishing Returns Pattern
The logarithmic transformation captures the diminishing returns pattern observed in model scaling, where each order of magnitude increase in parameters yields consistent performance improvements.

## B.5 Model Validation

### B.5.1 Statistical Significance
- **Linear F-statistic**: 11.25 (p < 0.05, significant)
- **Log-linear**: Superior fit indicates even stronger significance

### B.5.2 Outlier Analysis
No outliers detected in either model (all z-scores < 2.0), confirming model robustness.

## B.6 Conclusion

The log-linear model was selected for the main analysis based on:

1. **Superior explanatory power** (R² = 0.994 vs. 0.790)
2. **Better residual characteristics** (σ = 2.15 vs. 12.29)
3. **Theoretical alignment** with scaling law literature
4. **Maintained statistical validity** (normal residuals, no outliers)

The linear model comparison demonstrates that while a simpler relationship exists, the logarithmic transformation provides substantially better characterization of the parameter-performance scaling relationship.

---
