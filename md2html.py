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
import logging

try:
    import markdown
    import yaml
except ImportError as e:
    if 'yaml' in str(e):
        logging.error("The 'pyyaml' package is required. Install it with 'pip install pyyaml'")
    else:
        logging.error("The 'markdown' package is required. Install it with 'pip install markdown'")
    sys.exit(1)


def extract_yaml_frontmatter(md_content):
    """Extract YAML frontmatter from markdown content.

    Returns a tuple of (frontmatter_dict, content_without_frontmatter)
    If no frontmatter is found, returns (None, original_content)
    """
    logging.debug("Checking for YAML frontmatter")

    # Regular expression to match YAML frontmatter
    # It should be at the start of the file, between two sets of triple dashes
    frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

    match = frontmatter_pattern.match(md_content)
    if match:
        # Extract the YAML content
        yaml_content = match.group(1)
        logging.debug("Found YAML frontmatter")

        try:
            # Parse the YAML content
            frontmatter = yaml.safe_load(yaml_content)
            logging.debug(f"Parsed frontmatter: {frontmatter}")

            # Remove the frontmatter from the markdown content
            content_without_frontmatter = md_content[match.end():]
            return frontmatter, content_without_frontmatter
        except yaml.YAMLError as e:
            # If YAML parsing fails, assume it's not valid frontmatter
            logging.warning(f"Failed to parse YAML frontmatter: {e}")
            return None, md_content
    else:
        # No frontmatter found
        logging.debug("No YAML frontmatter found")
        return None, md_content


