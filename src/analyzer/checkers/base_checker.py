"""
Base compatibility checker class
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition

from ..models.compatibility_models import CompatibilityIssue


class BaseChecker(ABC):
    """Base class for compatibility checkers"""
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
    
    @abstractmethod
    def check(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check compatibility and return issues"""
        pass
    
    def get_issues(self) -> List[CompatibilityIssue]:
        """Get all issues found"""
        return self.issues
