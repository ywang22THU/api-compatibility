import clang.cindex
import os
import argparse
import json
from collections import defaultdict
from typing import Any

CLANG_PATH = '/usr/lib/llvm-14/lib/libclang.so'

def parse_args():
    parser = argparse.ArgumentParser(description="Parse C++ library headers and extract API information.")
    parser.add_argument('--root_path', type=str, help='The root path of the C++ library containing header files.')
    parser.add_argument('--compile_flags', nargs='*', default=['-std=c++14'], help='Compilation flags to use when parsing headers.')
    parser.add_argument('--output_path', type=str, default='api_data.json', help='Output file path for the extracted API data.')
    return parser.parse_args()

def parse_library(root_path: str, compile_flags: list[str], output_path: str):
    """
    Parse C++ library headers and extract API information.

    Args:
        root_path (str): the library root path containing header files
        compile_flags (list[str]): the compilation flags used to parse the headers
        output_path (str): the output file path
    """
    clang.cindex.Config.set_library_file(CLANG_PATH)
    index = clang.cindex.Index.create()
    
    # 收集头文件
    header_files = []
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(('.h', '.hh', '.hpp', '.hxx')):
                header_files.append(os.path.join(root, file))
    
    api_data = defaultdict(lambda: defaultdict(list))
    
    for header in header_files:
        # 解析每个头文件
        tu = index.parse(header, args=compile_flags)
        traverse_ast(tu.cursor, api_data, header)
    
    # 转换为可序列化结构
    serializable_data = {
        "header_files": {
            h: {k: list(v) for k, v in data.items()} 
            for h, data in api_data.items()
        }
    }
    
    # 保存为JSON
    with open(output_path, 'w') as f:
        json.dump(serializable_data, f, indent=2)

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
    parse_library(args.root_path, args.compile_flags, args.output_path)
    
if __name__ == "__main__":
    main()