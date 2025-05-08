#!/usr/bin/env python3
"""
Test script to verify that the fix for the same-file copying issue works.
This script creates a test file, runs md2html.py on it without specifying
an output directory (which should place the output in the same directory),
and then runs it again with overwrite mode to ensure it doesn't try to
copy a file to itself.
"""

import os
import subprocess
import tempfile
from pathlib import Path

# Create a temporary directory for testing
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Create a test markdown file
    test_md_file = temp_path / "test.md"
    with open(test_md_file, "w") as f:
        f.write("# Test Heading\n\nThis is a test markdown file.")
    
    # Create a test non-markdown file
    test_txt_file = temp_path / "test.txt"
    with open(test_txt_file, "w") as f:
        f.write("This is a test text file.")
    
    print(f"Created test files in {temp_path}")
    
    # Run md2html.py on the directory without specifying output (first run)
    print("\n--- First run ---")
    cmd = ["python", "md2html.py", str(temp_path), "-w", "-v"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    print("Output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Run md2html.py again with overwrite mode (second run)
    print("\n--- Second run (should not show file copying errors) ---")
    cmd = ["python", "md2html.py", str(temp_path), "-w", "-v"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    print("Output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # List files in the temp directory to verify results
    print("\n--- Files in temp directory after processing ---")
    for file in temp_path.iterdir():
        print(f"- {file.name}")

print("\nTest completed.")