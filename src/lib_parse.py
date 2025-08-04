import clang.cindex
import os
import argparse
import json
import subprocess
import re
import platform
from pathlib import Path
from collections import defaultdict
from typing import Any, List, Optional

CLANG_PATH = '/usr/lib/llvm-14/lib/libclang.so'

def parse_args():
    parser = argparse.ArgumentParser(description="Parse C++ library headers and extract API information.")
    parser.add_argument('--root_path', type=str, required=True, help='The root path of the C++ library containing header files.')
    parser.add_argument('--output_path', type=str, default='api_data.json', help='Output file path for the extracted API data.')
    parser.add_argument('--build_system', choices=['auto', 'make', 'cmake', 'manual'], default='auto', 
                       help='Build system to use for extracting compile flags.')
    parser.add_argument('--build_dir', type=str, default=None, help='Build directory (for CMake projects).')
    parser.add_argument('--target', type=str, default=None, help='Specific target to analyze (for Make/CMake).')
    parser.add_argument('--cmake_args', nargs='*', default=[], help='Additional CMake arguments.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output.')
    parser.add_argument('--compile_flags', nargs=argparse.REMAINDER, default=None, help='Manual compilation flags to use when parsing headers.')
    return parser.parse_args()

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
    
    if (root / 'configure.ac').exists() or (root / 'configure.in').exists():
        return 'autotools'
    
    return 'manual'


def extract_cmake_compile_flags(root_path: str, build_dir: str = None, target: str = None, 
                              cmake_args: List[str] = None, verbose: bool = False) -> List[str]:
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
        if cmake_args:
            cmake_cmd.extend(cmake_args)
        
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
                    flags = parse_compile_command(command)
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
                    flags = parse_compile_command(line)
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
                flags = parse_makefile_flags(makefile_path, verbose)
        
        if not flags:
            print("Could not extract flags from Makefile, using defaults")
            flags = ['-std=c++14']
            
    except Exception as e:
        print(f"Error extracting Make flags: {e}")
        flags = ['-std=c++14']
    
    return flags


def parse_makefile_flags(makefile_path: Path, verbose: bool = False) -> List[str]:
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


def parse_compile_command(command: str) -> List[str]:
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


def get_compile_flags(root_path: str, build_system: str = 'auto', build_dir: str = None, 
                     target: str = None, cmake_args: List[str] = None, 
                     manual_flags: List[str] = None, verbose: bool = False) -> List[str]:
    """Get compile flags based on the build system."""
    
    if manual_flags:
        if verbose:
            print(f"Using manual compile flags: {manual_flags}")
        return manual_flags
    
    if build_system == 'auto':
        build_system = detect_build_system(root_path)
        if verbose:
            print(f"Auto-detected build system: {build_system}")
    
    if build_system == 'cmake':
        return extract_cmake_compile_flags(root_path, build_dir, target, cmake_args, verbose)
    elif build_system == 'make':
        return extract_make_compile_flags(root_path, target, verbose)
    else:
        if verbose:
            print("Using default compile flags")
        return ['-std=c++14']


