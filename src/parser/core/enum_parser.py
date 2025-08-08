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
        # Match enum or enum class
        pattern = r'enum\s+(class\s+)?(\w+)\s*\{([^}]*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            is_class_enum = match.group(1) is not None
            name = match.group(2)
            body = match.group(3)
            
            enum_obj = Enum(name=name, is_class_enum=is_class_enum)
            
            # Parse enum members
            self._parse_enum_members(body, enum_obj)
            
            api_def.enums[name] = enum_obj
    
    def _parse_enum_members(self, body: str, enum_obj: Enum) -> None:
        """Parse enum members from enum body"""
        members_pattern = r'(\w+)(?:\s*=\s*([^,}]+))?'
        for member_match in re.finditer(members_pattern, body):
            member_name = member_match.group(1)
            member_value = member_match.group(2).strip() if member_match.group(2) else None
            enum_obj.members.append(EnumMember(name=member_name, value=member_value))