def convert_md_to_html(md_content):
    """Convert markdown content to HTML."""
    logging.debug("Starting markdown to HTML conversion")

    # Extract YAML frontmatter if present
    frontmatter, content_without_frontmatter = extract_yaml_frontmatter(md_content)

    # List of extensions to use
    extensions = [
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.footnotes'
    ]
    logging.debug(f"Using markdown extensions: {extensions}")

    # Convert markdown to HTML
    html_content = markdown.markdown(
        content_without_frontmatter,
        extensions=extensions
    )
    logging.debug("Markdown conversion completed")

    # If frontmatter was found, add it as meta tags
    if frontmatter:
        logging.debug("Adding frontmatter as meta tags")
        meta_tags = []
        for key, value in frontmatter.items():
            # Convert the value to a string and escape any quotes
            if isinstance(value, list):
                # Convert lists to comma-separated strings
                value = ', '.join(str(item) for item in value)
                logging.debug(f"Converted list to string for key '{key}': {value}")
            elif isinstance(value, dict):
                # Keep dictionaries as YAML
                value = yaml.dump(value, default_flow_style=False)
                logging.debug(f"Converted dict to YAML for key '{key}'")
            str_value = str(value).replace('"', '&quot;')
            meta_tags.append(f'<meta name="{key}" content="{str_value}">')

        # Add the meta tags to the beginning of the HTML content
        html_content = '\n'.join(meta_tags) + '\n' + html_content
        logging.debug(f"Added {len(meta_tags)} meta tags to HTML")

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

    logging.debug(f"Processing file: {input_path} -> {output_path}")
    logging.debug(f"Parameters: copy_non_md={copy_non_md}, mode={mode}")

    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)
    logging.debug(f"Ensured output directory exists: {output_path.parent}")

    # Check if it's a markdown file
    if input_path.suffix.lower() in ['.md', '.markdown']:
        output_html_path = output_path.with_suffix('.html')

        # Check if output file already exists
        if output_html_path.exists():
            if mode == 'skip':
                logging.info(f"Skipped existing file: {output_html_path}")
                return True
            elif mode == 'interactive':
                response = input(f"File {output_html_path} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    logging.info(f"Skipped: {input_path}")
                    return True
            # For 'overwrite' mode, we proceed without asking

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_content = convert_md_to_html(md_content)

            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logging.info(f"Converted: {input_path} -> {output_html_path}")
            return True
        except Exception as e:
            logging.error(f"Error processing {input_path}: {e}")
            return False
    elif copy_non_md:
        # For non-markdown files, check if the output file already exists
        if output_path.exists():
            if mode == 'skip':
                logging.info(f"Skipped existing file: {output_path}")
                return True
            elif mode == 'interactive':
                response = input(f"File {output_path} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    logging.info(f"Skipped: {input_path}")
                    return True

        try:
            # Skip copying if source and destination are the same file
            if input_path.resolve() == output_path.resolve():
                logging.info(f"Skipped copying to self: {input_path}")
                return True

            shutil.copy2(input_path, output_path)
            logging.info(f"Copied: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logging.error(f"Error copying {input_path}: {e}")
            return False
    else:
        logging.info(f"Skipped non-markdown file: {input_path}")
        return True


def process_directory(input_dir, output_dir, copy_non_md=True, mode='interactive'):
    """Process all files in a directory recursively.

    Args:
        input_dir: Path to the input directory
        output_dir: Path to the output directory
        copy_non_md: Whether to copy non-markdown files
        mode: How to handle existing files ('skip', 'overwrite', or 'interactive')

    Raises:
        ValueError: If the output directory is inside the input directory
    """
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()

    logging.debug(f"Processing directory: {input_path} -> {output_path}")
    logging.debug(f"Parameters: copy_non_md={copy_non_md}, mode={mode}")

    # Check if output directory is inside input directory
    try:
        if output_path != input_path and output_path.is_relative_to(input_path):
            error_msg = f"Output directory '{output_path}' is inside input directory '{input_path}'. This would cause an infinite loop."
            raise ValueError(error_msg)
    except AttributeError:
        # For Python < 3.9 that doesn't have is_relative_to
        if str(output_path).startswith(str(input_path + os.sep)) and output_path != input_path:
            error_msg = f"Output directory '{output_path}' is inside input directory '{input_path}'. This would cause an infinite loop."
            raise ValueError(error_msg)

    success = True
    file_count = 0

    for item in input_path.rglob('*'):
        if item.is_file():
            file_count += 1
            # Calculate the relative path from input_dir to the file
            rel_path = item.relative_to(input_path)
            # Construct the output file path
            out_file = output_path / rel_path

            logging.debug(f"Found file: {rel_path}")

            if not process_file(item, out_file, copy_non_md, mode):
                success = False

    logging.debug(f"Directory processing complete. Processed {file_count} files.")
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

    # Add verbosity options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-q', '--quiet', action='store_true',
                        help='Show only error messages')
    verbosity_group.add_argument('-v', '--verbose', action='store_true',
                        help='Show informational messages')
    verbosity_group.add_argument('--debug', action='store_true',
                        help='Show debug messages')

    args = parser.parse_args()

    # Configure logging based on verbosity level
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    elif args.quiet:
        log_level = logging.ERROR
    else:
        # Default: show warnings and errors
        log_level = logging.WARNING

    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Log the arguments in debug mode
    logging.debug(f"Arguments: {args}")

    # Determine the file handling mode
    if args.skip:
        mode = 'skip'
    elif args.overwrite:
        mode = 'overwrite'
    else:
        # Default to interactive mode
        mode = 'interactive'

    # Process each input
    logging.debug("Starting to process input paths")

    for input_path in args.input:
        path = Path(input_path)
        logging.debug(f"Processing input path: {path}")

        if not path.exists():
            logging.error(f"{path} does not exist")
            continue

        # Determine output path
        if args.output:
            output_base = Path(args.output)
        else:
            output_base = path.parent

        logging.debug(f"Output base path: {output_base}")

        if path.is_file():
            # For a single file
            if args.output:
                # If output is specified, use it as the directory
                output_file = output_base / path.name
            else:
                # Otherwise, output to the same directory
                output_file = path

            logging.debug(f"Processing single file: {path} -> {output_file}")
            try:
                process_file(path, output_file, not args.no_copy, mode)
                logging.debug(f"Completed processing file: {path}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif path.is_dir():
            # For a directory
            if args.output:
                # If output is specified, use it as the base directory
                output_dir = output_base
            else:
                # Otherwise, use the input directory
                output_dir = path

            logging.debug(f"Processing directory: {path} -> {output_dir}")
            try:
                process_directory(path, output_dir, not args.no_copy, mode)
                logging.debug(f"Completed processing directory: {path}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

    logging.debug("All input paths processed")


if __name__ == "__main__":
    main()
