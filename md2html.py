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
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: The 'markdown' package is required. Install it with 'pip install markdown'")
    sys.exit(1)


def convert_md_to_html(md_content):
    """Convert markdown content to HTML."""
    # Use extensions to better handle code blocks, nested lists, and tables
    return markdown.markdown(
        md_content,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ]
    )


def process_file(input_file, output_file, copy_non_md=True):
    """Process a single file, converting if it's markdown or copying if specified."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)

    # Check if it's a markdown file
    if input_path.suffix.lower() in ['.md', '.markdown']:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_content = convert_md_to_html(md_content)

            with open(output_path.with_suffix('.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"Converted: {input_path} -> {output_path.with_suffix('.html')}")
            return True
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False
    elif copy_non_md:
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


def process_directory(input_dir, output_dir, copy_non_md=True):
    """Process all files in a directory recursively."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    success = True

    for item in input_path.rglob('*'):
        if item.is_file():
            # Calculate the relative path from input_dir to the file
            rel_path = item.relative_to(input_path)
            # Construct the output file path
            out_file = output_path / rel_path

            if not process_file(item, out_file, copy_non_md):
                success = False

    return success


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown files to HTML')
    parser.add_argument('input', nargs='+', help='Input markdown file(s) or directory')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('--no-copy', action='store_true', 
                        help='Do not copy non-markdown files to the output directory')

    args = parser.parse_args()

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

            process_file(path, output_file, not args.no_copy)

        elif path.is_dir():
            # For a directory
            if args.output:
                # If output is specified, use it as the base directory
                output_dir = output_base
            else:
                # Otherwise, use the input directory
                output_dir = path

            process_directory(path, output_dir, not args.no_copy)


if __name__ == "__main__":
    main()
