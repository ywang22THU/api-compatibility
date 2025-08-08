"""
Class models for C++ classes
"""

from dataclasses import dataclass, field
from typing import List
from .function import Function
from .member import Member


@dataclass
class Class:
    """Class definition"""
    name: str
    base_classes: List[str] = field(default_factory=list)
    methods: List[Function] = field(default_factory=list)
    members: List[Member] = field(default_factory=list)
    is_final: bool = False
    nested_classes: List['Class'] = field(default_factory=list)
