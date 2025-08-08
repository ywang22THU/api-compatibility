"""
Parameter model for function parameters
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Parameter:
    """Function parameter"""
    name: str
    type: str
    default_value: Optional[str] = None
    
    def __str__(self):
        result = f"{self.type} {self.name}"
        if self.default_value:
            result += f" = {self.default_value}"
        return result
