import pytest
import os
import tempfile
import shutil
from pathlib import Path

# Import the functions to test
import sys
sys.path.append(str(Path(__file__).parent.parent))
from md2html import load_templates, select_template, load_template, DEFAULT_TEMPLATE


class TestLoadTemplates:
    @pytest.fixture
    def setup_templates(self):
        """Create temporary template files for testing."""
        temp_dir = tempfile.mkdtemp()

        # Create test template files
        template1_path = os.path.join(temp_dir, "template1.jinja")
        with open(template1_path, "w") as f:
            f.write("Template 1 content")

        template2_path = os.path.join(temp_dir, "template2.jinja")
        with open(template2_path, "w") as f:
            f.write("Template 2 content")

        # Create an invalid template file
        invalid_template_path = os.path.join(temp_dir, "invalid.jinja")
        with open(invalid_template_path, "w") as f:
            f.write("{{ unclosed tag")

        yield {
            'dir': Path(temp_dir),
            'template1': Path(template1_path),
            'template2': Path(template2_path),
            'invalid': Path(invalid_template_path)
        }

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_loading_valid_templates(self, setup_templates):
        """Test that valid templates are loaded correctly."""
        templates_list = [setup_templates['template1'], setup_templates['template2']]

        templates_dict = load_templates(templates_list)

        # Check that both templates are loaded
        assert str(setup_templates['template1']) in templates_dict
        assert str(setup_templates['template2']) in templates_dict

        # Check that the templates have the correct content
        assert "Template 1 content" in templates_dict[str(setup_templates['template1'])].render()
        assert "Template 2 content" in templates_dict[str(setup_templates['template2'])].render()

    def test_loading_invalid_templates(self, setup_templates):
        """Test that invalid templates are skipped but others are loaded."""
        templates_list = [setup_templates['template1'], setup_templates['invalid'], setup_templates['template2']]

        templates_dict = load_templates(templates_list)

        # Check that valid templates are loaded
        assert str(setup_templates['template1']) in templates_dict
        assert str(setup_templates['template2']) in templates_dict

        # Check that the invalid template is not loaded
        assert str(setup_templates['invalid']) not in templates_dict

    def test_default_template(self, setup_templates):
        """Test that the DEFAULT template is always included."""
        templates_list = [setup_templates['template1']]

        templates_dict = load_templates(templates_list)

        # Check that the DEFAULT template is included
        assert 'DEFAULT' in templates_dict

        # Check that the DEFAULT template has the correct content
        rendered = templates_dict['DEFAULT'].render(title="Test Title", content="Test Content")
        assert "Test Title" in rendered
        assert "Test Content" in rendered


class TestSelectTemplate:
    @pytest.fixture
    def setup_template_paths(self):
        """Create a list of template paths for testing."""
        return [
            "/path/to/templates/custom_template.jinja",
            "/path/to/templates/file_template.jinja",
            "/path/to/templates/dir_template.jinja",
            "DEFAULT"
        ]

    def test_frontmatter_template_selection(self, setup_template_paths):
        """Test that a template specified in frontmatter is selected."""
        input_file_path = Path("/path/to/input/file.md")
        frontmatter = {"template": "custom_template.jinja"}
        input_dir = Path("/path/to/input")

        template = select_template(input_file_path, setup_template_paths, frontmatter, input_dir)

        assert template == "/path/to/templates/custom_template.jinja"

    def test_same_name_template_selection(self):
        """Test that a template with the same name as the file is selected."""
        # Create a temporary directory structure for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory for our files
            file_dir = Path(temp_dir) / "files"
            file_dir.mkdir()

            # Create a template with the same name as our test file in the same directory
            template_path = file_dir / "test_file.jinja"
            with open(template_path, "w") as f:
                f.write("Template content")

            # Create a test markdown file
            md_file_path = file_dir / "test_file.md"
            with open(md_file_path, "w") as f:
                f.write("# Test Content")

            # Create another template to ensure we're selecting the right one
            other_template_path = file_dir / "other_template.jinja"
            with open(other_template_path, "w") as f:
                f.write("Other template content")

            # List of templates to pass to select_template
            templates = [
                str(template_path),
                str(other_template_path),
                "DEFAULT"
            ]

            # Call select_template with the test file
            template = select_template(md_file_path, templates, None, Path(temp_dir))

            # The template with the same name as the file should be selected
            assert template == str(template_path)

    def test_directory_based_template_selection(self, setup_template_paths):
        """Test that a template with the same name as the directory is selected."""
        # Create a simple test case where the directory name matches a template name
        templates = [
            "/path/to/templates/custom_template.jinja",
            "/path/to/templates/file_template.jinja",
            "/path/to/templates/dir_template.jinja",  # This should match
            "DEFAULT"
        ]

        # Create a temporary directory structure for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory with a name that matches a template
            dir_path = Path(temp_dir) / "dir_template"
            dir_path.mkdir()

            # Create a test file in the directory
            test_file = dir_path / "file.md"
            with open(test_file, "w") as f:
                f.write("Test content")

            # Call select_template with the test file
            template = select_template(test_file, templates, None, Path(temp_dir))

            # The template with the matching directory name should be selected
            assert template == "/path/to/templates/dir_template.jinja"

    def test_fallback_to_default(self, setup_template_paths):
        """Test that the DEFAULT template is used when no other matches are found."""
        # Create a simple test case where no template matches
        templates = [
            "/path/to/templates/custom_template.jinja",
            "/path/to/templates/file_template.jinja",
            "/path/to/templates/dir_template.jinja",
            "DEFAULT"  # This should be selected as fallback
        ]

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file with a name that doesn't match any template
            test_file = Path(temp_dir) / "no_match.md"
            with open(test_file, "w") as f:
                f.write("Test content")

            # Call select_template with the test file
            template = select_template(test_file, templates, None, Path(temp_dir))

            # The DEFAULT template should be selected as fallback
            assert template == "DEFAULT"


class TestLoadTemplate:
    @pytest.fixture
    def setup_template_file(self):
        """Create a temporary template file for testing."""
        temp_dir = tempfile.mkdtemp()
        template_path = os.path.join(temp_dir, "test_template.jinja")

        with open(template_path, "w") as f:
            f.write("Test template content: {{ title }}")

        yield Path(template_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_loading_existing_template(self, setup_template_file):
        """Test loading a template from an existing file."""
        template = load_template(setup_template_file)

        rendered = template.render(title="Test Title")
        assert "Test template content: Test Title" in rendered

    def test_loading_non_existent_template(self):
        """Test loading a template from a non-existent file."""
        template = load_template("/non/existent/template.jinja")

        # Should fall back to default template
        rendered = template.render(title="Test Title", content="Test Content")
        assert "Test Title" in rendered
        assert "Test Content" in rendered
        assert "<!DOCTYPE html>" in rendered

    def test_loading_with_no_path(self):
        """Test loading a template with no path provided."""
        template = load_template(None)

        # Should use default template
        rendered = template.render(title="Test Title", content="Test Content")
        assert "Test Title" in rendered
        assert "Test Content" in rendered
        assert "<!DOCTYPE html>" in rendered
