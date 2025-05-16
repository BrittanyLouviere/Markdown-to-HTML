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

try:
    import markdown
    import yaml
    import jinja2
except ImportError as e:
    if 'yaml' in str(e):
        logging.error("The 'pyyaml' package is required. Install it with 'pip install pyyaml'")
    elif 'jinja2' in str(e):
        logging.error("The 'jinja2' package is required. Install it with 'pip install jinja2'")
    else:
        logging.error("The 'markdown' package is required. Install it with 'pip install markdown'")
    sys.exit(1)


def load_template(template_path=None):
    """Load a Jinja2 template from a file or use the default template.

    Args:
        template_path: Path to the template file (optional)

    Returns:
        A Jinja2 Template object
    """
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


def convert_md_to_html(md_content, template_path=None):
    """Convert markdown content to HTML using a template.

    Args:
        md_content: The markdown content to convert
        template_path: Path to a Jinja2 template file (optional)

    Returns:
        The rendered HTML content
    """
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
        'markdown.extensions.footnotes',
        'mdx_wikilink_plus'
    ]
    # Configuration for extensions
    ext_configs = {
        'mdx_wikilink_plus': {
            'url_whitespace': ' ',
            'end_url': '.html',
        },
    }
    logging.debug(f"Using markdown extensions: {extensions}")

    # Convert markdown to HTML
    html_body = markdown.markdown(
        content_without_frontmatter,
        extensions=extensions,
        extension_configs=ext_configs
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
                logging.debug(f"Converted list to string for key '{key}': {value}")
            elif isinstance(value, dict):
                # Keep dictionaries as YAML
                value = yaml.dump(value, default_flow_style=False)
                logging.debug(f"Converted dict to YAML for key '{key}'")
            str_value = str(value).replace('"', '&quot;')
            context['meta_tags'].append(f'<meta name="{key}" content="{str_value}">')

        logging.debug(f"Added {len(context['meta_tags'])} meta tags to context")

    # Load template and render HTML
    template = load_template(template_path)
    html_content = template.render(**context)
    logging.debug("Template rendering completed")

    return html_content


def process_file(input_file, output_file, copy_non_md=True, mode='interactive', template=None):
    """Process a single file, converting if it's markdown or copying if specified.

    Args:
        input_file: Path to the input file
        output_file: Path to the output file
        copy_non_md: Whether to copy non-markdown files
        mode: How to handle existing files ('skip', 'overwrite', or 'interactive')
        template: Path to a Jinja2 template file (optional)
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

            html_content = convert_md_to_html(md_content, template)

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
            shutil.copy2(input_path, output_path)
            logging.info(f"Copied: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logging.error(f"Error copying {input_path}: {e}")
            return False
    else:
        logging.info(f"Skipped non-markdown file: {input_path}")
        return True


def process_directory(input_dir, output_dir, copy_non_md=True, mode='interactive', template=None):
    """Process all files in a directory recursively.

    Args:
        input_dir: Path to the input directory
        output_dir: Path to the output directory
        copy_non_md: Whether to copy non-markdown files
        mode: How to handle existing files ('skip', 'overwrite', or 'interactive')
        template: Path to a Jinja2 template file (optional)

    Raises:
        ValueError: If the output directory is inside the input directory
    """
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()

    logging.debug(f"Processing directory: {input_path} -> {output_path}")
    logging.debug(f"Parameters: copy_non_md={copy_non_md}, mode={mode}")

    # Check if output directory is the same as input directory
    if output_path == input_path:
        error_msg = f"Output directory '{output_path}' cannot be the same as input directory '{input_path}'."
        raise ValueError(error_msg)

    # Check if output directory is inside input directory
    try:
        if output_path.is_relative_to(input_path):
            error_msg = f"Output directory '{output_path}' is inside input directory '{input_path}'. This would cause an infinite loop."
            raise ValueError(error_msg)
    except AttributeError:
        # For Python < 3.9 that doesn't have is_relative_to
        if str(output_path).startswith(str(input_path + os.sep)):
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

            if not process_file(item, out_file, copy_non_md, mode, template):
                success = False

    logging.debug(f"Directory processing complete. Processed {file_count} files.")
    return success


def setup_argument_parser():
    parser = argparse.ArgumentParser(description='Convert Markdown files to HTML')
    parser.add_argument('input', nargs='+', help='Input markdown file(s) or directory')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
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
    log_levels = {
        'debug': logging.DEBUG,
        'verbose': logging.INFO,
        'quiet': logging.ERROR,
        'default': logging.WARNING
    }

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


def determine_output_path(input_path, output_base):
    return output_base / input_path.name if input_path.is_file() else output_base


def process_input_path(input_path, output_base, copy_files, mode, template=None):
    path = Path(input_path)
    if not path.exists():
        logging.error(f"{path} does not exist")
        return

    logging.debug(f"Processing input path: {path}")
    output_path = determine_output_path(path, output_base)

    try:
        if path.is_file():
            process_file(path, output_path, copy_files, mode, template)
        elif path.is_dir():
            process_directory(path, output_path, copy_files, mode, template)
        logging.debug(f"Completed processing: {path}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    args = setup_argument_parser()
    configure_logging(args)

    mode = determine_file_mode(args)
    copy_files = not args.no_copy
    output_base = Path(args.output)
    template_path = args.template

    logging.debug("Starting to process input paths")
    for input_path in args.input:
        process_input_path(input_path, output_base, copy_files, mode, template_path)
    logging.debug("All input paths processed")


if __name__ == "__main__":
    main()
