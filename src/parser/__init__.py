"""
C++ Library Parser Package
A modular and maintainable C++ header parser

This package provides tools for parsing C++ header files and extracting
API information including classes, functions, enums, and macros.
"""

from .models import (
    Parameter, Function, EnumMember, Enum, Member, Class, Macro, APIDefinition
)
from .core import CppParser
from .utils import TextProcessor, JSONSerializer

__version__ = "2.0.0"
__all__ = [
    # Models
    'Parameter',
    'Function', 
    'EnumMember',
    'Enum',
    'Member',
    'Class',
    'Macro',
    'APIDefinition',
    # Core parser
    'CppParser',
    # Utilities
    'TextProcessor',
    'JSONSerializer'
]
