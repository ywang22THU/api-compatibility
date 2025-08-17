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
        # Split content into lines to handle each #define separately
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('#define'):
                continue
                
            # Parse each #define line individually
            self._parse_define_line(line, api_def)
    
    def _parse_define_line(self, line: str, api_def: APIDefinition) -> None:
        """Parse a single #define line"""
        # Remove the #define prefix
        line = line[7:].strip()  # Remove '#define'
        
        if not line:
            return
        
        # Pattern for macro with parameters: NAME(params) value
        param_match = re.match(r'^(\w+)\s*\(([^)]*)\)\s*(.*)', line)
        if param_match:
            name = param_match.group(1)
            params_str = param_match.group(2)
            value = param_match.group(3).strip() if param_match.group(3) else None
            
            parameters = []
            if params_str:
                parameters = [p.strip() for p in params_str.split(',') if p.strip()]
            
            api_def.macros[name] = Macro(name=name, value=value, parameters=parameters)
            return
        
        # Pattern for simple macro: NAME value (or just NAME)
        simple_match = re.match(r'^(\w+)(?:\s+(.*))?$', line)
        if simple_match:
            name = simple_match.group(1)
            value = simple_match.group(2).strip() if simple_match.group(2) else None
            
            # Special handling for header guard macros and empty defines
            if self._is_header_guard_or_empty_define(name, value):
                value = None
            
            api_def.macros[name] = Macro(name=name, value=value, parameters=[])
    
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
