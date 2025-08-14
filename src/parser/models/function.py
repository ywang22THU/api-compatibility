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
    is_static: bool = False
    is_const: bool = False
    is_noexcept: bool = False
    is_override: bool = False
    is_final: bool = False
    is_pure_virtual: bool = False
    is_inline: bool = False
    is_extern: bool = False
    access_level: str = "public"  # public, protected, private
    
    def signature(self) -> str:
        """Generate function signature"""
        params = ", ".join(str(p) for p in self.parameters)
        prefixes = []
        suffix = " = 0" if self.is_virtual and self.is_pure_virtual else ""
        if self.is_static:
            prefixes.append("static")
        if self.is_virtual:
            prefixes.append("virtual")
        if self.is_const:
            prefixes.append("const")
        if self.is_noexcept:
            prefixes.append("noexcept")
        if self.is_override:
            prefixes.append("override")
        if self.is_final:
            prefixes.append("final")
        if self.is_inline:
            prefixes.append("inline")
        if self.is_extern:
            prefixes.append("extern")

        prefix_str = " ".join(prefixes)
        if prefix_str:
            return f"{prefix_str} {self.return_type} {self.name}({params}){suffix}"
        return f"{self.return_type} {self.name}({params}){suffix}"
    
    def is_constructor(self) -> bool:
        """Check if this is a constructor"""
        return self.name == self.return_type
    
    def is_destructor(self) -> bool:
        """Check if this is a destructor"""
        return self.name.startswith('~')
