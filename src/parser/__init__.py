"""
C++ API Parser Package

This package provides tools for parsing C++ libraries and extracting API information.
It supports various build systems and can automatically detect compile flags.

Modules:
    api_parser: Main API parser class
    build_system: Build system detection and compile flags extraction
    ast_extractor: AST traversal and API information extraction
    clang_utils: libclang utilities and configuration
    config: Configuration settings
    main: The main entry point for the parser    
"""

from .api_parser import APIParser
from .main import parse_arguments

__all__ = [
    # Main classes
    'APIParser',
    
    # Main functions
    'parse_arguments',
]
