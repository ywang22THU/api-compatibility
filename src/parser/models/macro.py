"""
Macro model for preprocessor macros
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Macro:
    """Macro definition"""
    name: str
    value: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
