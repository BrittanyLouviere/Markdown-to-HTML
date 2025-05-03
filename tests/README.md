# Markdown to HTML Converter Tests

This directory contains unit tests for the Markdown to HTML converter script (`md2html.py`).

## Test Structure

- `test_md2html.py`: Contains all the unit tests for the script
- `fixtures/`: Contains test fixtures (sample files) used by the tests
  - `simple.md`: A simple markdown file for basic testing
  - `data.txt`: A non-markdown file for testing the copy functionality
  - `nested/`: A nested directory structure for testing directory processing
    - `main.md`: A markdown file in the nested directory
    - `subdir/`: A subdirectory for testing nested directory handling
      - `sub.md`: A markdown file in the subdirectory

## Test Coverage

The tests cover all possible combinations of user inputs:

1. **Input Types**:
   - Single file input
   - Multiple file inputs
   - Directory input

2. **Output Options**:
   - With output directory
   - Without output directory (default)

3. **Copy Options**:
   - With copy of non-markdown files (default)
   - Without copy of non-markdown files (--no-copy flag)

4. **Error Handling**:
   - Non-existent input files/directories

## Running the Tests

To run all the tests:

```bash
python -m unittest discover tests
```

To run a specific test:

```bash
python -m unittest tests.test_md2html.TestMd2Html.test_convert_md_to_html
```

## Adding New Tests

If you need to add new tests:

1. Add any necessary test fixtures to the `fixtures/` directory
2. Add new test methods to the `TestMd2Html` class in `test_md2html.py`
3. Make sure to follow the naming convention `test_*` for test methods