#!/usr/bin/env python3
"""
Unit tests for the md2html.py script.

These tests cover all possible combinations of user inputs:
- Single file input vs. multiple file inputs vs. directory input
- With output directory vs. without output directory
- With no-copy flag vs. without no-copy flag
- Valid inputs vs. invalid inputs (non-existent files/directories)
"""

import os
import sys
import unittest
import tempfile
import shutil
import io
from unittest.mock import patch
from pathlib import Path

# Add the parent directory to the path so we can import md2html
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import md2html


class TestMd2Html(unittest.TestCase):
    """Test cases for the md2html.py script."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()

        # Get the path to the fixtures directory
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

        # Paths to test files
        self.simple_md = os.path.join(self.fixtures_dir, 'simple.md')
        self.data_txt = os.path.join(self.fixtures_dir, 'data.txt')
        self.nested_dir = os.path.join(self.fixtures_dir, 'nested')
        self.main_md = os.path.join(self.nested_dir, 'main.md')
        self.sub_md = os.path.join(self.nested_dir, 'subdir', 'sub.md')

        # Ensure test files exist
        self.assertTrue(os.path.exists(self.simple_md), f"Test file {self.simple_md} does not exist")
        self.assertTrue(os.path.exists(self.data_txt), f"Test file {self.data_txt} does not exist")
        self.assertTrue(os.path.exists(self.nested_dir), f"Test directory {self.nested_dir} does not exist")
        self.assertTrue(os.path.exists(self.main_md), f"Test file {self.main_md} does not exist")
        self.assertTrue(os.path.exists(self.sub_md), f"Test file {self.sub_md} does not exist")

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_convert_md_to_html(self):
        """Test the markdown to HTML conversion function."""
        with open(self.simple_md, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = md2html.convert_md_to_html(md_content)

        # Check that the HTML contains expected elements
        self.assertIn("<h1>Simple Test</h1>", html_content)
        self.assertIn("<li>List item 1</li>", html_content)
        self.assertIn("<code class=\"language-python\">", html_content)

    def test_process_single_file(self):
        """Test processing a single markdown file."""
        output_file = os.path.join(self.temp_dir, 'simple.md')

        # Process the file
        result = md2html.process_file(self.simple_md, output_file)

        # Check that the processing was successful
        self.assertTrue(result)

        # Check that the output HTML file exists
        output_html = os.path.join(self.temp_dir, 'simple.html')
        self.assertTrue(os.path.exists(output_html))

        # Check the content of the output file
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.assertIn("<h1>Simple Test</h1>", html_content)

    def test_process_single_file_no_copy(self):
        """Test processing a single non-markdown file with no-copy option."""
        output_file = os.path.join(self.temp_dir, 'data.txt')

        # Process the file with copy_non_md=False
        result = md2html.process_file(self.data_txt, output_file, copy_non_md=False)

        # Check that the processing was successful (should return True even if skipped)
        self.assertTrue(result)

        # Check that the output file does not exist (since it was skipped)
        self.assertFalse(os.path.exists(output_file))

    def test_process_single_file_with_copy(self):
        """Test processing a single non-markdown file with copy option."""
        output_file = os.path.join(self.temp_dir, 'data.txt')

        # Process the file with copy_non_md=True
        result = md2html.process_file(self.data_txt, output_file, copy_non_md=True)

        # Check that the processing was successful
        self.assertTrue(result)

        # Check that the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check the content of the output file
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        with open(self.data_txt, 'r', encoding='utf-8') as f:
            original_content = f.read()

        self.assertEqual(content, original_content)

    def test_process_directory(self):
        """Test processing a directory."""
        # Process the directory
        result = md2html.process_directory(self.nested_dir, self.temp_dir)

        # Check that the processing was successful
        self.assertTrue(result)

        # Check that the output files exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'subdir', 'sub.html')))

        # Check the content of the output files
        with open(os.path.join(self.temp_dir, 'main.html'), 'r', encoding='utf-8') as f:
            main_html = f.read()

        with open(os.path.join(self.temp_dir, 'subdir', 'sub.html'), 'r', encoding='utf-8') as f:
            sub_html = f.read()

        self.assertIn("<h1>Main Markdown File</h1>", main_html)
        self.assertIn("<h1>Subdirectory Markdown File</h1>", sub_html)

    def test_process_directory_no_copy(self):
        """Test processing a directory with no-copy option."""
        # Create a non-markdown file in the nested directory for testing
        test_txt = os.path.join(self.nested_dir, 'test.txt')
        with open(test_txt, 'w', encoding='utf-8') as f:
            f.write("Test file")

        try:
            # Process the directory with copy_non_md=False
            result = md2html.process_directory(self.nested_dir, self.temp_dir, copy_non_md=False)

            # Check that the processing was successful
            self.assertTrue(result)

            # Check that the markdown files were converted
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'subdir', 'sub.html')))

            # Check that the non-markdown file was not copied
            self.assertFalse(os.path.exists(os.path.join(self.temp_dir, 'test.txt')))
        finally:
            # Clean up the test file
            if os.path.exists(test_txt):
                os.remove(test_txt)

    def test_nonexistent_input(self):
        """Test handling of non-existent input files."""
        nonexistent_file = os.path.join(self.fixtures_dir, 'nonexistent.md')
        output_file = os.path.join(self.temp_dir, 'nonexistent.md')

        # Attempt to process a non-existent file
        result = md2html.process_file(nonexistent_file, output_file)

        # Check that the processing failed
        self.assertFalse(result)

        # Check that the output file was not created
        self.assertFalse(os.path.exists(output_file))

    def test_multiple_files(self):
        """Test processing multiple files by calling process_file multiple times."""
        output_file1 = os.path.join(self.temp_dir, 'simple.md')
        output_file2 = os.path.join(self.temp_dir, 'main.md')

        # Process the files
        result1 = md2html.process_file(self.simple_md, output_file1)
        result2 = md2html.process_file(self.main_md, output_file2)

        # Check that the processing was successful
        self.assertTrue(result1)
        self.assertTrue(result2)

        # Check that the output HTML files exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'simple.html')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_single_file(self, mock_stdout):
        """Test the main function with a single file input."""
        # Save original sys.argv
        original_argv = sys.argv

        try:
            # Set up the command-line arguments
            sys.argv = ['md2html.py', self.simple_md, '-o', self.temp_dir]

            # Call the main function
            md2html.main()

            # Check that the output file exists
            output_html = os.path.join(self.temp_dir, 'simple.html')
            self.assertTrue(os.path.exists(output_html))

            # Check that the output contains the expected message
            output = mock_stdout.getvalue()
            self.assertIn(f"Converted: {self.simple_md}", output)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_multiple_files(self, mock_stdout):
        """Test the main function with multiple file inputs."""
        # Save original sys.argv
        original_argv = sys.argv

        try:
            # Set up the command-line arguments
            sys.argv = ['md2html.py', self.simple_md, self.main_md, '-o', self.temp_dir]

            # Call the main function
            md2html.main()

            # Check that the output files exist
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'simple.html')))
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))

            # Check that the output contains the expected messages
            output = mock_stdout.getvalue()
            self.assertIn(f"Converted: {self.simple_md}", output)
            self.assertIn(f"Converted: {self.main_md}", output)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_directory(self, mock_stdout):
        """Test the main function with a directory input."""
        # Save original sys.argv
        original_argv = sys.argv

        try:
            # Set up the command-line arguments
            sys.argv = ['md2html.py', self.nested_dir, '-o', self.temp_dir]

            # Call the main function
            md2html.main()

            # Check that the output files exist
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'subdir', 'sub.html')))

            # Check that the output contains the expected messages
            output = mock_stdout.getvalue()
            self.assertIn(f"Converted: {self.main_md}", output)
            self.assertIn(f"Converted: {self.sub_md}", output)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_no_copy(self, mock_stdout):
        """Test the main function with the --no-copy option."""
        # Create a non-markdown file in the nested directory for testing
        test_txt = os.path.join(self.nested_dir, 'test.txt')
        with open(test_txt, 'w', encoding='utf-8') as f:
            f.write("Test file")

        # Save original sys.argv
        original_argv = sys.argv

        try:
            # Set up the command-line arguments
            sys.argv = ['md2html.py', self.nested_dir, '-o', self.temp_dir, '--no-copy']

            # Call the main function
            md2html.main()

            # Check that the markdown files were converted
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'main.html')))
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'subdir', 'sub.html')))

            # Check that the non-markdown file was not copied
            self.assertFalse(os.path.exists(os.path.join(self.temp_dir, 'test.txt')))

            # Check that the output contains the expected messages
            output = mock_stdout.getvalue()
            self.assertIn(f"Converted: {self.main_md}", output)
            self.assertIn(f"Converted: {self.sub_md}", output)
            self.assertIn(f"Skipped non-markdown file: {test_txt}", output)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
            # Clean up the test file
            if os.path.exists(test_txt):
                os.remove(test_txt)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_nonexistent_input(self, mock_stdout):
        """Test the main function with a non-existent input."""
        nonexistent_file = os.path.join(self.fixtures_dir, 'nonexistent.md')

        # Save original sys.argv
        original_argv = sys.argv

        try:
            # Set up the command-line arguments
            sys.argv = ['md2html.py', nonexistent_file]

            # Call the main function
            md2html.main()

            # Check that the output contains the expected error message
            output = mock_stdout.getvalue()
            self.assertIn(f"Error: {nonexistent_file} does not exist", output)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv


if __name__ == '__main__':
    unittest.main()
