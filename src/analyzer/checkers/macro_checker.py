"""
Macro compatibility checker
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition, Macro

from .base_checker import BaseChecker
from ..models.compatibility_models import CompatibilityIssue, ChangeType, CompatibilityLevel


class MacroChecker(BaseChecker):
    """Checker for macro compatibility"""
    
    def __init__(self):
        super().__init__()
        self._change_type_severity_map = self._initialize_severity_mapping()
    
    def _initialize_severity_mapping(self) -> Dict[ChangeType, CompatibilityLevel]:
        """Map change types to their severity levels for macros"""
        return {
            ChangeType.MACRO_REMOVED: CompatibilityLevel.CRITICAL,
            ChangeType.MACRO_VALUE_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.MACRO_ADDED: CompatibilityLevel.INFO,
        }
    
    def _get_severity_level(self, change_type: ChangeType) -> CompatibilityLevel:
        """Get severity level for a change type"""
        return self._change_type_severity_map.get(change_type, CompatibilityLevel.WARNING)
    
    def check(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check macro compatibility"""
        self.issues = []
        self._check_macros_compatibility(old_api.macros, new_api.macros)
        return self.issues
    
    def _check_macros_compatibility(self, old_macros: Dict[str, Macro], new_macros: Dict[str, Macro]):
        """Check macro compatibility"""
        old_names = set(old_macros.keys())
        new_names = set(new_macros.keys())
        
        # Check removed macros
        for removed_macro in old_names - new_names:
            level = self._get_severity_level(ChangeType.MACRO_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.MACRO_REMOVED,
                level=level,
                description=f"Macro '{removed_macro}' has been removed",
                element_name=removed_macro,
                element_type="macro"
            ))
        
        # Check added macros
        for added_macro in new_names - old_names:
            level = self._get_severity_level(ChangeType.MACRO_ADDED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.MACRO_ADDED,
                level=level,
                description=f"Macro '{added_macro}' has been added",
                element_name=added_macro,
                element_type="macro"
            ))
        
        # Check macro value changes
        for macro_name in old_names & new_names:
            old_macro = old_macros[macro_name]
            new_macro = new_macros[macro_name]
            
            if old_macro.value != new_macro.value:
                level = self._get_severity_level(ChangeType.MACRO_VALUE_CHANGED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.MACRO_VALUE_CHANGED,
                    level=level,
                    old_signature=f"#define {macro_name} {old_macro.value}",
                    new_signature=f"#define {macro_name} {new_macro.value}",
                    description=f"Macro '{macro_name}' value changed",
                    element_name=macro_name,
                    element_type="macro"
                ))
