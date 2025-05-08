#!/usr/bin/env python3
"""
Test script to verify that verbosity levels work correctly in md2html.py
"""

import os
import subprocess
import tempfile
import shutil

def run_command(cmd):
    """Run a command and return its output"""
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def main():
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a simple markdown file
        md_file = os.path.join(temp_dir, "test.md")
        with open(md_file, "w") as f:
            f.write("# Test Heading\n\nThis is a test markdown file.")

        # Test different verbosity levels
        print("Testing default verbosity (warnings and errors only):")
        stdout, stderr, _ = run_command(["python", "md2html.py", "--overwrite", md_file])
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        print("-" * 50)

        print("Testing quiet mode (errors only):")
        stdout, stderr, _ = run_command(["python", "md2html.py", "-q", "--overwrite", md_file])
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        print("-" * 50)

        print("Testing verbose mode (info, warnings, errors):")
        stdout, stderr, _ = run_command(["python", "md2html.py", "-v", "--overwrite", md_file])
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        print("-" * 50)

        print("Testing debug mode (debug, info, warnings, errors):")
        stdout, stderr, _ = run_command(["python", "md2html.py", "--debug", "--overwrite", md_file])
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
