#!/usr/bin/env python3
"""
Auto-update HTML from README.md

This script automatically regenerates the HTML file whenever README.md is updated.
Run this script after making changes to README.md to keep the HTML version current.

Usage:
    python scripts/utils/update_html.py
    (or from scripts/utils/: python update_html.py)
"""

import markdown
import os
from datetime import datetime
from pathlib import Path

def update_html_from_readme():
    """Update HTML file from current README.md content"""
    
    # Get the project root directory (two levels up from scripts/utils/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    readme_path = project_root / "README.md"
    docs_dir = project_root / "docs"
    
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
    </style>
</head>
<body>
{html_content}
<div class="timestamp">
    Generated from README.md on {timestamp}
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
    else:
        print("\n❌ HTML update failed") 