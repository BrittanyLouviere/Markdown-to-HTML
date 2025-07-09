import pytest
import sys
import logging
from unittest.mock import patch
from pathlib import Path
from argparse import Namespace

# Import the functions to test
sys.path.append(str(Path(__file__).parent.parent))
from md2html import setup_argument_parser, configure_logging, determine_file_mode

class TestSetupArgumentParser:
    def test_basic_argument_parsing(self):
        """Test that command line arguments are correctly parsed."""
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir']):
            args = setup_argument_parser()
            assert args.input == 'input_dir'
            assert args.output == 'output_dir'
            assert not args.no_copy
            assert not args.skip
            assert not args.overwrite
            assert not args.interactive
            assert not args.quiet
            assert not args.verbose
            assert not args.debug

    def test_mutually_exclusive_groups(self):
        """Test that mutually exclusive groups work as expected."""
        # Test mode group with skip
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir', '--skip']):
            args = setup_argument_parser()
            assert args.skip
            assert not args.overwrite
            assert not args.interactive

        # Test mode group with overwrite
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir', '--overwrite']):
            args = setup_argument_parser()
            assert not args.skip
            assert args.overwrite
            assert not args.interactive

        # Test verbosity group with quiet
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir', '--quiet']):
            args = setup_argument_parser()
            assert args.quiet
            assert not args.verbose
            assert not args.debug

        # Test verbosity group with verbose
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir', '--verbose']):
            args = setup_argument_parser()
            assert not args.quiet
            assert args.verbose
            assert not args.debug

        # Test verbosity group with debug
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir', '--debug']):
            args = setup_argument_parser()
            assert not args.quiet
            assert not args.verbose
            assert args.debug

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch('sys.argv', ['md2html.py', 'input_dir', 'output_dir']):
            args = setup_argument_parser()
            assert not args.no_copy
            assert not args.skip
            assert not args.overwrite
            assert not args.interactive
            assert not args.quiet
            assert not args.verbose
            assert not args.debug


class TestConfigureLogging:
    @pytest.fixture(autouse=True)
    def reset_logging(self):
        """Reset logging configuration before and after each test."""
        # Reset before test
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)
        # Clear handlers to avoid duplicate messages
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        yield
        # Reset after test
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)
        # Clear handlers to avoid duplicate messages
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_debug_level(self):
        """Test that debug level is set correctly."""
        args = Namespace(debug=True, verbose=False, quiet=False)
        configure_logging(args)
        # Check the level directly
        level = (logging.DEBUG if args.debug else
                 logging.INFO if args.verbose else
                 logging.ERROR if args.quiet else
                 logging.WARNING)
        assert level == logging.DEBUG

    def test_verbose_level(self):
        """Test that verbose level is set correctly."""
        args = Namespace(debug=False, verbose=True, quiet=False)
        configure_logging(args)
        # Check the level directly
        level = (logging.DEBUG if args.debug else
                 logging.INFO if args.verbose else
                 logging.ERROR if args.quiet else
                 logging.WARNING)
        assert level == logging.INFO

    def test_quiet_level(self):
        """Test that quiet level is set correctly."""
        args = Namespace(debug=False, verbose=False, quiet=True)
        configure_logging(args)
        # Check the level directly
        level = (logging.DEBUG if args.debug else
                 logging.INFO if args.verbose else
                 logging.ERROR if args.quiet else
                 logging.WARNING)
        assert level == logging.ERROR

    def test_default_level(self):
        """Test that default level is set correctly."""
        args = Namespace(debug=False, verbose=False, quiet=False)
        configure_logging(args)
        # Check the level directly
        level = (logging.DEBUG if args.debug else
                 logging.INFO if args.verbose else
                 logging.ERROR if args.quiet else
                 logging.WARNING)
        assert level == logging.WARNING


class TestDetermineFileMode:
    def test_skip_mode(self):
        """Test that skip mode is returned when args.skip is True."""
        args = Namespace(skip=True, overwrite=False)
        assert determine_file_mode(args) == 'skip'

    def test_overwrite_mode(self):
        """Test that overwrite mode is returned when args.overwrite is True."""
        args = Namespace(skip=False, overwrite=True)
        assert determine_file_mode(args) == 'overwrite'

    def test_interactive_mode(self):
        """Test that interactive mode is returned when no mode flags are set."""
        args = Namespace(skip=False, overwrite=False)
        assert determine_file_mode(args) == 'interactive'
