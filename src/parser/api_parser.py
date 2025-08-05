"""
Main API Parser Module

This module provides the main APIParser class that coordinates
all the parsing activities.
"""

import os
import json
from typing import List

from .build_system import BuildSystemDetector
from .clang_utils import ClangUtils
from .ast_extractor import ASTExtractor

DEFAULT_EXCLUDE_DIRS = ['3rdparty', 'third_party', 'thirdparty', 'icons', 'tests', 'test', 'examples', 'example', 'docs', 'doc', 'build', 'cmake-build-debug', 'cmake-build-release', '.git', '.vscode', '__pycache__']

class APIParser:
    """Main parser class for extracting API information from C++ libraries."""
    
    def __init__(self, verbose: bool = False, exclude_dirs: List[str] = None):
        """Initialize the API parser.
        
        Args:
            verbose: Enable verbose output
            exclude_dirs: List of directory names to exclude from header file search
        """
        self.verbose = verbose
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
        self.build_detector = BuildSystemDetector()
        self.clang_utils = ClangUtils()
        self.ast_extractor = ASTExtractor()
        
        # Configure libclang
        if not self.clang_utils.configure_libclang():
            print("Warning: libclang configuration may be incomplete")
        elif self.verbose:
            print(f"libclang configured successfully: {self.clang_utils.get_libclang_path()}")
    
    def parse_library(self, root_path: str, compile_flags: List[str], 
                        output_path: str) -> bool:
        """Parse a C++ library and extract API information.
        
        Args:
            root_path: Root path of the C++ library
            compile_flags: Compilation flags to use
            output_path: Output file path for API data
            
        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            # Find header files
            header_files = self._find_header_files(root_path)
            
            if not header_files:
                print(f"No header files found in {root_path}")
                return False
            
            if self.verbose:
                print(f"Found {len(header_files)} header files")
                print(f"Using compile flags: {compile_flags}")
            
            # Create clang index
            index = self.clang_utils.create_index()
            
            # Parse each header file
            for header in header_files:
                if self.verbose:
                    print(f"Parsing header: {header}")
                else:
                    print(f"Parsing header: {header}")
                
                # Parse the file
                tu = self.clang_utils.parse_file(index, header, compile_flags, self.verbose)
                if tu:
                    self.ast_extractor.traverse_ast(tu.cursor, header)
            
            # Get API data and save
            api_data = self.ast_extractor.get_api_data()
            self._save_api_data(api_data, output_path)
            
            if self.verbose:
                print(f"API data saved to: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"Error parsing library: {e}")
            return False
    
    def parse_with_build_system(self, root_path: str, build_system: str = 'auto',
                                build_dir: str = None, target: str = None,
                                manual_flags: List[str] = None,
                                output_path: str = 'api_data.json') -> bool:
        """Parse a library using build system detection.
        
        Args:
            root_path: Root path of the C++ library
            build_system: Build system to use ('auto', 'cmake', 'make', 'manual')
            build_dir: Build directory for CMake projects
            target: Specific target for Make/CMake
            cmake_args: Additional CMake arguments
            manual_flags: Manual compilation flags
            output_path: Output file path
            
        Returns:
            True if parsing was successful, False otherwise
        """
        # Get compile flags from build system
        compile_flags = self.build_detector.get_compile_flags(
            root_path=root_path,
            build_system=build_system,
            build_dir=build_dir,
            target=target,
            manual_flags=manual_flags,
            verbose=self.verbose
        )
        
        # Parse the library
        return self.parse_library(root_path, compile_flags, output_path)
    
    def _find_header_files(self, root_path: str) -> List[str]:
        """Find all header files in the given directory, excluding specified directories."""
        header_files = []
        
        if self.verbose:
            print(f"Excluding directories: {self.exclude_dirs}")
        
        for root, dirs, files in os.walk(root_path):
            # Remove excluded directories from dirs to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            # Also check if current directory path contains any excluded directory
            relative_path = os.path.relpath(root, root_path)
            if any(excluded_dir in relative_path.split(os.sep) for excluded_dir in self.exclude_dirs):
                continue
            
            for file in files:
                if file.endswith(('.h', '.hh', '.hpp', '.hxx')):
                    full_path = os.path.join(root, file)
                    header_files.append(full_path)
                    if self.verbose:
                        print(f"Found header file: {full_path}")
        
        return header_files
    
    def _save_api_data(self, api_data: dict, output_path: str):
        """Save API data to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(api_data, f, indent=2)
