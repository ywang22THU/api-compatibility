"""
Build System Detection and Compile Flags Extraction Module

This module provides functionality to detect build systems (CMake, Make, etc.)
and extract compile flags from them.
"""

import subprocess
import re
import json
from pathlib import Path
from typing import List


class BuildSystemDetector:
    """Detects build systems and extracts compile flags."""
    
    @staticmethod
    def detect_build_system(root_path: str) -> str:
        """Detect the build system used in the project."""
        root = Path(root_path)
        
        # Check for CMakeLists.txt
        if (root / 'CMakeLists.txt').exists():
            return 'cmake'
        
        # Check for Makefile
        for makefile_name in ['Makefile', 'makefile', 'GNUmakefile']:
            if (root / makefile_name).exists():
                return 'make'
        
        # Check for other build systems
        if (root / 'build.gradle').exists() or (root / 'build.gradle.kts').exists():
            return 'gradle'
        
        if (root / 'meson.build').exists():
            return 'meson'
        
        if (root / 'configure.ac').exists() or (root / 'configure.in').exists() or (root / 'configure').exists():
            return 'autotools'
        
        return 'manual'
    
    @staticmethod
    def extract_cmake_compile_flags(root_path: str, build_dir: str = None, 
                                    target: str = None, verbose: bool = False) -> List[str]:
        """Extract compile flags from CMake project."""
        root = Path(root_path)
        if build_dir is None:
            build_dir = root / 'build'
        else:
            build_dir = Path(build_dir)
        
        flags = []
        
        try:
            # Create build directory if it doesn't exist
            build_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure the project with CMAKE_EXPORT_COMPILE_COMMANDS=ON
            cmake_cmd = ['cmake', str(root), '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
            
            if verbose:
                print(f"Running CMake configuration: {' '.join(cmake_cmd)}")
            
            result = subprocess.run(cmake_cmd, cwd=build_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"CMake configuration failed: {result.stderr}")
                return ['-std=c++14']  # fallback
            
            # Read compile_commands.json
            compile_commands_file = build_dir / 'compile_commands.json'
            if compile_commands_file.exists():
                with open(compile_commands_file, 'r') as f:
                    compile_commands = json.load(f)
                
                # Extract flags from the first C++ compilation unit
                for entry in compile_commands:
                    command = entry.get('command', '')
                    file_path = entry.get('file', '')
                    
                    # Filter for C++ files if target is specified
                    if target and target not in command:
                        continue
                    
                    if any(file_path.endswith(ext) for ext in ['.cpp', '.cxx', '.cc', '.c++']):
                        flags = BuildSystemDetector._parse_compile_command(command)
                        if verbose:
                            print(f"Extracted flags from {file_path}: {flags}")
                        break
            
            if not flags:
                print("Could not extract flags from compile_commands.json, using defaults")
                flags = ['-std=c++14']
                
        except Exception as e:
            print(f"Error extracting CMake flags: {e}")
            flags = ['-std=c++14']
        
        return flags
    
    @staticmethod
    def extract_make_compile_flags(root_path: str, target: str = None, verbose: bool = False) -> List[str]:
        """Extract compile flags from Makefile project."""
        root = Path(root_path)
        flags = []
        
        try:
            # Try to do a dry run with make to see the commands
            make_cmd = ['make', '-n']
            if target:
                make_cmd.append(target)
            else:
                # Try common targets
                for common_target in ['all', 'build', '']:
                    test_cmd = make_cmd + ([common_target] if common_target else [])
                    result = subprocess.run(test_cmd, cwd=root, capture_output=True, text=True)
                    if result.returncode == 0:
                        make_cmd = test_cmd
                        break
            
            if verbose:
                print(f"Running Make dry run: {' '.join(make_cmd)}")
            
            result = subprocess.run(make_cmd, cwd=root, capture_output=True, text=True)
            if result.returncode == 0:
                # Parse the output to find compiler commands
                lines = result.stdout.split('\n')
                for line in lines:
                    # Look for g++, clang++, or other C++ compiler invocations
                    if any(compiler in line for compiler in ['g++', 'clang++', 'c++', 'gcc']):
                        flags = BuildSystemDetector._parse_compile_command(line)
                        if flags:
                            if verbose:
                                print(f"Extracted flags from make: {flags}")
                            break
            
            if not flags:
                # Try to parse Makefile directly for common flags
                makefile_path = None
                for makefile_name in ['Makefile', 'makefile', 'GNUmakefile']:
                    if (root / makefile_name).exists():
                        makefile_path = root / makefile_name
                        break
                
                if makefile_path:
                    flags = BuildSystemDetector._parse_makefile_flags(makefile_path, verbose)
            
            if not flags:
                print("Could not extract flags from Makefile, using defaults")
                flags = ['-std=c++14']
                
        except Exception as e:
            print(f"Error extracting Make flags: {e}")
            flags = ['-std=c++14']
        
        return flags
    
    @staticmethod
    def _parse_makefile_flags(makefile_path: Path, verbose: bool = False) -> List[str]:
        """Parse Makefile to extract common compile flags."""
        flags = []
        
        try:
            with open(makefile_path, 'r') as f:
                content = f.read()
            
            # Look for common variable definitions
            flag_variables = ['CXXFLAGS', 'CPPFLAGS', 'INCLUDES', 'DEFINES']
            
            for var in flag_variables:
                # Match variable assignments like CXXFLAGS = -std=c++14 -O2
                pattern = rf'^{var}\s*[+:=]\s*(.+)$'
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    # Split the flags and add them
                    var_flags = match.strip().split()
                    flags.extend(var_flags)
                    if verbose:
                        print(f"Found {var}: {var_flags}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_flags = []
            for flag in flags:
                if flag not in seen:
                    seen.add(flag)
                    unique_flags.append(flag)
            
            flags = unique_flags
            
        except Exception as e:
            print(f"Error parsing Makefile: {e}")
        
        return flags
    
    @staticmethod
    def _parse_compile_command(command: str) -> List[str]:
        """Parse a compile command to extract relevant flags for clang parsing."""
        # Split the command into tokens
        tokens = command.split()
        
        flags = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Skip the compiler name
            if any(compiler in token for compiler in ['gcc', 'g++', 'clang', 'clang++', 'c++']):
                i += 1
                continue
            
            # Include paths
            if token.startswith('-I'):
                if token == '-I' and i + 1 < len(tokens):
                    flags.extend(['-I', tokens[i + 1]])
                    i += 2
                else:
                    flags.append(token)
                    i += 1
            # Preprocessor definitions
            elif token.startswith('-D'):
                if token == '-D' and i + 1 < len(tokens):
                    flags.extend(['-D', tokens[i + 1]])
                    i += 2
                else:
                    flags.append(token)
                    i += 1
            # Standard library
            elif token.startswith('-std='):
                flags.append(token)
                i += 1
            # System include paths
            elif token.startswith('-isystem'):
                if token == '-isystem' and i + 1 < len(tokens):
                    flags.extend(['-isystem', tokens[i + 1]])
                    i += 2
                else:
                    flags.append(token)
                    i += 1
            # Framework paths (macOS)
            elif token.startswith('-F'):
                if token == '-F' and i + 1 < len(tokens):
                    flags.extend(['-F', tokens[i + 1]])
                    i += 2
                else:
                    flags.append(token)
                    i += 1
            # Other relevant flags
            elif token in ['-fPIC', '-fno-rtti', '-fno-exceptions', '-pthread']:
                flags.append(token)
                i += 1
            # Skip output files and other irrelevant flags
            elif token.startswith('-o') or token.startswith('-c') or token.endswith('.o') or token.endswith('.cpp'):
                if token in ['-o', '-c'] and i + 1 < len(tokens):
                    i += 2  # Skip the flag and its argument
                else:
                    i += 1
            else:
                i += 1
        
        return flags
    
    @staticmethod
    def get_compile_flags(root_path: str, build_system: str = 'auto', build_dir: str = None, 
                            target: str = None, manual_flags: List[str] = None, verbose: bool = False) -> List[str]:
        """Get compile flags based on the build system."""
        
        if manual_flags:
            if verbose:
                print(f"Using manual compile flags: {manual_flags}")
            return manual_flags
        
        if build_system == 'auto':
            build_system = BuildSystemDetector.detect_build_system(root_path)
            if verbose:
                print(f"Auto-detected build system: {build_system}")
        
        if build_system == 'cmake':
            return BuildSystemDetector.extract_cmake_compile_flags(root_path, build_dir, target, verbose)
        elif build_system == 'make':
            return BuildSystemDetector.extract_make_compile_flags(root_path, target, verbose)
        elif build_system in ['gradle', 'meson', 'autotools']:
            raise NotImplementedError(f"Build system '{build_system}' is not yet supported for compile flags extraction.")
        else:
            if verbose:
                print("Using default compile flags")
            return ['-std=c++14']
