#!/usr/bin/env python3
"""
Markdown to HTML converter

This script converts Markdown files to HTML files. It can handle single files,
multiple files, or directories. When processing directories, it maintains the
directory structure in the output.
"""

import argparse
import os
import shutil
import sys
import re
from pathlib import Path

try:
    import markdown
    import yaml
except ImportError as e:
    if 'yaml' in str(e):
        print("Error: The 'pyyaml' package is required. Install it with 'pip install pyyaml'")
    else:
        print("Error: The 'markdown' package is required. Install it with 'pip install markdown'")
    sys.exit(1)


def extract_yaml_frontmatter(md_content):
    """Extract YAML frontmatter from markdown content.

    Returns a tuple of (frontmatter_dict, content_without_frontmatter)
    If no frontmatter is found, returns (None, original_content)
    """
    # Regular expression to match YAML frontmatter
    # It should be at the start of the file, between two sets of triple dashes
    frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

    match = frontmatter_pattern.match(md_content)
    if match:
        # Extract the YAML content
        yaml_content = match.group(1)
        try:
            # Parse the YAML content
            frontmatter = yaml.safe_load(yaml_content)
            # Remove the frontmatter from the markdown content
            content_without_frontmatter = md_content[match.end():]
            return frontmatter, content_without_frontmatter
        except yaml.YAMLError:
            # If YAML parsing fails, assume it's not valid frontmatter
            return None, md_content
    else:
        # No frontmatter found
        return None, md_content


def convert_md_to_html(md_content):
    """Convert markdown content to HTML."""
    # Extract YAML frontmatter if present
    frontmatter, content_without_frontmatter = extract_yaml_frontmatter(md_content)

    # Convert markdown to HTML
    html_content = markdown.markdown(
        content_without_frontmatter,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.footnotes'
        ]
    )

    # If frontmatter was found, add it as meta tags
    if frontmatter:
        meta_tags = []
        for key, value in frontmatter.items():
            # Convert the value to a string and escape any quotes
            if isinstance(value, list):
                # Convert lists to comma-separated strings
                value = ', '.join(str(item) for item in value)
            elif isinstance(value, dict):
                # Keep dictionaries as YAML
                value = yaml.dump(value, default_flow_style=False)
            str_value = str(value).replace('"', '&quot;')
            meta_tags.append(f'<meta name="{key}" content="{str_value}">')

        # Add the meta tags to the beginning of the HTML content
        html_content = '\n'.join(meta_tags) + '\n' + html_content

    return html_content


def process_file(input_file, output_file, copy_non_md=True, mode='interactive'):
    """Process a single file, converting if it's markdown or copying if specified.

    Args:
        input_file: Path to the input file
        output_file: Path to the output file
        copy_non_md: Whether to copy non-markdown files
        mode: How to handle existing files ('skip', 'overwrite', or 'interactive')
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)

    # Check if it's a markdown file
    if input_path.suffix.lower() in ['.md', '.markdown']:
        output_html_path = output_path.with_suffix('.html')

        # Check if output file already exists
        if output_html_path.exists():
            if mode == 'skip':
                print(f"Skipped existing file: {output_html_path}")
                return True
            elif mode == 'interactive':
                response = input(f"File {output_html_path} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print(f"Skipped: {input_path}")
                    return True
            # For 'overwrite' mode, we proceed without asking

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_content = convert_md_to_html(md_content)

            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"Converted: {input_path} -> {output_html_path}")
            return True
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False
    elif copy_non_md:
        # For non-markdown files, check if the output file already exists
        if output_path.exists():
            if mode == 'skip':
                print(f"Skipped existing file: {output_path}")
                return True
            elif mode == 'interactive':
                response = input(f"File {output_path} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print(f"Skipped: {input_path}")
                    return True

        try:
            shutil.copy2(input_path, output_path)
            print(f"Copied: {input_path} -> {output_path}")
            return True
        except Exception as e:
            print(f"Error copying {input_path}: {e}")
            return False
    else:
        print(f"Skipped non-markdown file: {input_path}")
        return True


def process_directory(input_dir, output_dir, copy_non_md=True, mode='interactive'):
    """Process all files in a directory recursively.

    Args:
        input_dir: Path to the input directory
        output_dir: Path to the output directory
        copy_non_md: Whether to copy non-markdown files
        mode: How to handle existing files ('skip', 'overwrite', or 'interactive')
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    success = True

    for item in input_path.rglob('*'):
        if item.is_file():
            # Calculate the relative path from input_dir to the file
            rel_path = item.relative_to(input_path)
            # Construct the output file path
            out_file = output_path / rel_path

            if not process_file(item, out_file, copy_non_md, mode):
                success = False

    return success


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown files to HTML')
    parser.add_argument('input', nargs='+', help='Input markdown file(s) or directory')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('--no-copy', action='store_true', 
                        help='Do not copy non-markdown files to the output directory')

    # Add a mutually exclusive group for file handling modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-s', '--skip', action='store_true',
                        help='Skip files that already exist')
    mode_group.add_argument('-w', '--overwrite', action='store_true',
                        help='Overwrite all existing files without asking')
    mode_group.add_argument('-i', '--interactive', action='store_true',
                        help='Ask before overwriting existing files (default)')

    args = parser.parse_args()

    # Determine the file handling mode
    if args.skip:
        mode = 'skip'
    elif args.overwrite:
        mode = 'overwrite'
    else:
        # Default to interactive mode
        mode = 'interactive'

    # Process each input
    for input_path in args.input:
        path = Path(input_path)

        if not path.exists():
            print(f"Error: {path} does not exist")
            continue

        # Determine output path
        if args.output:
            output_base = Path(args.output)
        else:
            output_base = path.parent

        if path.is_file():
            # For a single file
            if args.output:
                # If output is specified, use it as the directory
                output_file = output_base / path.name
            else:
                # Otherwise, output to the same directory
                output_file = path

            process_file(path, output_file, not args.no_copy, mode)

        elif path.is_dir():
            # For a directory
            if args.output:
                # If output is specified, use it as the base directory
                output_dir = output_base
            else:
                # Otherwise, use the input directory
                output_dir = path

            process_directory(path, output_dir, not args.no_copy, mode)


if __name__ == "__main__":
    main()
