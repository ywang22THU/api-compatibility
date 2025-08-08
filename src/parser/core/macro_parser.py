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
        pattern = r'#define\s+(\w+)(?:\(([^)]*)\))?\s*(.*?)(?=\n|$)'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            params_str = match.group(2)
            value = match.group(3).strip() if match.group(3) else None
            
            parameters = []
            if params_str:
                parameters = [p.strip() for p in params_str.split(',') if p.strip()]
            
            api_def.macros[name] = Macro(name=name, value=value, parameters=parameters)
