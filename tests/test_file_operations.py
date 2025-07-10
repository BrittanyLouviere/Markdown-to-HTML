import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Import the functions to test
import sys
sys.path.append(str(Path(__file__).parent.parent))
from md2html import validate_paths, inventory_files, create_output_dirs, should_skip


class TestValidatePaths:
    def test_non_existent_input_path(self):
        """Test that a FileNotFoundError is raised for non-existent input path."""
        with pytest.raises(FileNotFoundError):
            validate_paths(Path('/non/existent/path'), Path('/output/path'))

    def test_same_input_and_output_path(self, tmp_path):
        """Test that a ValueError is raised when input and output paths are the same."""
        input_path = tmp_path / "test_dir"
        input_path.mkdir()
        
        with pytest.raises(ValueError):
            validate_paths(input_path, input_path)

    def test_output_inside_input(self, tmp_path):
        """Test that a ValueError is raised when output path is inside input path."""
        input_path = tmp_path / "test_dir"
        input_path.mkdir()
        output_path = input_path / "output"
        
        with pytest.raises(ValueError):
            validate_paths(input_path, output_path)

    def test_valid_paths(self, tmp_path):
        """Test that no exception is raised for valid distinct paths."""
        input_path = tmp_path / "input"
        input_path.mkdir()
        output_path = tmp_path / "output"
        
        # This should not raise an exception
        validate_paths(input_path, output_path)


class TestInventoryFiles:
    @pytest.fixture
    def setup_test_directory(self):
        """Create a temporary directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        os.makedirs(os.path.join(temp_dir, "subdir"))
        
        # Create test files
        with open(os.path.join(temp_dir, "test.md"), "w") as f:
            f.write("# Test Markdown")
        
        with open(os.path.join(temp_dir, "test.markdown"), "w") as f:
            f.write("# Test Markdown with .markdown extension")
        
        with open(os.path.join(temp_dir, "template.jinja"), "w") as f:
            f.write("Template content")
        
        with open(os.path.join(temp_dir, "other.txt"), "w") as f:
            f.write("Other content")
        
        with open(os.path.join(temp_dir, "subdir", "nested.md"), "w") as f:
            f.write("# Nested Markdown")
        
        yield Path(temp_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_empty_directory(self, tmp_path):
        """Test that empty lists are returned for an empty directory."""
        result = inventory_files(tmp_path)
        
        assert len(result['md_files']) == 0
        assert len(result['jinja_files']) == 0
        assert len(result['other_files']) == 0
        assert len(result['directories']) == 0

    def test_mixed_content_directory(self, setup_test_directory):
        """Test that files are correctly categorized in a directory with mixed content."""
        result = inventory_files(setup_test_directory)
        
        # Check counts
        assert len(result['md_files']) == 3  # test.md, test.markdown, subdir/nested.md
        assert len(result['jinja_files']) == 1  # template.jinja
        assert len(result['other_files']) == 1  # other.txt
        assert len(result['directories']) == 1  # subdir
        
        # Check specific files
        md_files = [os.path.basename(str(f)) for f in result['md_files']]
        assert 'test.md' in md_files
        assert 'test.markdown' in md_files
        assert any('nested.md' in str(f) for f in result['md_files'])
        
        jinja_files = [os.path.basename(str(f)) for f in result['jinja_files']]
        assert 'template.jinja' in jinja_files
        
        other_files = [os.path.basename(str(f)) for f in result['other_files']]
        assert 'other.txt' in other_files

    def test_nested_directories(self, setup_test_directory):
        """Test that files in nested directories are found."""
        result = inventory_files(setup_test_directory)
        
        # Check that the nested markdown file is found
        nested_md_found = any('subdir/nested.md' in str(f) for f in result['md_files'])
        assert nested_md_found
        
        # Check that the subdirectory is listed
        assert Path('subdir') in result['directories']

    def test_file_extensions(self, setup_test_directory):
        """Test that files are correctly categorized by extension."""
        result = inventory_files(setup_test_directory)
        
        # Check that .md and .markdown files are in md_files
        md_files = [str(f) for f in result['md_files']]
        assert any(f.endswith('.md') for f in md_files)
        assert any(f.endswith('.markdown') for f in md_files)
        
        # Check that .jinja files are in jinja_files
        jinja_files = [str(f) for f in result['jinja_files']]
        assert all(f.endswith('.jinja') for f in jinja_files)
        
        # Check that other files are in other_files
        other_files = [str(f) for f in result['other_files']]
        assert any(f.endswith('.txt') for f in other_files)


class TestCreateOutputDirs:
    def test_creating_single_directory(self, tmp_path):
        """Test creating a single directory."""
        output_path = tmp_path / "output"
        directories = [Path("test_dir")]
        
        create_output_dirs(directories, output_path)
        
        assert (output_path / "test_dir").exists()
        assert (output_path / "test_dir").is_dir()

    def test_creating_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        output_path = tmp_path / "output"
        directories = [Path("parent"), Path("parent/child"), Path("parent/child/grandchild")]
        
        create_output_dirs(directories, output_path)
        
        assert (output_path / "parent").exists()
        assert (output_path / "parent" / "child").exists()
        assert (output_path / "parent" / "child" / "grandchild").exists()

    def test_creating_existing_directories(self, tmp_path):
        """Test creating directories that already exist."""
        output_path = tmp_path / "output"
        output_path.mkdir()
        test_dir = output_path / "test_dir"
        test_dir.mkdir()
        
        directories = [Path("test_dir")]
        
        # This should not raise an exception
        create_output_dirs(directories, output_path)
        
        assert test_dir.exists()


class TestShouldSkip:
    def test_jinja_file(self):
        """Test that .jinja files are always skipped."""
        input_path = Path("test.jinja")
        output_path = Path("output.html")
        
        should_skip_result, mode = should_skip(input_path, output_path, "interactive")
        
        assert should_skip_result is True
        assert mode == "interactive"

    def test_skip_mode_with_existing_file(self, tmp_path):
        """Test that files are skipped in skip mode."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "skip")
        
        assert should_skip_result is True
        assert mode == "skip"

    def test_overwrite_mode_with_existing_file(self, tmp_path):
        """Test that files are not skipped in overwrite mode."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "overwrite")
        
        assert should_skip_result is False
        assert mode == "overwrite"

    @patch('builtins.input', return_value='y')
    def test_interactive_mode_yes_response(self, mock_input, tmp_path):
        """Test interactive mode with 'y' response."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "interactive")
        
        assert should_skip_result is False
        assert mode == "interactive"

    @patch('builtins.input', return_value='n')
    def test_interactive_mode_no_response(self, mock_input, tmp_path):
        """Test interactive mode with 'n' response."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "interactive")
        
        assert should_skip_result is True
        assert mode == "interactive"

    @patch('builtins.input', return_value='o')
    def test_interactive_mode_overwrite_response(self, mock_input, tmp_path):
        """Test interactive mode with 'o' response."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "interactive")
        
        assert should_skip_result is False
        assert mode == "overwrite"

    @patch('builtins.input', return_value='s')
    def test_interactive_mode_skip_response(self, mock_input, tmp_path):
        """Test interactive mode with 's' response."""
        input_path = Path("test.md")
        output_path = tmp_path / "output.html"
        
        # Create the output file
        with open(output_path, "w") as f:
            f.write("Test content")
        
        should_skip_result, mode = should_skip(input_path, output_path, "interactive")
        
        assert should_skip_result is True
        assert mode == "skip"