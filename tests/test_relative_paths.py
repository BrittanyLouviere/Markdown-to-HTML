import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Import the functions to test
sys.path.append(str(Path(__file__).parent.parent))
from md2html import inventory_files, validate_paths, load_templates, main

class TestRelativePaths:
    @pytest.fixture
    def setup_test_directory(self):
        """Create a temporary directory structure for testing."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Create a subdirectory for input
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir)

        # Create a subdirectory for output
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir)

        # Create test files in input directory
        with open(os.path.join(input_dir, "test.md"), "w") as f:
            f.write("# Test Markdown")

        with open(os.path.join(input_dir, "template.jinja"), "w") as f:
            f.write("Template content")

        # Save the current working directory
        original_cwd = os.getcwd()

        # Change to the temporary directory
        os.chdir(temp_dir)

        yield {
            "temp_dir": temp_dir,
            "input_dir": "input",  # Relative path
            "output_dir": "output",  # Relative path
            "original_cwd": original_cwd
        }

        # Change back to the original directory
        os.chdir(original_cwd)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_relative_paths(self, setup_test_directory):
        """Test that the program can handle relative paths for input and output directories."""
        # Get the test directory information
        input_dir = Path(setup_test_directory["input_dir"])
        output_dir = Path(setup_test_directory["output_dir"])

        # Validate the paths (this should not raise an exception)
        validate_paths(input_dir, output_dir)

        # Inventory the files in the input directory
        result = inventory_files(input_dir)

        # Check that the files were found
        assert len(result['md_files']) == 1  # test.md
        assert len(result['jinja_files']) == 1  # template.jinja
        assert len(result['other_files']) == 0
        assert len(result['directories']) == 0

        # Check specific files
        md_files = [os.path.basename(str(f)) for f in result['md_files']]
        assert 'test.md' in md_files

        jinja_files = [os.path.basename(str(f)) for f in result['jinja_files']]
        assert 'template.jinja' in jinja_files

    def test_load_templates_with_relative_paths(self, setup_test_directory):
        """Test that templates can be loaded when using relative paths."""
        # Get the test directory information
        input_dir = Path(setup_test_directory["input_dir"])

        # Inventory the files in the input directory
        result = inventory_files(input_dir)

        # Load the templates
        templates = load_templates(result['jinja_files'])

        # Check that the template was loaded
        assert len(templates) == 2  # One template file + DEFAULT
        assert 'DEFAULT' in templates

        # Check that the template content is correct
        template_path = str([path for path in templates.keys() if path != 'DEFAULT'][0])
        assert 'template.jinja' in template_path

    def test_main_with_relative_paths(self, setup_test_directory, monkeypatch):
        """Test that the main function works with relative paths."""
        # Get the test directory information
        input_dir = setup_test_directory["input_dir"]
        output_dir = setup_test_directory["output_dir"]

        # Mock the command line arguments
        import sys
        monkeypatch.setattr(sys, 'argv', ['md2html.py', input_dir, output_dir])

        # Run the main function
        try:
            main()
            # If we get here, the test passed
            assert True
        except Exception as e:
            # If we get an exception, the test failed
            assert False, f"main() raised an exception: {e}"

        # Check that the output file was created
        output_file = os.path.join(output_dir, 'test.html')
        assert os.path.exists(output_file), f"Output file {output_file} was not created"
