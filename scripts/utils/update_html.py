#!/usr/bin/env python3
"""
Auto-update HTML from README.md with embedded figures

This script automatically regenerates the HTML file whenever README.md is updated.
It also embeds any figures from docs/figures/ directory into the HTML.
Run this script after making changes to README.md to keep the HTML version current.

Usage:
    python scripts/utils/update_html.py
    (or from scripts/utils/: python update_html.py)
"""

import markdown
import os
import base64
from datetime import datetime
from pathlib import Path
import re

def encode_image_to_base64(image_path):
    """Convert image to base64 string for embedding in HTML"""
    try:
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding {image_path}: {e}")
        return None

def insert_figures_in_html(html_content, figures_dir):
    """Insert figure references into HTML content"""
    if not figures_dir.exists():
        print("📁 No figures directory found, skipping figure embedding")
        return html_content
    
    # Find all figure files
    figure_files = {}
    for fig_file in figures_dir.glob("figure_*.png"):
        fig_num = fig_file.stem.split('_')[1]  # Extract number from figure_1_xxx.png
        figure_files[fig_num] = fig_file
    
    if not figure_files:
        print("📁 No figures found in docs/figures/, skipping figure embedding")
        return html_content
    
    print(f"🖼️  Found {len(figure_files)} figures to embed")
    
    # Replace figure references with embedded images
    for fig_num, fig_path in figure_files.items():
        # Find references like "See Figure 1" or "(See Figure 1)"
        pattern = rf'\(See Figure {fig_num}\)'
        replacement_pattern = rf'See Figure {fig_num}'
        
        base64_data = encode_image_to_base64(fig_path)
        if base64_data:
            # Create the figure HTML with embedded image
            fig_html = f'''
<div class="figure-container">
    <img src="data:image/png;base64,{base64_data}" alt="Figure {fig_num}" class="research-figure">
    <p class="figure-caption"><strong>Figure {fig_num}:</strong> {get_figure_caption(fig_num)}</p>
</div>
'''
            
            # Insert figure after the paragraph that references it
            html_content = re.sub(
                pattern, 
                f'(See Figure {fig_num} below){fig_html}', 
                html_content
            )
            
            # Also handle cases without parentheses
            html_content = re.sub(
                replacement_pattern, 
                f'See Figure {fig_num} below{fig_html}', 
                html_content
            )
            
            print(f"✅ Embedded Figure {fig_num}")
    
    return html_content

def get_figure_caption(fig_num):
    """Get appropriate caption for each figure"""
    captions = {
        "1": "Performance with 95% Confidence Intervals and Daily PPFD Mean Absolute Error",
        "2": "Model Scale vs. Optimization Performance Correlation (r² = 0.91)",
        "3": "Error Analysis & Failure Modes across Different Model Types",
        "4": "Seasonal Performance Breakdown showing complexity variation",
        "5": "Prompt Evolution Impact on API Success, Accuracy, and JSON Compliance",
        "6": "Response Time Analysis and API Reliability Comparison",
        "7": "Cost-Performance Analysis with Efficiency Rankings and ROI"
    }
    return captions.get(fig_num, f"Research Figure {fig_num}")

def update_html_from_readme():
    """Update HTML file from current README.md content with embedded figures"""
    
    # Get the project root directory (two levels up from scripts/utils/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    readme_path = project_root / "README.md"
    docs_dir = project_root / "docs"
    figures_dir = docs_dir / "figures"
    
    # Check if README.md exists
    if not readme_path.exists():
        print(f"❌ README.md not found at {readme_path}")
        return False
    
    # Create docs directory if it doesn't exist
    docs_dir.mkdir(exist_ok=True)
    
    print("🔄 Updating HTML from README.md...")
    
    # Read the README.md file
    with open(readme_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert markdown to HTML with extensions for tables
    md = markdown.Markdown(extensions=['tables', 'toc', 'codehilite', 'fenced_code'])
    html_content = md.convert(markdown_content)
    
    # Insert figures into HTML
    html_content = insert_figures_in_html(html_content, figures_dir)

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create a complete HTML document with professional styling
    html_doc = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LLM LED Optimization Research Results</title>
    <meta name="generator" content="Auto-generated from README.md on {timestamp}">
    <style>
        @media print {{
            body {{ margin: 0.5in; }}
            .no-print {{ display: none; }}
            .research-figure {{ max-width: 100%; height: auto; }}
        }}
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            font-size: 14px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 28px;
        }}
        h2 {{
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 30px;
            font-size: 22px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 25px;
            font-size: 18px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 12px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 6px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
            font-size: 12px;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        li {{
            margin: 3px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        .timestamp {{
            color: #666;
            font-size: 12px;
            text-align: center;
            margin-top: 40px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
        
        /* Figure Styles */
        .figure-container {{
            margin: 30px 0;
            text-align: center;
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .research-figure {{
            max-width: 95%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .figure-caption {{
            font-size: 12px;
            color: #555;
            font-style: italic;
            margin: 10px 0 5px 0;
            text-align: center;
        }}
        .figure-caption strong {{
            color: #2c3e50;
            font-style: normal;
        }}
    </style>
</head>
<body>
{html_content}
<div class="timestamp">
    Generated from README.md on {timestamp}<br>
    📊 Research figures automatically embedded from analysis results
</div>
</body>
</html>
'''

    # Save HTML file in docs directory
    html_filename = docs_dir / 'LLM_LED_Optimization_Research_Results.html'
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_doc)

    print(f'✅ HTML updated successfully: {html_filename}')
    print(f'📅 Generated on: {timestamp}')
    return True

if __name__ == "__main__":
    success = update_html_from_readme()
    if success:
        print("\n💡 To create PDF:")
        print("   1. Open the HTML file in your browser")
        print("   2. Press ⌘+P → Save as PDF")
        print("\n🔄 Run this script anytime you update README.md to keep HTML current")
        print("📂 HTML file location: docs/LLM_LED_Optimization_Research_Results.html")
        print("🖼️  All research figures are now embedded in the HTML!")
    else:
        print("\n❌ HTML update failed") 