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
    is_constexpr: bool = False
    is_constructor: bool = False
    is_destructor: bool = False
    is_deleted: bool = False
    is_deprecated: bool = False
    access_level: str = "public"  # public, protected, private, signals, slots
    
    def signature(self) -> str:
        """Generate function signature"""
        params = ", ".join(str(p) for p in self.parameters)
        prefixes = []
        
        # Handle deleted functions
        suffix = ""
        if self.is_deleted:
            suffix = " = delete"
        elif self.is_virtual and self.is_pure_virtual:
            suffix = " = 0"
        
        if self.is_static:
            prefixes.append("static")
        if self.is_virtual:
            prefixes.append("virtual")
        if self.is_inline:
            prefixes.append("inline")
        if self.is_extern:
            prefixes.append("extern")
        if self.is_constexpr:
            prefixes.append("constexpr")

        prefix_str = " ".join(prefixes)
        
        # Handle constructors and destructors (no return type)
        if self.is_constructor or self.is_destructor:
            if prefix_str:
                return f"{prefix_str} {self.name}({params}){suffix}"
            return f"{self.name}({params}){suffix}"
        
        # Handle regular functions
        const_suffix = " const" if self.is_const else ""
        noexcept_suffix = " noexcept" if self.is_noexcept else ""
        override_suffix = " override" if self.is_override else ""
        final_suffix = " final" if self.is_final else ""
        
        all_suffixes = f"{const_suffix}{noexcept_suffix}{override_suffix}{final_suffix}{suffix}"
        
        if prefix_str:
            return f"{prefix_str} {self.return_type} {self.name}({params}){all_suffixes}"
        return f"{self.return_type} {self.name}({params}){all_suffixes}"
