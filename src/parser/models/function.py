"""
Function model for methods and functions
"""

from dataclasses import dataclass, field
from typing import List
from .parameter import Parameter


@dataclass
class Function:
    """Function or method"""
    name: str
    return_type: str
    parameters: List[Parameter] = field(default_factory=list)
    is_virtual: bool = False
    is_pure_virtual: bool = False
    is_static: bool = False
    is_const: bool = False
    is_noexcept: bool = False
    is_override: bool = False
    is_final: bool = False
    access_level: str = "public"  # public, protected, private
    
    def signature(self) -> str:
        """Generate function signature"""
        params = ", ".join(str(p) for p in self.parameters)
        modifiers = []
        if self.is_static:
            modifiers.append("static")
        if self.is_virtual:
            modifiers.append("virtual")
        if self.is_const:
            modifiers.append("const")
        if self.is_noexcept:
            modifiers.append("noexcept")
        if self.is_override:
            modifiers.append("override")
        if self.is_final:
            modifiers.append("final")
        
        modifier_str = " ".join(modifiers)
        if modifier_str:
            return f"{modifier_str} {self.return_type} {self.name}({params})"
        return f"{self.return_type} {self.name}({params})"
