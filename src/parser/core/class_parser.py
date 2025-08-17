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
        # First remove forward declarations to avoid parsing them
        content = self._remove_forward_declarations(content)
        
        # Match class definition with optional Q_XXX_EXPORT macro
        # Pattern: class Q_XXX_EXPORT ClassName : inheritance { body }
        pattern = r'class\s+(Q_\w+_EXPORT\s+)?(final\s+)?(\w+)(?:\s*:\s*([^{]+))?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            export_macro = match.group(1)
            is_final = match.group(2) is not None
            name = match.group(3)
            inheritance = match.group(4)
            body = match.group(5)
            
            # Skip classes without Q_XXX_EXPORT macro (not public API)
            if not export_macro:
                continue
            
            # Skip private classes (those with 'private' in name)
            if self._is_private_class(name):
                print("skip private class : {}".format(name))
                continue
            
            class_obj = Class(name=name, is_final=is_final)
            
            # Store the export macro information
            class_obj.export_macro = export_macro.strip()
            
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
    
    def _remove_forward_declarations(self, content: str) -> str:
        """Remove forward class declarations to avoid parsing them"""
        # Pattern to match forward declarations like:
        # class ClassName;
        # struct StructName;
        # Also handle QT_FORWARD_DECLARE_CLASS and similar macros
        forward_patterns = [
            r'^\s*class\s+\w+\s*;\s*$',                    # class Name;
            r'^\s*struct\s+\w+\s*;\s*$',                   # struct Name;
            r'^\s*QT_FORWARD_DECLARE_CLASS\s*\(\s*\w+\s*\)\s*;\s*$',  # QT_FORWARD_DECLARE_CLASS(Name);
            r'^\s*Q_DECLARE_METATYPE\s*\(\s*[^)]+\s*\)\s*;\s*$',      # Q_DECLARE_METATYPE declarations
        ]
        
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            is_forward_declaration = False
            
            for pattern in forward_patterns:
                if re.match(pattern, line, re.MULTILINE):
                    is_forward_declaration = True
                    break
            
            if not is_forward_declaration:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _is_private_class(self, class_name: str) -> bool:
        """Check if a class should be considered private and excluded"""
        private_indicators = [
            'private',     # Contains 'private' directly
            'Private',     # Contains 'Private' (Qt style)
            'Internal',    # Internal classes
            'Detail',      # Detail namespace classes
            'Impl',        # Implementation classes
            '_p',          # Private suffix pattern
            '_impl',       # Implementation suffix
            'Details',     # Details namespace
        ]
        
        class_name_lower = class_name.lower()
        
        # Check if class name contains any private indicators
        for indicator in private_indicators:
            if indicator.lower() in class_name_lower:
                return True
        
        # Check for specific naming patterns
        if (class_name.endswith('Private') or 
            class_name.endswith('Impl') or 
            class_name.endswith('Internal') or
            class_name.startswith('Q') and 'Private' in class_name or
            '_' in class_name and ('private' in class_name_lower or 'impl' in class_name_lower)):
            return True
        
        return False
    
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
