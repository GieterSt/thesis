import markdown
import weasyprint
from weasyprint import HTML, CSS
import os

# Read the README.md file
with open('README.md', 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# Convert markdown to HTML with extensions for tables
md = markdown.Markdown(extensions=['tables', 'toc', 'codehilite', 'fenced_code'])
html_content = md.convert(markdown_content)

# Create a complete HTML document with styling
html_doc = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LLM LED Optimization Research Results</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px 8px;
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
        tr:hover {{
            background-color: #e8f4f8;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        strong {{
            color: #2c3e50;
        }}
        @page {{
            margin: 0.8in;
            @top-center {{
                content: 'LLM LED Optimization Research Results';
                font-size: 10pt;
                color: #666;
            }}
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #666;
            }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
'''

# Convert HTML to PDF
print('Converting README.md to PDF...')
html = HTML(string=html_doc)
html.write_pdf('LLM_LED_Optimization_Research_Results.pdf')
print('✓ PDF generated successfully: LLM_LED_Optimization_Research_Results.pdf')
print('📄 File saved in current directory') 