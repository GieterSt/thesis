#!/usr/bin/env python3
"""
STATISTICAL ANALYSIS
Comprehensive statistical analysis including correlation, regression, and significance testing
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import spearmanr, pearsonr, kruskal, mannwhitneyu, chi2_contingency
from scipy.stats import bootstrap, norm, t
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
import warnings

def bootstrap_correlation(x, y, n_bootstrap=1000):
    """Calculate bootstrap confidence intervals for correlations"""
    correlations = []
    n = len(x)
    
    for _ in range(n_bootstrap):
        # Sample with replacement
        indices = np.random.choice(n, n, replace=True)
        x_boot = [x[i] for i in indices]
        y_boot = [y[i] for i in indices]
        
        # Calculate correlation
        if len(set(x_boot)) > 1 and len(set(y_boot)) > 1:  # Check for variation
            corr, _ = pearsonr(x_boot, y_boot)
            if not np.isnan(corr):
                correlations.append(corr)
    
    if correlations:
        return {
            'mean': np.mean(correlations),
            'std': np.std(correlations),
            'ci_lower': np.percentile(correlations, 2.5),
            'ci_upper': np.percentile(correlations, 97.5)
        }
    else:
        return {'mean': 0, 'std': 0, 'ci_lower': 0, 'ci_upper': 0}

def comprehensive_statistical_analysis(all_metrics):
    """Perform comprehensive statistical analysis on model performance data"""
    print("\n" + "="*80)
    print("📈 COMPREHENSIVE STATISTICAL ANALYSIS")
    print("="*80)
    
    if not all_metrics or len(all_metrics) < 2:
        print("⚠️  Insufficient data for statistical analysis (need at least 2 models)")
        return None
    
    # Extract data for analysis
    model_data = []
    for metrics in all_metrics:
        if metrics and metrics['model_parameters'] and metrics['basic_performance']:
            model_info = {
                'model_name': metrics['model_name'],
                'parameters': metrics['model_parameters']['parameters'],
                'architecture': metrics['model_parameters']['architecture'],
                'api_success_rate': metrics['basic_performance']['api_success_rate'],
                'json_success_rate': metrics['basic_performance']['json_success_rate'],
                'hourly_success_rate': 0,
                'exact_match_rate': 0
            }
            
            # Add ground truth metrics if available
            if metrics['ground_truth_analysis']:
                model_info['hourly_success_rate'] = metrics['ground_truth_analysis']['mean_hourly_match_rate']
                model_info['exact_match_rate'] = metrics['ground_truth_analysis']['exact_24h_match_rate']
            
            model_data.append(model_info)
    
    if len(model_data) < 2:
        print("⚠️  Insufficient valid model data for analysis")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(model_data)
    
    print(f"📊 Analyzing {len(df)} models")
    print("Models:", ', '.join(df['model_name'].tolist()))
    
    results = {
        'summary_stats': {},
        'correlations': {},
        'regression_analysis': {},
        'comparative_tests': {},
        'model_data': df
    }
    
    # Summary Statistics
    print("\n📈 Summary Statistics")
    numeric_cols = ['parameters', 'api_success_rate', 'json_success_rate', 'hourly_success_rate']
    summary_stats = df[numeric_cols].describe()
    results['summary_stats'] = summary_stats.to_dict()
    
    for col in numeric_cols:
        print(f"  {col}: μ={df[col].mean():.2f}, σ={df[col].std():.2f}")
    
    # Correlation Analysis
    print("\n🔗 Correlation Analysis")
    correlations = {}
    
    # Parameter Count vs Performance Metrics
    perf_metrics = ['api_success_rate', 'json_success_rate', 'hourly_success_rate']
    
    for metric in perf_metrics:
        if len(df[df[metric] > 0]) >= 2:  # Need at least 2 non-zero values
            # Pearson correlation
            r_pearson, p_pearson = pearsonr(df['parameters'], df[metric])
            
            # Spearman correlation (rank-based, more robust)
            r_spearman, p_spearman = spearmanr(df['parameters'], df[metric])
            
            # Bootstrap confidence intervals
            bootstrap_stats = bootstrap_correlation(df['parameters'].tolist(), df[metric].tolist())
            
            correlations[f'parameters_vs_{metric}'] = {
                'pearson_r': r_pearson,
                'pearson_p': p_pearson,
                'spearman_r': r_spearman,
                'spearman_p': p_spearman,
                'bootstrap': bootstrap_stats,
                'interpretation': interpret_correlation(r_pearson, p_pearson)
            }
            
            print(f"  Parameters vs {metric}:")
            print(f"    Pearson: r={r_pearson:.3f}, p={p_pearson:.3f}")
            print(f"    Spearman: r={r_spearman:.3f}, p={p_spearman:.3f}")
            print(f"    95% CI: [{bootstrap_stats['ci_lower']:.3f}, {bootstrap_stats['ci_upper']:.3f}]")
    
    results['correlations'] = correlations
    
    # Regression Analysis
    print("\n📊 Regression Analysis")
    regression_results = {}
    
    # Focus on hourly success rate as primary outcome
    if len(df[df['hourly_success_rate'] > 0]) >= 2:
        X = df[['parameters']].values
        y = df['hourly_success_rate'].values
        
        # Linear regression (existing)
        reg_linear = LinearRegression()
        reg_linear.fit(X, y)
        y_pred_linear = reg_linear.predict(X)
        r2_linear = r2_score(y, y_pred_linear)
        residuals_linear = y - y_pred_linear
        mse_linear = np.mean(residuals_linear ** 2)
        
        # Log-linear regression (new for thesis equation)
        X_log = np.log10(X)  # Transform parameters to log10
        reg_log = LinearRegression()
        reg_log.fit(X_log, y)
        y_pred_log = reg_log.predict(X_log)
        r2_log = r2_score(y, y_pred_log)
        residuals_log = y - y_pred_log
        mse_log = np.mean(residuals_log ** 2)
        
        regression_results['hourly_success_rate'] = {
            'linear': {
                'coefficient': reg_linear.coef_[0],
                'intercept': reg_linear.intercept_,
                'r_squared': r2_linear,
                'rmse': np.sqrt(mse_linear),
                'equation': f"Hourly Success = {reg_linear.intercept_:.2f} + {reg_linear.coef_[0]:.4f} × Parameters"
            },
            'log_linear': {
                'coefficient': reg_log.coef_[0],
                'intercept': reg_log.intercept_,
                'r_squared': r2_log,
                'rmse': np.sqrt(mse_log),
                'equation': f"Performance = {reg_log.intercept_:.1f} + {reg_log.coef_[0]:.1f} × log₁₀(Parameters)",
                'log_coefficients': {
                    'intercept': reg_log.intercept_,
                    'coefficient': reg_log.coef_[0]
                }
            }
        }
        
        print(f"  Linear Regression:")
        print(f"    R² = {r2_linear:.3f}")
        print(f"    Equation: {regression_results['hourly_success_rate']['linear']['equation']}")
        
        print(f"  Log-Linear Regression (Thesis Model):")
        print(f"    R² = {r2_log:.3f}")
        print(f"    Equation: {regression_results['hourly_success_rate']['log_linear']['equation']}")
        
        # Determine which model fits better
        if r2_log > r2_linear:
            print(f"    ✅ Log-linear model provides better fit (ΔR² = {r2_log - r2_linear:.3f})")
        else:
            print(f"    ⚠️  Linear model provides better fit (ΔR² = {r2_linear - r2_log:.3f})")
    
    results['regression_analysis'] = regression_results
    
    # Comparative Tests
    print("\n🔬 Comparative Analysis")
    comparative_results = {}
    
    # Group models by architecture if we have multiple types
    if len(df['architecture'].unique()) > 1:
        arch_groups = {}
        for arch in df['architecture'].unique():
            arch_data = df[df['architecture'] == arch]['hourly_success_rate'].values
            if len(arch_data) > 0:
                arch_groups[arch] = arch_data
        
        if len(arch_groups) >= 2:
            print(f"  Architecture Comparison: {list(arch_groups.keys())}")
            # Note: With small samples, we'd typically need more data for meaningful tests
            comparative_results['architecture_groups'] = arch_groups
    
    results['comparative_tests'] = comparative_results
    
    # Generate interpretations and recommendations
    results['insights'] = generate_statistical_insights(results)
    
    return results

def interpret_correlation(r, p, alpha=0.05):
    """Interpret correlation strength and significance"""
    # Effect size interpretation
    if abs(r) < 0.1:
        strength = "negligible"
    elif abs(r) < 0.3:
        strength = "small"
    elif abs(r) < 0.5:
        strength = "medium"
    elif abs(r) < 0.7:
        strength = "large"
    else:
        strength = "very large"
    
    # Significance
    significance = "significant" if p < alpha else "not significant"
    
    # Direction
    direction = "positive" if r > 0 else "negative"
    
    return {
        'strength': strength,
        'direction': direction,
        'significance': significance,
        'description': f"{strength} {direction} correlation ({significance})"
    }

def generate_statistical_insights(results):
    """Generate insights and interpretations from statistical results"""
    insights = {
        'key_findings': [],
        'limitations': [],
        'recommendations': []
    }
    
    # Analyze correlations
    if 'correlations' in results:
        for key, corr_data in results['correlations'].items():
            if 'parameters_vs_hourly_success_rate' in key:
                r = corr_data['pearson_r']
                p = corr_data['pearson_p']
                
                if p < 0.05:
                    insights['key_findings'].append(
                        f"Strong correlation between model size and performance (r={r:.3f}, p={p:.3f})"
                    )
                else:
                    insights['limitations'].append(
                        f"Correlation not statistically significant (p={p:.3f}) - likely due to small sample size"
                    )
    
    # Sample size assessment
    if 'model_data' in results:
        n_models = len(results['model_data'])
        insights['limitations'].append(f"Small sample size (n={n_models}) limits statistical power")
        
        if n_models < 5:
            insights['recommendations'].append("Test additional models to increase statistical power")
    
    # Performance insights
    if 'summary_stats' in results:
        stats_data = results['summary_stats']
        if 'hourly_success_rate' in stats_data:
            mean_performance = stats_data['hourly_success_rate']['mean']
            if mean_performance < 50:
                insights['key_findings'].append("Overall model performance is below acceptable thresholds")
            
    return insights 