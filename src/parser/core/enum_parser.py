"""
Enum parser for enumeration types
"""

import re
from .base_parser import BaseParser
from ..models import APIDefinition, Enum, EnumMember


class EnumParser(BaseParser):
    """Parser for C++ enumerations"""
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Parse enum definitions from content"""
        # First, find enum declarations with proper brace matching
        self._find_and_parse_enums(content, api_def)
    
    def _find_and_parse_enums(self, content: str, api_def: APIDefinition) -> None:
        """Find and parse enum definitions with proper brace matching"""
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for enum declaration
            enum_match = re.match(r'^\s*enum\s+(class\s+)?(\w+)\s*\{?\s*$', line)
            if enum_match:
                is_class_enum = enum_match.group(1) is not None
                name = enum_match.group(2)
                
                # Find the enum body
                enum_body, consumed_lines = self._extract_enum_body(lines, i)
                if enum_body is not None:
                    enum_obj = Enum(name=name, is_class_enum=is_class_enum)
                    self._parse_enum_members(enum_body, enum_obj)
                    api_def.enums[name] = enum_obj
                
                i += consumed_lines
            else:
                i += 1
    
    def _extract_enum_body(self, lines: list, start_idx: int) -> tuple:
        """Extract enum body content with proper brace matching"""
        brace_count = 0
        enum_lines = []
        i = start_idx
        found_opening_brace = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Count braces
            brace_count += line.count('{') - line.count('}')
            
            if '{' in line:
                found_opening_brace = True
                # Start collecting content after the opening brace
                brace_pos = line.find('{')
                if brace_pos < len(line) - 1:
                    enum_lines.append(line[brace_pos + 1:])
            elif found_opening_brace:
                if brace_count > 0:
                    enum_lines.append(line)
                elif brace_count == 0:
                    # Found closing brace
                    if '}' in line:
                        close_pos = line.find('}')
                        if close_pos > 0:
                            enum_lines.append(line[:close_pos])
                    break
            
            i += 1
            
            # Safety check
            if i - start_idx > 100:
                break
        
        if found_opening_brace and brace_count == 0:
            return '\n'.join(enum_lines), i - start_idx + 1
        
        return None, 1
    
    def _parse_enum_members(self, body: str, enum_obj: Enum) -> None:
        """Parse enum members from enum body"""
        if not body:
            return
        
        # Clean the body: remove comments and Qt macros
        clean_body = self._clean_enum_body(body)
        
        # Split by commas to get individual members
        member_parts = []
        current_part = ""
        paren_count = 0
        
        for char in clean_body:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                if current_part.strip():
                    member_parts.append(current_part.strip())
                current_part = ""
                continue
            
            current_part += char
        
        # Add the last part
        if current_part.strip():
            member_parts.append(current_part.strip())
        
        # Parse each member
        for part in member_parts:
            member = self._parse_single_enum_member(part)
            if member:
                enum_obj.members.append(member)
    
    def _clean_enum_body(self, body: str) -> str:
        """Clean enum body by removing comments and Qt macros"""
        lines = body.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip comments
            if line.startswith('//') or line.startswith('/*'):
                continue
            
            # Skip Qt macros
            if self._is_qt_macro_line(line):
                continue
            
            clean_lines.append(line)
        
        return ' '.join(clean_lines)
    
    def _is_qt_macro_line(self, line: str) -> bool:
        """Check if line contains Qt macros that should be skipped"""
        qt_macros = [
            'Q_ENUM',
            'Q_FLAG',
            'Q_DECLARE_FLAGS',
            'Q_DECLARE_OPERATORS_FOR_FLAGS',
            'Q_OBJECT',
            'Q_GADGET',
        ]
        
        line_upper = line.upper()
        for macro in qt_macros:
            if macro in line_upper:
                return True
        
        return False
    
    def _parse_single_enum_member(self, member_text: str) -> EnumMember:
        """Parse a single enum member"""
        member_text = member_text.strip()
        
        if not member_text:
            return None
        
        # Pattern: NAME = value or just NAME
        match = re.match(r'^(\w+)(?:\s*=\s*(.+))?$', member_text)
        if match:
            member_name = match.group(1)
            member_value = match.group(2).strip() if match.group(2) else None
            
            # Skip if this looks like a Qt macro
            if self._is_qt_macro_line(member_name):
                return None
            
            return EnumMember(name=member_name, value=member_value)
        
        return None
