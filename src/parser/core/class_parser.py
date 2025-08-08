"""
Class parser for C++ class definitions
"""

import re
from .base_parser import BaseParser
from .function_parser import FunctionParser
from ..models import APIDefinition, Class


class ClassParser(BaseParser):
    """Parser for C++ class definitions"""
    
    def __init__(self):
        super().__init__()
        self.function_parser = FunctionParser()
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Parse class definitions from content"""
        # Match class definition (simplified)
        pattern = r'class\s+(final\s+)?(\w+)(?:\s*:\s*([^{]+))?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            is_final = match.group(1) is not None
            name = match.group(2)
            inheritance = match.group(3)
            body = match.group(4)
            
            class_obj = Class(name=name, is_final=is_final)
            
            # Parse inheritance relationships
            if inheritance:
                class_obj.base_classes = self._parse_inheritance(inheritance)
            
            # Parse class body
            self._parse_class_body(body, class_obj)
            
            api_def.classes[name] = class_obj
    
    def _parse_inheritance(self, inheritance: str) -> list[str]:
        """Parse class inheritance relationships"""
        base_classes = []
        for base in inheritance.split(','):
            base = base.strip()
            # Remove access modifiers
            base = re.sub(r'^(public|protected|private)\s+', '', base)
            if base:
                base_classes.append(base)
        return base_classes
    
    def _parse_class_body(self, body: str, class_obj: Class) -> None:
        """Parse class body content"""
        current_access = "private"  # Class default is private
        
        lines = body.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check access modifiers
            if line in ['public:', 'protected:', 'private:']:
                current_access = line[:-1]
                i += 1
                continue
            
            # Parse methods
            method = self.function_parser.parse_method(line, current_access)
            if method:
                class_obj.methods.append(method)
            
            i += 1