def parse_library(root_path: str, compile_flags: List[str], output_path: str, verbose: bool = False):
    """
    Parse C++ library headers and extract API information.

    Args:
        root_path (str): the library root path containing header files
        compile_flags (List[str]): the compilation flags used to parse the headers
        output_path (str): the output file path
        verbose (bool): enable verbose output
    """
    # Try to auto-detect libclang
    if not os.path.exists(CLANG_PATH):
        libclang_path = find_libclang()
        if libclang_path:
            clang.cindex.Config.set_library_file(libclang_path)
        else:
            print("Warning: Could not find libclang, using default path")
            clang.cindex.Config.set_library_file(CLANG_PATH)
    else:
        clang.cindex.Config.set_library_file(CLANG_PATH)
    
    index = clang.cindex.Index.create()
    
    # Collect header files
    header_files = []
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(('.h', '.hh', '.hpp', '.hxx')):
                header_files.append(os.path.join(root, file))
    
    if verbose:
        print(f"Found {len(header_files)} header files")
        print(f"Using compile flags: {compile_flags}")
    
    api_data = defaultdict(lambda: defaultdict(list))
    
    for header in header_files:
        if verbose:
            print(f"Parsing header: {header}")
        else:
            print("Parsing header:", header)
        
        # Parse each header file
        try:
            tu = index.parse(header, args=compile_flags)
            if tu.diagnostics:
                for diag in tu.diagnostics:
                    if diag.severity >= clang.cindex.Diagnostic.Error:
                        print(f"Error in {header}: {diag.spelling}")
                    elif verbose and diag.severity >= clang.cindex.Diagnostic.Warning:
                        print(f"Warning in {header}: {diag.spelling}")
            
            traverse_ast(tu.cursor, api_data, header)
        except clang.cindex.TranslationUnitLoadError as e:
            print(f"Failed to parse {header}: {e}")
    
    # Convert to serializable structure
    serializable_data = {
        "header_files": {
            h: {k: list(v) for k, v in data.items()} 
            for h, data in api_data.items()
        }
    }
    
    # Save as JSON
    with open(output_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    if verbose:
        print(f"API data saved to: {output_path}")


def find_libclang() -> Optional[str]:
    """Try to find libclang automatically."""
    possible_paths = []
    
    # Common paths on different systems
    if platform.system() == "Linux":
        possible_paths.extend([
            '/usr/lib/llvm-*/lib/libclang.so*',
            '/usr/lib/x86_64-linux-gnu/libclang*.so*',
            '/usr/lib/libclang*.so*',
            '/usr/local/lib/libclang*.so*'
        ])
    elif platform.system() == "Darwin":  # macOS
        possible_paths.extend([
            '/usr/local/lib/libclang*.dylib',
            '/opt/homebrew/lib/libclang*.dylib',
            '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang*.dylib'
        ])
    elif platform.system() == "Windows":
        possible_paths.extend([
            'C:/Program Files/LLVM/lib/libclang.dll',
            'C:/Program Files (x86)/LLVM/lib/libclang.dll'
        ])
    
    import glob
    for pattern in possible_paths:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    return None

def traverse_ast(cursor: clang.cindex.Cursor, api_data: dict, filename: str):
    if cursor.location.file and cursor.location.file.name != filename:
        return
    
    if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        api_data[filename]['functions'].append(extract_function_info(cursor))
    
    elif cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
        api_data[filename]['classes'].append(extract_class_info(cursor))
    
    elif cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
        api_data[filename]['enums'].append(extract_enum_info(cursor))
    
    elif cursor.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
        api_data[filename]['macros'].append(extract_macro_info(cursor))
    
    for child in cursor.get_children():
        traverse_ast(child, api_data, filename)

def extract_function_info(cursor: clang.cindex.Cursor) -> dict[str, Any]:
    """Extract function information"""
    return {
        "name": cursor.spelling,
        "return_type": cursor.result_type.spelling,
        "parameters": [
            {"type": arg.type.spelling, "name": arg.spelling}
            for arg in cursor.get_arguments()
        ],
        "is_constexpr": "constexpr" in cursor.type.spelling,
        "exception_spec": get_exception_spec(cursor),
        "access": get_access_specifier(cursor),
        "visibility": get_visibility(cursor)
    }

def extract_class_info(cursor: clang.cindex.Cursor) -> dict[str, Any]:
    """Extract class information"""
    class_info = {
        "name": cursor.spelling,
        "bases": [
            {"name": base.spelling, "access": base.access_specifier.name}
            for base in cursor.get_children()
            if base.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER
        ],
        "fields": [],
        "methods": []
    }
    
    for child in cursor.get_children():
        if child.kind == clang.cindex.CursorKind.FIELD_DECL:
            class_info["fields"].append({
                "name": child.spelling,
                "type": child.type.spelling,
                "access": get_access_specifier(child)
            })
        elif child.kind in [
            clang.cindex.CursorKind.CXX_METHOD,
            clang.cindex.CursorKind.CONSTRUCTOR,
            clang.cindex.CursorKind.DESTRUCTOR
        ]:
            method = extract_function_info(child)
            method.update({
                "is_virtual": child.is_virtual_method(),
                "is_pure_virtual": child.is_pure_virtual_method(),
                "is_final": "final" in [t.spelling for t in child.get_tokens()]
            })
            class_info["methods"].append(method)
    
    return class_info

def extract_enum_info(cursor: clang.cindex.Cursor) -> dict[str, Any]:
    """Extract enum information"""
    return {
        "name": cursor.spelling,
        "enumerators": [
            {"name": child.spelling, "value": child.enum_value}
            for child in cursor.get_children()
            if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL
        ]
    }

def extract_macro_info(cursor: clang.cindex.Cursor) -> dict[str, str]:
    """Extract macro definition information"""
    return {
        "name": cursor.spelling,
        "definition": " ".join([t.spelling for t in cursor.get_tokens()][1:])
    }

def get_access_specifier(cursor: clang.cindex.Cursor) -> str:
    """Get the access specifier"""
    return cursor.access_specifier.name if hasattr(cursor, 'access_specifier') else "PUBLIC"

def get_exception_spec(cursor: clang.cindex.Cursor) -> str:
    """Get the exception specification"""
    if cursor.exception_specification_kind == clang.cindex.ExceptionSpecificationKind.NONE:
        return ""
    return cursor.type.spelling.split(")")[1].strip()

def get_visibility(cursor: clang.cindex.Cursor) -> str:
    """Get the visibility attributes: default, hidden."""
    for child in cursor.get_children():
        if child.kind == clang.cindex.CursorKind.VISIBILITY_ATTR:
            return "default"
    return "hidden"

def main():
    args = parse_args()
    
    # Get compile flags from build system or use manual flags
    compile_flags = get_compile_flags(
        root_path=args.root_path,
        build_system=args.build_system,
        build_dir=args.build_dir,
        target=args.target,
        cmake_args=args.cmake_args,
        manual_flags=args.compile_flags,
        verbose=args.verbose
    )
    
    # Parse the library
    parse_library(args.root_path, compile_flags, args.output_path, args.verbose)
    
if __name__ == "__main__":
    main()