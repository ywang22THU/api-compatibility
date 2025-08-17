"""
API definition model that aggregates all parsed elements
"""

from dataclasses import dataclass, field
from typing import Dict
from .class_models import Class
from .enum_models import Enum
from .macro import Macro


@dataclass
class APIDefinition:
    """API definition collection"""
    classes: Dict[str, Class] = field(default_factory=dict)
    enums: Dict[str, Enum] = field(default_factory=dict)
    macros: Dict[str, Macro] = field(default_factory=dict)
    constants: Dict[str, str] = field(default_factory=dict)
