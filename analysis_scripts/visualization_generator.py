#!/usr/bin/env python3
"""
VISUALIZATION GENERATOR
Creates thesis-ready visualizations with proper model naming
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
import os
import glob

# Get the script's directory to build robust paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

# Ensure output directories exist
RESULTS_DIRS = {
    'figures': PROJECT_ROOT / 'results/figures'
}

def ensure_directories():
    """Create all required output directories"""
    for dir_path in RESULTS_DIRS.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def clean_figures_directory():
    """Clean up old visualization files to avoid clutter"""
    figures_dir = RESULTS_DIRS['figures']
    
    print(f"🧹 Cleaning figures directory: {figures_dir}")
    
    # Remove all PNG files from figures directory
    png_files = glob.glob(os.path.join(figures_dir, "*.png"))
    
    removed_count = 0
    for png_file in png_files:
        try:
            os.remove(png_file)
            removed_count += 1
        except Exception as e:
            print(f"⚠️  Could not remove {png_file}: {e}")
    
    print(f"✅ Cleaned {removed_count} old visualization files")

def get_clean_model_name(model_name):
    """Get clean, consistent model names for visualization"""
    model_name_lower = model_name.lower()
    
    # Use EXACT mapping to avoid confusion - include prompt versions but exclude "improved" for Mistral
    name_mapping = {
        'deepseek-r1-0528-free': 'DeepSeek R1 V2 Prompt (671B)',
        'deepseek-r1-distill-qwen-7b': 'DeepSeek R1 Distill Qwen V2 Prompt (7B)', 
        'claude-3-7-sonnet': 'Claude 3.7 Sonnet V2 Prompt (200B)',
        'llama-3.3-70b-instruct': 'Llama 3.3 70B Instruct V2 Prompt (70B)',
        'mistral-7b-instruct': 'Mistral 7B Instruct V2 Prompt (7.3B)'
    }
    
    # Check for exact matches first
    for key, clean_name in name_mapping.items():
        if key in model_name_lower:
            return clean_name
    
    # Fallback to capitalize the original name
    return model_name.replace('_', ' ').replace('-', ' ').title()

def format_parameter_count(params):
    """Format parameter count for display"""
    if params >= 1000:
        return f"{params/1000:.0f}K"
    elif params >= 100:
        return f"{params:.0f}B"
    else:
        return f"{params:.1f}B"

def create_thesis_visualizations(all_metrics, stats_results, timestamp):
    """Generate thesis-ready visualizations - Figure 1 and Figure 1.1 only"""
    print("\n" + "="*80)
    print("📊 GENERATING THESIS VISUALIZATIONS (Figure 1 & 1.1)")
    print("="*80)
    
    ensure_directories()
    clean_figures_directory()  # Clean up old files first
    
    if not all_metrics:
        print("❌ No metrics data available for visualization")
        return None
    
    # Extract data for plotting
    plot_data = []
    for metrics in all_metrics:
        if metrics and metrics['model_parameters'] and metrics['basic_performance']:
            # Get clean model name using centralized function
            clean_name = get_clean_model_name(metrics['model_name'])
            
            model_info = {
                'model_name': clean_name,  # Use clean name consistently
                'original_name': metrics['model_name'],
                'parameters': metrics['model_parameters']['parameters'],
                'api_success_rate': metrics['basic_performance']['api_success_rate'],
                'json_success_rate': metrics['basic_performance']['json_success_rate'],
                'hourly_success_rate': 0,
                'daily_mae': 0  # Add Daily MAE metric
            }
            
            if metrics['ground_truth_analysis']:
                model_info['hourly_success_rate'] = metrics['ground_truth_analysis']['mean_hourly_match_rate']
                model_info['daily_mae'] = metrics['ground_truth_analysis']['mean_daily_mae']
            
            plot_data.append(model_info)
    
    df = pd.DataFrame(plot_data)
    
    if df.empty:
        print("❌ No valid data for plotting")
        return None
    
    print(f"📈 Creating visualizations for {len(df)} models")
    
    # Set up the plotting style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    created_figures = []
    
    # Figure 1: Scaling Law Analysis (Linear Scale)
    if len(df[df['hourly_success_rate'] > 0]) >= 2:
        fig1 = create_scaling_law_plot(df, timestamp)
        if fig1:
            created_figures.append(fig1)
    
    # Figure 1.1: Log-Scale Scaling Law (using computed regression from stats)
    if stats_results and 'regression_analysis' in stats_results:
        fig1_1 = create_log_scaling_law_plot(df, stats_results, timestamp)
        if fig1_1:
            created_figures.append(fig1_1)
    
    return created_figures

def create_scaling_law_plot(df, timestamp):
    """Create scaling law plot with proper model annotations"""
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Filter models with hourly success rate data
        df_filtered = df[df['hourly_success_rate'] > 0].copy()
        
        if len(df_filtered) < 2:
            print("⚠️  Insufficient data for scaling law plot")
            return None
        
        # Create scatter plot
        scatter = ax.scatter(df_filtered['parameters'], df_filtered['hourly_success_rate'],
                           s=200, alpha=0.7, c=range(len(df_filtered)), cmap='viridis')
        
        # Add model name annotations using smart positioning to avoid overlaps
        annotations = []
        for i, (_, row) in enumerate(df_filtered.iterrows()):
            # Calculate smart positioning to avoid overlaps
            base_offset = (15, 15)  # Base offset
            # Stagger annotations vertically for models with similar parameters
            if i > 0:
                # Check for similar parameter counts that might cause overlaps
                prev_params = list(df_filtered['parameters'])[i-1]
                curr_params = row['parameters']
                if abs(np.log10(curr_params) - np.log10(prev_params)) < 0.3:  # Close in log space
                    base_offset = (15, 15 + (i % 3) * 25)  # Stagger vertically
            
            annotation = ax.annotate(row['model_name'], 
                       (row['parameters'], row['hourly_success_rate']),
                       xytext=base_offset, textcoords='offset points',
                       fontsize=10, ha='left',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                edgecolor='#4a4a4a', alpha=0.9, linewidth=0.5),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1',
                                     color='#4a4a4a', alpha=0.7, linewidth=1))
            annotations.append(annotation)
        
        # Fit regression line if we have enough data
        if len(df_filtered) >= 2:
            z = np.polyfit(df_filtered['parameters'], df_filtered['hourly_success_rate'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df_filtered['parameters'].min(), df_filtered['parameters'].max(), 100)
            ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Trend Line')
        
        ax.set_xlabel('Model Parameters (Billions)', fontsize=12)
        ax.set_ylabel('Hourly Success Rate (%)', fontsize=12)
        ax.set_title('Scaling Law: Model Size vs Hourly Success Rate', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        # Save figure
        figure_path = f"{RESULTS_DIRS['figures']}/figure_1_scaling_law_hourly_{timestamp}.png"
        plt.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Figure 1 saved: {figure_path}")
        return figure_path
        
    except Exception as e:
        print(f"❌ Error creating scaling law plot: {e}")
        return None

def create_log_scaling_law_plot(df, stats_results, timestamp):
    """Create log-scale scaling law plot using computed regression coefficients"""
    try:
        # Check if we have log-linear regression results
        if ('regression_analysis' not in stats_results or 
            'hourly_success_rate' not in stats_results['regression_analysis'] or
            'log_linear' not in stats_results['regression_analysis']['hourly_success_rate']):
            print("⚠️  No log-linear regression data available")
            return None
        
        log_reg_data = stats_results['regression_analysis']['hourly_success_rate']['log_linear']
        
        # Create figure with wider layout to accommodate legend table
        fig, (ax, legend_ax) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [3, 1]})
        
        # Filter models with hourly success rate data and sort by PERFORMANCE (best to worst)
        df_filtered = df[df['hourly_success_rate'] > 0].copy().sort_values('hourly_success_rate', ascending=False)
        
        if len(df_filtered) < 2:
            print("⚠️  Insufficient data for log scaling law plot")
            return None
        
        # Create scatter plot with numbered points
        colors = plt.cm.viridis(np.linspace(0, 1, len(df_filtered)))
        scatter = ax.scatter(df_filtered['parameters'], df_filtered['hourly_success_rate'],
                           s=250, alpha=0.8, c=colors, edgecolors='black', linewidth=2)
        
        # Add numbered annotations with better positioning to avoid overlaps
        for i, (_, row) in enumerate(df_filtered.iterrows()):
            # More sophisticated positioning to avoid all overlaps
            # Create offsets based on both performance and parameter values
            if i == 0:  # Best performer
                offset_x, offset_y = 0, 8
            elif i == 1:  # Second best
                offset_x, offset_y = 0, -8
            elif i == 2:  # Third
                offset_x, offset_y = 8, 0
            elif i == 3:  # Fourth - offset to avoid #5
                offset_x, offset_y = -8, 8
            else:  # Fifth (worst) - offset to avoid #4
                offset_x, offset_y = 8, -8
                
            ax.annotate(f'{i+1}', 
                       (row['parameters'], row['hourly_success_rate']),
                       ha='center', va='center', fontsize=13, fontweight='bold', 
                       color='white', 
                       bbox=dict(boxstyle='circle,pad=0.2', facecolor='black', alpha=0.9),
                       xytext=(offset_x, offset_y), textcoords='offset points')
        
        # Plot the log-linear regression line using computed coefficients
        x_log_range = np.logspace(np.log10(df_filtered['parameters'].min()), 
                                 np.log10(df_filtered['parameters'].max()), 100)
        y_log_pred = log_reg_data['intercept'] + log_reg_data['coefficient'] * np.log10(x_log_range)
        
        # Use academic color scheme - navy blue for regression line
        ax.plot(x_log_range, y_log_pred, color='#1f4e79', linestyle='-', alpha=0.9, linewidth=2.5, 
                label=f"Log-linear fit (R² = {log_reg_data['r_squared']:.3f})")
        
        # Add confidence interval shading with subtle gray
        rmse = log_reg_data['rmse']
        y_upper = y_log_pred + 1.96 * rmse  # 95% confidence interval
        y_lower = y_log_pred - 1.96 * rmse
        ax.fill_between(x_log_range, y_lower, y_upper, alpha=0.15, color='#4a4a4a', 
                       label='95% Confidence Interval')
        
        # Add sample size to legend
        ax.plot([], [], ' ', label=f'n = {len(df_filtered)} models')
        
        # Set log scale for x-axis
        ax.set_xscale('log')
        ax.set_xlabel('Number of Model Parameters (Log Scale)', fontsize=12)
        ax.set_ylabel('Mean Hourly Success Rate (%, n=72)', fontsize=12)
        ax.set_title('Log-Linear Scaling Law: Language Model Performance in Greenhouse LED Optimization', fontsize=14, fontweight='bold')
        
        # Add equation text cleanly integrated into plot area
        equation_text = log_reg_data['equation']
        # Fix log₁₀ display issue by using LaTeX rendering
        equation_text_latex = equation_text.replace('log₁₀', r'log$_{10}$')
        ax.text(0.03, 0.97, equation_text_latex, transform=ax.transAxes, 
                fontsize=12, fontfamily='sans-serif', fontweight='normal',
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor='#4a4a4a', 
                         alpha=0.95, linewidth=0.5))
        
        # Add subtle light gray grid lines for easier reading
        ax.grid(True, alpha=0.4, color='lightgray', linestyle='-', linewidth=0.8)
        ax.legend(loc='lower right')
        
        # Create clean legend table on the right
        legend_ax.axis('off')  # Remove axes
        
        # Prepare clean model names for legend (use cleaner, shorter names)
        legend_data = []
        for i, (_, row) in enumerate(df_filtered.iterrows()):
            # Map to cleaner model names
            original_name_lower = row['original_name'].lower()
            if 'deepseek-r1-0528' in original_name_lower:
                clean_name = "DeepSeek-R1-0528"
            elif 'claude-3.7-sonnet' in original_name_lower:
                clean_name = "Claude-3.7-Sonnet"
            elif 'llama-3.3-70b-instruct' in original_name_lower:
                clean_name = "Llama-3.3-70B-Instruct"
            elif 'deepseek-r1-distill-qwen-7b' in original_name_lower:
                clean_name = "DeepSeek-R1-Distill-Qwen-7B"
            elif 'mistral-7b-instruct' in original_name_lower:
                clean_name = "Mistral-7B-Instruct"
            else:
                clean_name = row['model_name'].replace(' V2 Prompt', '').replace(' V1 Prompt', '').replace(' V0 Prompt', '')
            
            legend_data.append([f'{i+1}', clean_name, f"{row['parameters']:.0f}B", f"{row['hourly_success_rate']:.1f}%"])
        
        # Create legend table with better spacing
        legend_ax.text(0.05, 0.95, 'Model Legend', transform=legend_ax.transAxes, 
                      fontsize=14, fontweight='bold', verticalalignment='top')
        
        # Table headers with improved column positions
        headers = ['#', 'Model Name', 'Params', 'Success']
        header_y = 0.85
        col_positions = [0.05, 0.15, 0.75, 0.88]  # Better spacing
        
        for i, header in enumerate(headers):
            legend_ax.text(col_positions[i], header_y, header, transform=legend_ax.transAxes,
                          fontsize=11, fontweight='bold', verticalalignment='top')
        
        # Table data with improved spacing
        for i, row_data in enumerate(legend_data):
            y_pos = header_y - 0.12 * (i + 1)  # More vertical spacing
            for j, cell_data in enumerate(row_data):
                # Adjust text alignment for better fit
                ha = 'left' if j == 1 else 'center'  # Left align model names
                legend_ax.text(col_positions[j], y_pos, cell_data, transform=legend_ax.transAxes,
                              fontsize=10, verticalalignment='top', horizontalalignment=ha,
                              color=colors[i] if j == 0 else 'black',
                              fontweight='bold' if j == 0 else 'normal')
        
        # Add horizontal lines for table structure with better spacing
        for i in range(len(legend_data) + 2):  # +2 for header and one extra
            y_line = header_y + 0.02 - 0.12 * i  # Match the improved spacing
            if i == 1:  # Thicker line under header
                legend_ax.plot([0.05, 0.98], [y_line, y_line], transform=legend_ax.transAxes,
                              color='black', linewidth=1.5, alpha=0.8)
            else:
                legend_ax.plot([0.05, 0.98], [y_line, y_line], transform=legend_ax.transAxes,
                              color='lightgray', linewidth=0.5, alpha=0.6)
        
        plt.tight_layout()
        
        # Save figure
        figure_path = f"{RESULTS_DIRS['figures']}/figure_1-1_log_scaling_law_{timestamp}.png"
        plt.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Figure 1.1 (Log-Scale) saved: {figure_path}")
        return figure_path
        
    except Exception as e:
        print(f"❌ Error creating log scaling law plot: {e}")
        return None 