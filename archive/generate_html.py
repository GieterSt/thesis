import markdown
import os
import re

def generate_html(readme_path, output_path):
    """Converts the README markdown to a styled HTML file with corrected image paths."""
    print(f"Reading README from: {readme_path}")
    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # --- Path Correction Logic ---
    # Find all markdown image tags: ![alt text](path)
    # And add a '../' prefix to the path if it starts with 'results/'
    def correct_image_path(match):
        alt_text = match.group(1)
        path = match.group(2)
        if path.startswith('results/'):
            # Correct the path to be relative from the 'docs' directory
            corrected_path = f'../{path}'
            print(f"Correcting image path: '{path}' -> '{corrected_path}'")
            return f'![{alt_text}]({corrected_path})'
        return match.group(0) # Return original if no correction needed

    # Replace all occurrences in the readme content
    readme_content = re.sub(r'!\[(.*?)\]\((.*?)\)', correct_image_path, readme_content)

    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LLM Performance Analysis</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 20px auto; padding: 20px; }}
            h1, h2, h3 {{ border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #dfe2e5; padding: 8px 12px; text-align: left; }}
            th {{ background-color: #f6f8fa; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f6f8fa; }}
            code {{ background-color: #f1f1f1; padding: 0.2em 0.4em; margin: 0; font-size: 85%; border-radius: 3px; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
    
    html_content = markdown.markdown(readme_content, extensions=['markdown.extensions.tables'])
    
    final_html = html_template.format(content=html_content)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"✅ Successfully generated HTML report at: {output_path}")

if __name__ == '__main__':
    generate_html('README.md', 'docs/LLM_LED_Optimization_Research_Results.html') 