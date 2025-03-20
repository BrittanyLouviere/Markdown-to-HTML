import os
import sys
import markdown
import shutil
from pathlib import Path


def convert_md_to_html(input_path, output_path):
    """
    Convert a single Markdown file to HTML.

    Args:
        input_path (str): Path to the input Markdown file
        output_path (str): Path to the output HTML file
    """
    try:
        # Read the Markdown file
        with open(input_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

        # Create basic HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(input_path)}</title>
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

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as html_file:
            html_file.write(html_template)

        print(f"Converted: {input_path} -> {output_path}")

    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}")


def process_single_file(input_file, output_path=None):
    """
    Process a single Markdown file.

    Args:
        input_file (str): Path to the input Markdown file
        output_path (str, optional): Path to the output HTML file or directory
    """
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_file}' not found")

    if not input_path.is_file():
        raise ValueError(f"Input '{input_file}' is not a file")

    if input_path.suffix.lower() != '.md':
        raise ValueError(f"Input file '{input_file}' is not a Markdown file (.md)")

    # Determine output path
    if output_path is None:
        output_file = input_path.with_suffix('.html')
    elif Path(output_path).is_dir():
        output_file = Path(output_path) / input_path.with_suffix('.html').name
    else:
        output_file = Path(output_path)

    convert_md_to_html(str(input_path), str(output_file))


def process_directory(input_dir, output_dir):
    """
    Process a directory recursively.

    Args:
        input_dir (str): Path to input directory
        output_dir (str): Path to output directory
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' not found")

    if not input_path.is_dir():
        raise ValueError(f"Input '{input_dir}' is not a directory")

    for item in input_path.rglob('*'):
        relative_path = item.relative_to(input_path)
        output_item = output_path / relative_path

        if item.is_file():
            if item.suffix.lower() == '.md':
                output_html = output_item.with_suffix('.html')
                convert_md_to_html(str(item), str(output_html))
            else:
                output_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, output_item)
                print(f"Copied: {item} -> {output_item}")


def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python md_to_html.py input.md [output.html|output_dir]")
        print("  Directory:   python md_to_html.py input_dir output_dir")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    try:
        if input_path.is_file():
            # Single file mode
            output_path = sys.argv[2] if len(sys.argv) > 2 else None
            process_single_file(sys.argv[1], output_path)
        else:
            # Directory mode
            if len(sys.argv) < 3:
                print("Error: Output directory required for directory processing")
                print("Usage: python script.py input_dir output_dir")
                sys.exit(1)
            process_directory(sys.argv[1], sys.argv[2])

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()