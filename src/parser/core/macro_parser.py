"""
Macro parser for preprocessor directives
"""

import re
from .base_parser import BaseParser
from ..models import APIDefinition, Macro


class MacroParser(BaseParser):
    """Parser for C++ preprocessor macros"""
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Parse macro definitions from content"""
        # Pattern for #define macros with optional parameters and values
        define_pattern = r'^\s*#define\s+(\w+)(?:\(([^)]*)\))?\s*(.*?)(?=\n|$)'
        
        for match in re.finditer(define_pattern, content, re.MULTILINE):
            name = match.group(1)
            params_str = match.group(2)
            value = match.group(3).strip() if match.group(3) else None
            
            # Special handling for header guard macros and empty defines
            if self._is_header_guard_or_empty_define(name, value):
                # For header guards and empty defines, set value to None
                value = None
            
            parameters = []
            if params_str:
                parameters = [p.strip() for p in params_str.split(',') if p.strip()]
            
            api_def.macros[name] = Macro(name=name, value=value, parameters=parameters)
    
    def _is_header_guard_or_empty_define(self, name: str, value: str) -> bool:
        """Check if this is a header guard or empty define that should have no value"""
        # Common patterns for header guards
        header_guard_patterns = [
            r'.*_H$',           # ends with _H
            r'.*_HPP$',         # ends with _HPP
            r'.*_HXX$',         # ends with _HXX
            r'.*_INCLUDED$',    # ends with _INCLUDED
            r'.*_HEADER_$',     # ends with _HEADER_
        ]
        
        # Check if it's a header guard pattern
        for pattern in header_guard_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        
        # Check if it's an empty define (no value or just whitespace)
        if not value or not value.strip():
            return True
            
        return False
