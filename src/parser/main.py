"""
Command Line Interface Module

This module provides the command line interface for the API parser.
"""

import argparse

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Parse C++ library headers and extract API information.",
    )
    
    parser.add_argument(
        '--root_path', 
        type=str, 
        required=True,
        help='The root path of the C++ library containing header files.'
    )
    
    parser.add_argument(
        '--output_path', 
        type=str, 
        default='api_data.json',
        help='Output file path for the extracted API data (default: api_data.json).'
    )
    
    parser.add_argument(
        '--build_system', 
        choices=['auto', 'make', 'cmake', 'manual'], 
        default='auto',
        help='Build system to use for extracting compile flags (default: auto).'
    )
    
    parser.add_argument(
        '--build_dir', 
        type=str, 
        default=None,
        help='Build directory for CMake projects (default: {root_path}/build).'
    )
    
    parser.add_argument(
        '--target', 
        type=str, 
        default=None,
        help='Specific target to analyze for Make/CMake projects.'
    )
        
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose output.'
    )
    
    parser.add_argument(
        '--compile_flags', 
        nargs=argparse.REMAINDER, 
        default=None,
        help='Manual compilation flags to use when parsing headers (use with --build_system manual).'
    )
    
    parser.add_argument(
        '--exclude_dirs', 
        nargs='+', 
        default=['3rdparty', 'third_party', 'thirdparty', 'icons', 'assets', 'tests', 'test', 'testlib', 'testinternal', 'examples', 'example', 'docs', 'doc', 'build', 'cmake-build-debug', 'cmake-build-release', '.git', '.vscode', '__pycache__'],
        help='Directories to exclude when searching for header files (default: common directories like 3rdparty, tests, etc.).'
    )
    
    return parser


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_argument_parser()
    return parser.parse_args()
