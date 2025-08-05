"""
AST Extraction Module

This module provides functionality to traverse AST nodes and extract
API information from C++ code.
"""

from typing import Any, Dict
import clang.cindex
from collections import defaultdict


class ASTExtractor:
    """Extracts API information from clang AST nodes."""
    
    def __init__(self):
        self.api_data = defaultdict(lambda: defaultdict(list))
    
    def traverse_ast(self, cursor: clang.cindex.Cursor, filename: str):
        """Traverse AST and extract API information."""
        if cursor.location.file and cursor.location.file.name != filename:
            return
        
        if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            self.api_data[filename]['functions'].append(self._extract_function_info(cursor))
        
        elif cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
            self.api_data[filename]['classes'].append(self._extract_class_info(cursor))
        
        elif cursor.kind == clang.cindex.CursorKind.ENUM_DECL:
            self.api_data[filename]['enums'].append(self._extract_enum_info(cursor))
        
        elif cursor.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
            self.api_data[filename]['macros'].append(self._extract_macro_info(cursor))
        
        for child in cursor.get_children():
            self.traverse_ast(child, filename)
    
    def _extract_function_info(self, cursor: clang.cindex.Cursor) -> Dict[str, Any]:
        """Extract function information from cursor."""
        return {
            "name": cursor.spelling,
            "return_type": cursor.result_type.spelling,
            "parameters": [
                {"type": arg.type.spelling, "name": arg.spelling}
                for arg in cursor.get_arguments()
            ],
            "is_constexpr": "constexpr" in cursor.type.spelling,
            "exception_spec": self._get_exception_spec(cursor),
            "access": self._get_access_specifier(cursor),
            "visibility": self._get_visibility(cursor)
        }
    
    def _extract_class_info(self, cursor: clang.cindex.Cursor) -> Dict[str, Any]:
        """Extract class information from cursor."""
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
                    "access": self._get_access_specifier(child)
                })
            elif child.kind in [
                clang.cindex.CursorKind.CXX_METHOD,
                clang.cindex.CursorKind.CONSTRUCTOR,
                clang.cindex.CursorKind.DESTRUCTOR
            ]:
                method = self._extract_function_info(child)
                method.update({
                    "is_virtual": child.is_virtual_method(),
                    "is_pure_virtual": child.is_pure_virtual_method(),
                    "is_final": "final" in [t.spelling for t in child.get_tokens()]
                })
                class_info["methods"].append(method)
        
        return class_info
    
    def _extract_enum_info(self, cursor: clang.cindex.Cursor) -> Dict[str, Any]:
        """Extract enum information from cursor."""
        return {
            "name": cursor.spelling,
            "enumerators": [
                {"name": child.spelling, "value": child.enum_value}
                for child in cursor.get_children()
                if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL
            ]
        }
    
    def _extract_macro_info(self, cursor: clang.cindex.Cursor) -> Dict[str, str]:
        """Extract macro definition information from cursor."""
        return {
            "name": cursor.spelling,
            "definition": " ".join([t.spelling for t in cursor.get_tokens()][1:])
        }
    
    def _get_access_specifier(self, cursor: clang.cindex.Cursor) -> str:
        """Get the access specifier for a cursor."""
        return cursor.access_specifier.name if hasattr(cursor, 'access_specifier') else "PUBLIC"
    
    def _get_exception_spec(self, cursor: clang.cindex.Cursor) -> str:
        """Get the exception specification for a cursor."""
        if cursor.exception_specification_kind == clang.cindex.ExceptionSpecificationKind.NONE:
            return ""
        return cursor.type.spelling.split(")")[1].strip()
    
    def _get_visibility(self, cursor: clang.cindex.Cursor) -> str:
        """Get the visibility attributes: default, hidden."""
        for child in cursor.get_children():
            if child.kind == clang.cindex.CursorKind.VISIBILITY_ATTR:
                return "default"
        return "hidden"
    
    def get_api_data(self) -> Dict:
        """Get the extracted API data."""
        return {
            "header_files": {
                h: {k: list(v) for k, v in data.items()} 
                for h, data in self.api_data.items()
            }
        }
    
    def clear(self):
        """Clear the extracted API data."""
        self.api_data.clear()
