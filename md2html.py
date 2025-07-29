#!/usr/bin/env python3

import argparse
import os
import shutil
import sys
import re
from pathlib import Path, PurePath
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


class MdFile:
    def __init__(self, input_dir:PurePath, input_path: PurePath, output_path: PurePath):
        self.input_path = input_path
        self.file_name = input_path.stem
        self.output_relative_path = input_path.relative_to(input_dir).with_suffix('.html')
        self.html_output_path = output_path / self.output_relative_path

md_files: list[MdFile]


def main():
    args = setup_argument_parser()
    configure_logging(args)

    mode = determine_file_mode(args)
    copy_files = not args.no_copy
    input_path = Path(args.input)
    output_path = Path(args.output)

    validate_paths(input_path, output_path)
    logging.debug(f"Input: {input_path}, Output: {output_path}, Copy files: {copy_files}, Mode: {mode}")
    logging.debug(f"Arguments validated. Inventorying files.")

    global md_files
    (
        md_files,
        jinja_files,
        other_files,
        directories
    ) = inventory_files(input_path, output_path)
    logging.debug(f"File inventory complete. Creating directories.")
    create_output_dirs(directories, output_path)
    logging.debug("Directories created. Loading templates.")
    loaded_templates = load_templates(jinja_files)
    logging.debug("Templates loaded. Processing markdown files.")

    file_success_count = 0
    failed_files = []

    for md_file in md_files:
        try:
            with open(md_file.input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            frontmatter, content_without_frontmatter = extract_yaml_frontmatter(md_content)
            template_path = select_template(md_file.input_path, list(loaded_templates.keys()), frontmatter, input_path)
            template = load_template(template_path)
            html_content = convert_md_to_html(content_without_frontmatter, frontmatter, template)

            with open(md_file.html_output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logging.debug(f"Converted: {md_file.input_path} -> {md_file.html_output_path}")
            file_success_count += 1
        except Exception as e:
            logging.error(f"Error processing {md_file.input_path}: {e}")
            failed_files.append(md_file.input_path)

    logging.debug("Finished processing markdown files. Processing other files.")

    for other_file in other_files:
        if copy_files:
            should_skip_file, mode = should_skip(other_file, output_path, mode)
            if should_skip_file:
                continue

            output_file_path = Path(output_path) / other_file.relative_to(input_path)
            try:
                shutil.copy2(other_file, output_file_path)
                logging.debug(f"Copied: {other_file} -> {output_file_path}")
                file_success_count += 1
            except Exception as e:
                logging.error(f"Error copying {other_file}: {e}")
                failed_files.append(other_file)
        else:
            logging.debug(f"Skipped non-markdown file: {other_file}")
            file_success_count += 1

    logging.debug("Finished processing other files.")
    logging.info(f"Processed {file_success_count} files.")
    if len(failed_files) > 0:
        logging.info(f"{len(failed_files)} file(s) failed to process.")
        for failed_file in failed_files:
            logging.info(f"\t{failed_file}")


def setup_argument_parser():
    parser = argparse.ArgumentParser(description='Convert Markdown files to HTML')
    parser.add_argument('input', help='Input markdown file(s) or directory')
    parser.add_argument('output', help='Output directory')
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


def inventory_files(input_dir: Path, output_dir: Path) -> (list[MdFile], list[PurePath], list[PurePath], list[PurePath]):
    md_files = []
    jinja_files = []
    other_files = []
    directories = []
    for item in input_dir.rglob('*'):
        if item.is_file():
            if item.suffix.lower() in ['.md', '.markdown']:
                md_files.append(MdFile(input_dir, item, output_dir))
            elif item.suffix.lower() == '.jinja':
                jinja_files.append(item)
            else:
                other_files.append(item)
        elif item.is_dir():
            directories.append(item.relative_to(input_dir))
    return (
        md_files,
        jinja_files,
        other_files,
        directories
    )


def create_output_dirs(directories: list[PurePath], output_path: PurePath):
    for directory in directories:
        os.makedirs(output_path / directory, exist_ok=True)


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


def load_templates(templates_list: list[PurePath]) -> dict[str, jinja2.Template]:
    templates_dict = {}
    for template_path in templates_list:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            templates_dict[str(template_path)] = jinja2.Template(template_content)
            logging.debug(f"Loaded template from {template_path}")
        except Exception as e:
            logging.error(f"Error loading template from {template_path}: {e}")

    templates_dict['DEFAULT'] = jinja2.Template(DEFAULT_TEMPLATE)
    logging.debug("Added default template to templates dictionary")

    return templates_dict


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


def select_template(input_file_path: PurePath, templates: list[str], frontmatter, input_dir: Path) -> str:
    # 1. Check if a template file is specified in frontmatter
    if frontmatter and 'template' in frontmatter:
        template_path = frontmatter['template']
        # Check if the specified template exists in our template list
        for t in templates:
            if template_path in t:
                logging.debug(f"Using template specified in frontmatter: {t}")
                return t

    # 2. Check if a .jinja file exists with the same name as the current file
    file_name = input_file_path.stem
    file_dir = input_file_path.parent

    for t in templates:
        template_path = Path(t)
        if template_path.stem == file_name and template_path.parent == file_dir:
            logging.debug(f"Using template with same name as file: {t}")
            return t

    # 3. Check parent directories recursively until we hit the input directory
    current_dir = file_dir
    while current_dir.name and (input_dir is None or current_dir.is_relative_to(input_dir)):
        dir_name = current_dir.name
        for t in templates:
            template_path = Path(t)
            if template_path.stem == dir_name:
                logging.debug(f"Using template with same name as directory: {t}")
                return t
        # Move up to parent directory
        current_dir = current_dir.parent

    # 4. If all else fails, use the DEFAULT_TEMPLATE
    logging.debug("No suitable template found, using DEFAULT template")
    return 'DEFAULT'


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


def convert_md_to_html(md_content, frontmatter, template):
    logging.debug("Starting markdown to HTML conversion")

    # Convert markdown to HTML
    html_body = markdown.markdown(
        md_content,
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

    html_content = template.render(**context)
    logging.debug("Template rendering completed")

    return html_content


def should_skip(input_path: PurePath, output_html_path: PurePath, mode):
    if input_path.suffix.lower() == '.jinja':
        return True, mode
    if output_html_path.exists():
        if mode == 'skip':
            logging.info(f"Skipped existing file: {output_html_path}")
            return True, mode
        elif mode == 'interactive':
            response = input(f"File {output_html_path} already exists. Overwrite? (y/N/o/s): ")
            if response.lower() == 'o':
                logging.info(f"Switching to overwrite mode")
                return False, 'overwrite'
            elif response.lower() == 's':
                logging.info(f"Switching to skip mode")
                return True, 'skip'
            elif response.lower() != 'y':
                logging.info(f"Skipped: {input_path}")
                return True, mode
    return False, mode


if __name__ == "__main__":
    main()
