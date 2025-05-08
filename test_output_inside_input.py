#!/usr/bin/env python3
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Create a temporary directory for testing
temp_dir = tempfile.mkdtemp()
try:
    # Create a test input directory
    input_dir = Path(temp_dir) / "input"
    input_dir.mkdir()
    
    # Create a test markdown file
    test_md = input_dir / "test.md"
    with open(test_md, "w") as f:
        f.write("# Test\n\nThis is a test markdown file.")
    
    # Create an output directory inside the input directory
    output_dir = input_dir / "output"
    output_dir.mkdir()
    
    print(f"Testing with input_dir={input_dir} and output_dir={output_dir}")
    
    # Run the md2html.py script with the output directory inside the input directory
    cmd = ["python", "md2html.py", str(input_dir), "-o", str(output_dir)]
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output
    print("\nCommand output:")
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
    
    # Check if the error was detected
    if result.returncode != 0 and "inside input directory" in result.stderr:
        print("\nTest PASSED: The script correctly detected that the output directory is inside the input directory.")
    else:
        print("\nTest FAILED: The script did not detect that the output directory is inside the input directory.")
        
finally:
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)