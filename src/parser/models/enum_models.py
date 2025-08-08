"""
Enum models for enumeration types
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EnumMember:
    """Enum member"""
    name: str
    value: Optional[str] = None


@dataclass
class Enum:
    """Enum type"""
    name: str
    members: List[EnumMember] = field(default_factory=list)
    is_class_enum: bool = False
