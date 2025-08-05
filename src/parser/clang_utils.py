"""
Clang Utilities Module

This module provides utilities for working with libclang,
including automatic detection and configuration.
"""

import os
import platform
import glob
from typing import Optional
import clang.cindex


class ClangUtils:
    """Utilities for libclang setup and configuration."""
    
    DEFAULT_CLANG_PATHS = {
        'Linux': [
            '/usr/lib/llvm-*/lib/libclang.so*',
            '/usr/lib/x86_64-linux-gnu/libclang*.so*',
            '/usr/lib/libclang*.so*',
            '/usr/local/lib/libclang*.so*'
        ],
    }
    
    _libclang_path = None
    
    @staticmethod
    def get_libclang_path() -> Optional[str]:
        """Get the path to the configured libclang library."""
        return ClangUtils._libclang_path

    @staticmethod
    def _find_libclang() -> Optional[str]:
        """Try to find libclang automatically."""
        # Support only for linux at the moment
        system = platform.system()
        if system not in ClangUtils.DEFAULT_CLANG_PATHS:
            raise NotImplementedError(f"Automatic libclang detection is not implemented for {system}")
        possible_paths = ClangUtils.DEFAULT_CLANG_PATHS.get(system, [])
        
        for pattern in possible_paths:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        
        return None
    
    @staticmethod
    def configure_libclang(custom_path: str = None) -> bool:
        """Configure libclang for use with the parser."""
        if custom_path and os.path.exists(custom_path):
            clang.cindex.Config.set_library_file(custom_path)
            return True
        
        # Try to auto-detect
        libclang_path = ClangUtils._find_libclang()
        if libclang_path:
            clang.cindex.Config.set_library_file(libclang_path)
            ClangUtils._libclang_path = libclang_path
            return True
        
        print("Warning: Could not find libclang, using system default")
        return False
    
    @staticmethod
    def create_index() -> clang.cindex.Index:
        """Create a clang index for parsing."""
        return clang.cindex.Index.create()
    
    @staticmethod
    def parse_file(index: clang.cindex.Index, filepath: str, 
                    compile_flags: list, verbose: bool = False) -> Optional[clang.cindex.TranslationUnit]:
        """Parse a single file using clang."""
        try:
            tu = index.parse(filepath, args=compile_flags)
            
            # Check for errors and warnings
            if tu.diagnostics:
                for diag in tu.diagnostics:
                    if diag.severity >= clang.cindex.Diagnostic.Error:
                        print(f"Error in {filepath}: {diag.spelling}")
                    elif verbose and diag.severity >= clang.cindex.Diagnostic.Warning:
                        print(f"Warning in {filepath}: {diag.spelling}")
            
            return tu
            
        except clang.cindex.TranslationUnitLoadError as e:
            print(f"Failed to parse {filepath}: {e}")
            return None
