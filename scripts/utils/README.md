# Utility Scripts

This directory contains utility scripts for documentation generation and project maintenance.

## Scripts

### `update_html.py`
**Purpose**: Automatically convert README.md to HTML with professional formatting

**Usage**:
```bash
# From project root:
python scripts/utils/update_html.py

# From this directory:
python update_html.py
```

**Features**:
- Converts markdown to HTML with table support
- Professional styling optimized for print
- Automatic timestamp tracking
- Outputs to `docs/` directory
- Cross-references and syntax highlighting

**Output**: `docs/LLM_LED_Optimization_Research_Results.html`

### `simple_pdf_converter.py`
**Purpose**: Alternative HTML generation with PDF conversion options

**Usage**:
```bash
python simple_pdf_converter.py
```

**Features**:
- HTML generation with print-optimized CSS
- Attempts PDF conversion if wkhtmltopdf available
- Fallback instructions for browser-based PDF generation

### `convert_readme_to_pdf.py`
**Purpose**: Direct PDF conversion using WeasyPrint (requires additional dependencies)

**Usage**:
```bash
python convert_readme_to_pdf.py
```

**Requirements**:
- WeasyPrint library
- System font libraries (may need additional setup)

## Workflow

### For Regular Documentation Updates:

1. **Edit README.md** with new results or changes
2. **Run**: `python scripts/utils/update_html.py`
3. **Generate PDF**: Open `docs/LLM_LED_Optimization_Research_Results.html` in browser → ⌘+P → Save as PDF

### For One-time Setup:

1. **Install dependencies**: `pip install markdown weasyprint` (optional)
2. **Test HTML generation**: `python scripts/utils/update_html.py`
3. **Verify output**: Check `docs/` directory for HTML file

## Dependencies

**Required**:
- `markdown` - Markdown to HTML conversion
- `pathlib` - Cross-platform path handling

**Optional**:
- `weasyprint` - Direct PDF generation (may require system libraries)
- `wkhtmltopdf` - Alternative PDF generation (discontinued)

## Output Directory Structure

```
docs/
└── LLM_LED_Optimization_Research_Results.html  # Generated documentation
```

## Integration

These utilities are designed to maintain synchronized documentation:
- **HTML version**: For web viewing and easy PDF generation
- **Markdown source**: For version control and editing
- **Automatic updates**: One command to refresh all documentation 