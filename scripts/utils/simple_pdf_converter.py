import markdown
import os

# Read the README.md file
with open('README.md', 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# Convert markdown to HTML with extensions for tables
md = markdown.Markdown(extensions=['tables', 'toc', 'codehilite', 'fenced_code'])
html_content = md.convert(markdown_content)

# Create a complete HTML document with professional styling
html_doc = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LLM LED Optimization Research Results</title>
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
    </style>
</head>
<body>
{html_content}
</body>
</html>
'''

# Save HTML file
html_filename = 'LLM_LED_Optimization_Research_Results.html'
with open(html_filename, 'w', encoding='utf-8') as f:
    f.write(html_doc)

print(f'✓ HTML file generated: {html_filename}')
print('📄 You can:')
print('   1. Open the HTML file in your browser')
print('   2. Print to PDF using your browser (⌘+P → Save as PDF)')
print('   3. Or use: wkhtmltopdf if available')

# Try to use system wkhtmltopdf if available
try:
    import subprocess
    result = subprocess.run(['which', 'wkhtmltopdf'], capture_output=True, text=True)
    if result.returncode == 0:
        print('\\n🔄 Attempting PDF conversion with wkhtmltopdf...')
        pdf_result = subprocess.run([
            'wkhtmltopdf', 
            '--page-size', 'A4',
            '--margin-top', '0.75in',
            '--margin-right', '0.75in',
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--print-media-type',
            html_filename,
            'LLM_LED_Optimization_Research_Results.pdf'
        ], capture_output=True, text=True)
        
        if pdf_result.returncode == 0:
            print('✅ PDF generated successfully: LLM_LED_Optimization_Research_Results.pdf')
        else:
            print(f'❌ PDF conversion failed: {pdf_result.stderr}')
    else:
        print('\\n💡 To generate PDF directly, install wkhtmltopdf:')
        print('   brew install wkhtmltopdf')
except Exception as e:
    print(f'\\n⚠️  Error checking for wkhtmltopdf: {e}')

 