import os
import sys
import markdown

def convert_md_to_html(input_file, output_file=None):
    """
    Convert a Markdown file to HTML.
    
    Args:
        input_file (str): Path to the input Markdown file
        output_file (str, optional): Path to the output HTML file. 
            If None, uses the same name as input with .html extension
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file '{input_file}' not found")

        # If no output file specified, create one from input filename
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.html'

        # Read the Markdown file
        with open(input_file, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

        # Create basic HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(input_file)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as html_file:
            html_file.write(html_template)

        print(f"Successfully converted '{input_file}' to '{output_file}'")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    # Check if command line argument is provided
    if len(sys.argv) < 2:
        print("Usage: python script.py input.md [output.html]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    convert_md_to_html(input_file, output_file)

if __name__ == "__main__":
    main()
