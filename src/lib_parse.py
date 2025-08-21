#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ Library Parser - Main Entry Point
A modular and maintainable C++ header parser
"""

import os
import sys
import argparse
import logging
from multiprocessing import cpu_count
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from parser import CppParser, JSONSerializer


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure logging format
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="C++ Library Parser - Parse C++ header files and extract API information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Basic usage
            python lib_parse.py --root_path /path/to/cpp/library --output_path api_v1.json
            
            # With custom exclude directories
            python lib_parse.py --root_path /path/to/cpp/library --exclude_dirs 3rdparty tests build --output_path api_v1.json
            
            # Verbose output with no exclusions
            python lib_parse.py --root_path /path/to/cpp/library --exclude_dirs --output_path api_v1.json --verbose
        """
    )
    
    parser.add_argument(
        '--root_path',
        required=True,
        help='Root path of the C++ library containing header files'
    )
    
    parser.add_argument(
        '--output_path',
        default='api_data.json',
        help='Output JSON file path (default: api_data.json)'
    )
    
    parser.add_argument(
        '--exclude_dirs',
        nargs='*',
        default=[
            '3rdparty', 'third_party', 'thirdparty', 'icons', 'tests', 'test', 
            'examples', 'example', 'docs', 'doc', 'build', 'cmake-build-debug', 
            'cmake-build-release', '.git', '.vscode', '__pycache__'
        ],
        help='Directories to exclude from parsing (default: common build/test directories). Use empty list to exclude nothing.'
    )
    
    parser.add_argument(
        '--path_patterns',
        nargs='*',
        default='*',
        help='Regex patterns to match specific directory paths (e.g., "qt/*/src" to match qt/any/src). If specified, only matching paths will be parsed.'
    )
    
    parser.add_argument(
        '--max_workers',
        type=int,
        default=1,
        help=f'Maximum number of worker processes for parallel parsing (default: {cpu_count()})'
    )
    
    parser.add_argument(
        '-vvv', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments"""
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(args.root_path):
        logger.error(f"Root path does not exist: {args.root_path}")
        sys.exit(1)
    
    if not os.path.isdir(args.root_path):
        logger.error(f"Root path is not a directory: {args.root_path}")
        sys.exit(1)


def log_verbose_info(args: argparse.Namespace) -> None:
    """Log verbose information about parsing parameters"""
    logger = logging.getLogger(__name__)
    logger.debug(f"Parsing C++ headers in: {args.root_path}")
    if args.exclude_dirs:
        logger.debug(f"Excluding directories: {', '.join(args.exclude_dirs)}")
    else:
        logger.debug("No directories excluded")


def log_results(api_def, args: argparse.Namespace) -> None:
    """Log parsing results"""
    logger = logging.getLogger(__name__)
    logger.debug(f"Found {len(api_def.classes)} classes")
    logger.debug(f"Found {len(api_def.enums)} enums") 
    logger.debug(f"Found {len(api_def.macros)} macros")
    logger.info(f"Analysis complete. API data saved to: {args.output_path}")


def main() -> None:
    """Main function for command line interface"""    
    # Parse command line arguments
    arg_parser = create_argument_parser()
    args = arg_parser.parse_args()
    
    # Setup logging based on verbose flag
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    validate_arguments(args)
    
    # Log verbose info if requested
    log_verbose_info(args)
    
    # Initialize parser and process
    try:
        cpp_parser = CppParser()
        
        # Log parsing configuration
        logger.info(f"Parsing directory: {args.root_path}")
        if args.path_patterns:
            logger.info(f"Using path patterns: {args.path_patterns}")
        else:
            logger.info(f"Excluding directories: {args.exclude_dirs}")
        
        # Parse directory
        api_def = cpp_parser.parse_directory(
            dir_path=args.root_path, 
            exclude_dirs=args.exclude_dirs,
            path_patterns=args.path_patterns,
            max_workers=args.max_workers,
        )
        
        # Save to file using JSONSerializer
        JSONSerializer.save_to_file(api_def, args.output_path)
        
        # Log results
        log_results(api_def, args)
            
    except Exception as e:
        logger.exception(f"Error during parsing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
