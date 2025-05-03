# Markdown-to-HTML

A Python script to convert Markdown files to HTML.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/BrittanyLouviere/Markdown-to-HTML.git
   cd Markdown-to-HTML
   ```

2. Install the required dependencies:
   ```
   pip install markdown
   ```

## Usage

The script can handle single files, multiple files, or directories:

```
python md2html.py [options] input [input ...]
```

### Options

- `-o, --output`: Specify the output directory (default: same as input)
- `--no-copy`: Do not copy non-markdown files to the output directory

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

## Features

- Converts Markdown files to HTML
- Handles single files, multiple files, or entire directories
- Maintains directory structure when processing directories
- Option to control whether non-markdown files are copied to the output
- Simple 1-to-1 translation without adding extra CSS, headers, footers, or JavaScript
