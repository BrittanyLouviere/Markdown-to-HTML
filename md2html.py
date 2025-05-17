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
import os.path

try:
    import markdown
    import yaml
    import jinja2
except ImportError as import_error:
    if 'yaml' in str(import_error):
        logging.error("The 'pyyaml' package is required. Install it with 'pip install pyyaml'")
    elif 'jinja2' in str(import_error):
        logging.error("The 'jinja2' package is required. Install it with 'pip install jinja2'")
    else:
        logging.error("The 'markdown' package is required. Install it with 'pip install markdown'")
    sys.exit(1)


# Default HTML template
DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title|default('Document') }}</title>
    {% for meta_tag in meta_tags %}
    {{ meta_tag }}
    {% endfor %}
</head>
<body>
{{ content }}
</body>
</html>
"""

def load_template(template_path=None):
    if template_path and os.path.exists(template_path):
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            logging.debug(f"Loaded template from {template_path}")
            return jinja2.Template(template_content)
        except Exception as e:
            logging.error(f"Error loading template from {template_path}: {e}")
            logging.warning("Falling back to default template")

    # Use default template if no template path provided or loading failed
    logging.debug("Using default template")
    return jinja2.Template(DEFAULT_TEMPLATE)


def extract_yaml_frontmatter(md_content):
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

def convert_md_to_html(md_content, template_path=None):
    logging.debug("Starting markdown to HTML conversion")

    # Extract YAML frontmatter if present
    frontmatter, content_without_frontmatter = extract_yaml_frontmatter(md_content)

    # Convert markdown to HTML
    html_body = markdown.markdown(
        content_without_frontmatter,
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.footnotes',
            'mdx_wikilink_plus'
        ],
        extension_configs={
            'mdx_wikilink_plus': {
                'url_whitespace': ' ',
                'end_url': '.html',
            },
        }
    )
    logging.debug("Markdown conversion completed")

    # Prepare template context
    context = {
        'content': html_body,
        'meta_tags': []
    }

    # If frontmatter was found, add it to the context
    if frontmatter:
        logging.debug("Processing frontmatter for template")
        # Add frontmatter values to context
        context.update(frontmatter)

        # Create meta tags
        for key, value in frontmatter.items():
            # Convert the value to a string and escape any quotes
            if isinstance(value, list):
                # Convert lists to comma-separated strings
                value = ', '.join(str(item) for item in value)
            elif isinstance(value, dict):
                # Keep dictionaries as YAML
                value = yaml.dump(value, default_flow_style=False)
            str_value = str(value).replace('"', '&quot;')
            context['meta_tags'].append(f'<meta name="{key}" content="{str_value}">')

        logging.debug(f"Added {len(context['meta_tags'])} meta tags to context")

    # Load template and render HTML
    template = load_template(template_path)
    html_content = template.render(**context)
    logging.debug("Template rendering completed")

    return html_content

def should_skip(input_path, output_html_path, mode):
    if output_html_path.exists():
        if mode == 'skip':
            logging.info(f"Skipped existing file: {output_html_path}")
            return True
        elif mode == 'interactive':
            # TODO add option to skip or overwrite all
            response = input(f"File {output_html_path} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                logging.info(f"Skipped: {input_path}")
                return True
    return False

def process_file(input_file, output_file, copy_non_md=True, mode='interactive', template=None):
    input_path = Path(input_file)
    output_path = Path(output_file)

    logging.debug(f"Processing file: {input_path} -> {output_path}")

    # Create output directory if it doesn't exist
    os.makedirs(output_path.parent, exist_ok=True)
    logging.debug(f"Ensured output directory exists: {output_path.parent}")

    # Check if it's a markdown file
    if input_path.suffix.lower() in ['.md', '.markdown']:
        output_html_path = output_path.with_suffix('.html')

        if should_skip(input_path, output_html_path, mode): return True

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            html_content = convert_md_to_html(md_content, template)

            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logging.info(f"Converted: {input_path} -> {output_html_path}")
            return True
        except Exception as e:
            logging.error(f"Error processing {input_path}: {e}")
            return False
    elif copy_non_md:
        if should_skip(input_path, output_path, mode): return True

        try:
            shutil.copy2(input_path, output_path)
            logging.info(f"Copied: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logging.error(f"Error copying {input_path}: {e}")
            return False
    else:
        logging.info(f"Skipped non-markdown file: {input_path}")
        return True


def process_directory(input_dir: Path, output_dir: Path, copy_non_md=True, mode='interactive', template=None):
    input_path = input_dir.resolve()
    output_path = output_dir.resolve()

    success = True
    file_success_count = 0
    file_failed_count = 0

    for item in input_path.rglob('*'):
        if item.is_file():
            # Calculate the relative path from input_dir to the file
            rel_path = item.relative_to(input_path)
            # Construct the output file path
            out_file = output_path / rel_path

            logging.debug(f"Found file: {rel_path}")

            if process_file(item, out_file, copy_non_md, mode, template):
                file_success_count += 1
            else:
                file_failed_count += 1
                success = False

    logging.debug(f"Directory processing complete. Processed {file_success_count} files.")
    logging.debug(f"{file_failed_count} files failed to process.")
    return success


def validate_paths(input_path, output_path):
    # Check if input directory exists
    if not input_path.exists():
        logging.error(f"{input_path} does not exist")
        raise FileNotFoundError(f"{input_path} does not exist")

    # Check if output directory is the same as input directory
    if output_path == input_path:
        error_msg = f"Output directory '{output_path}' cannot be the same as input directory '{input_path}'."
        raise ValueError(error_msg)

    # Check if output directory is inside input directory
    if output_path.is_relative_to(input_path):
        error_msg = f"Output directory '{output_path}' cannot be inside input directory '{input_path}'."
        raise ValueError(error_msg)


def setup_argument_parser():
    parser = argparse.ArgumentParser(description='Convert Markdown files to HTML')
    parser.add_argument('input', help='Input markdown file(s) or directory')
    parser.add_argument('output', help='Output directory')
    parser.add_argument('-t', '--template', help='Path to a Jinja2 HTML template file')
    parser.add_argument('--no-copy', action='store_true',
                        help='Do not copy non-markdown files to the output directory')

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-s', '--skip', action='store_true',
                            help='Skip files that already exist')
    mode_group.add_argument('-w', '--overwrite', action='store_true',
                            help='Overwrite all existing files without asking')
    mode_group.add_argument('-i', '--interactive', action='store_true',
                            help='Ask before overwriting existing files (default)')

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-q', '--quiet', action='store_true',
                                 help='Show only error messages')
    verbosity_group.add_argument('-v', '--verbose', action='store_true',
                                 help='Show informational messages')
    verbosity_group.add_argument('--debug', action='store_true',
                                 help='Show debug messages')
    return parser.parse_args()


def configure_logging(args):
    level = (logging.DEBUG if args.debug else
             logging.INFO if args.verbose else
             logging.ERROR if args.quiet else
             logging.WARNING)

    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    logging.debug(f"Arguments: {args}")


def determine_file_mode(args):
    if args.skip:
        return 'skip'
    elif args.overwrite:
        return 'overwrite'
    return 'interactive'


def main():
    args = setup_argument_parser()
    configure_logging(args)

    mode = determine_file_mode(args)
    copy_files = not args.no_copy
    input_path = Path(args.input)
    output_path = Path(args.output)
    template_path = args.template

    validate_paths(input_path, output_path)
    logging.debug(f"Arguments validated. Starting processing.")
    logging.debug(f"Input: {input_path}, Output: {output_path}, Copy files: {copy_files}, Mode: {mode}, Template: {template_path}")
    process_directory(input_path, output_path, copy_files, mode, template_path)


if __name__ == "__main__":
    main()
