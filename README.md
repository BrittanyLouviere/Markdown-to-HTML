# Markdown-to-HTML

A Python script to convert Markdown files to HTML.

## Features

- Converts Markdown files to HTML
- Handles single files, multiple files, or entire directories
- Maintains directory structure when processing directories
- Option to control whether non-markdown files are copied to the output
- Jinja2 templating for customizable HTML output
- Default template provides simple 1-to-1 translation without extra CSS, headers, footers, or JavaScript
- Extracts YAML frontmatter from markdown files and converts it to HTML meta tags
- Supports footnotes in markdown content

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/BrittanyLouviere/Markdown-to-HTML.git
   cd Markdown-to-HTML
   ```

2. Install the required dependencies:
   ```
   pip install markdown pyyaml jinja2
   ```

## Usage

The script can handle single files, multiple files, or directories:

```
python md2html.py [options] input [input ...]
```

### Options

- `-o, --output`: Specify the output directory (default: same as input)
  - Note: The output directory cannot be inside the input directory when processing directories, as this would cause an infinite loop
- `-t, --template`: Specify a Jinja2 HTML template file to use for rendering
- `--no-copy`: Do not copy non-markdown files to the output directory
- `-s, --skip`: Skip files that already exist
- `-w, --overwrite`: Overwrite all existing files without asking
- `-i, --interactive`: Ask before overwriting existing files (default) - default answer is 'no'

#### Verbosity Options

- `-q, --quiet`: Show only error messages
- `-v, --verbose`: Show informational messages
- `--debug`: Show debug messages
- Default: Show only error and warning messages

### Examples

1. Convert a single file:
   ```
   python md2html.py document.md
   ```

2. Convert multiple files:
   ```
   python md2html.py file1.md file2.md file3.md
   ```

3. Convert all files in a directory (maintaining directory structure):
   ```
   python md2html.py input_directory/
   ```

4. Convert files to a specific output directory:
   ```
   python md2html.py input_directory/ -o output_directory/
   ```

5. Convert files without copying non-markdown files:
   ```
   python md2html.py input_directory/ -o output_directory/ --no-copy
   ```

6. Skip files that already exist:
   ```
   python md2html.py input_directory/ --skip
   # Or using the short form:
   python md2html.py input_directory/ -s
   ```

7. Overwrite all existing files without asking:
   ```
   python md2html.py input_directory/ --overwrite
   # Or using the short form:
   python md2html.py input_directory/ -w
   ```

8. Interactive mode (default) - ask before overwriting each file (default answer is 'no'):
   ```
   python md2html.py input_directory/ --interactive
   # Or using the short form:
   python md2html.py input_directory/ -i
   ```

9. Using verbosity options:
   ```
   # Quiet mode - show only error messages
   python md2html.py input_directory/ -q

   # Verbose mode - show informational messages
   python md2html.py input_directory/ -v

   # Debug mode - show debug messages
   python md2html.py input_directory/ --debug
   ```

10. Using a custom HTML template:
   ```
   python md2html.py input_directory/ -t my_template.html
   ```

## Jinja2 Templating

The script uses Jinja2 templating to generate HTML output. By default, a simple HTML template is used that includes:
- Basic HTML structure
- Meta tags for YAML frontmatter
- The converted markdown content

You can provide your own template using the `-t` or `--template` option. Your template should be a valid Jinja2 template and can access the following variables:

- `content`: The HTML content converted from markdown
- `meta_tags`: A list of HTML meta tags generated from the YAML frontmatter
- Any variables defined in the YAML frontmatter

For example, if your markdown file has frontmatter with `title` and `author` fields, you can access these directly in your template:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <meta name="author" content="{{ author }}">
    {% for meta_tag in meta_tags %}
    {{ meta_tag }}
    {% endfor %}
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
        {% if author %}
        <p class="author">By {{ author }}</p>
        {% endif %}
    </header>
    <main>
        {{ content }}
    </main>
    <footer>
        <p>&copy; {{ author }}</p>
    </footer>
</body>
</html>
```

## YAML Frontmatter

The script supports YAML frontmatter in markdown files. YAML frontmatter is a block of YAML at the beginning of a markdown file, delimited by triple dashes (`---`). For example:

```markdown
---
title: My Document
author: John Doe
date: 2023-01-01
tags:
  - markdown
  - yaml
  - frontmatter
---

# My Document

This is the content of my document.
```

When converting a markdown file with YAML frontmatter to HTML, the script:
1. Extracts the YAML frontmatter from the markdown content
2. Converts the YAML frontmatter to HTML meta tags
3. Ensures the YAML frontmatter is not included in the visible HTML content

The resulting HTML will include meta tags for each key-value pair in the frontmatter:

```html
<meta name="title" content="My Document">
<meta name="author" content="John Doe">
<meta name="date" content="2023-01-01">
<meta name="tags" content="markdown, yaml, frontmatter">
<h1>My Document</h1>
<p>This is the content of my document.</p>
```
