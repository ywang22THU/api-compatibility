"""
Member model for class member variables
"""

from dataclasses import dataclass


@dataclass
class Member:
    """Class member variable"""
    name: str
    type: str
    access_level: str = "private"
    is_static: bool = False
    is_const: bool = False
