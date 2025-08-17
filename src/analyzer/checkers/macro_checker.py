"""
Macro compatibility checker
"""

import re
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
            ChangeType.MACRO_VALUE_CHANGED: CompatibilityLevel.WARNING,  # Most macros are not used by user code
            ChangeType.MACRO_ADDED: CompatibilityLevel.INFO,
        }
    
    def _get_severity_level(self, change_type: ChangeType) -> CompatibilityLevel:
        """Get severity level for a change type"""
        return self._change_type_severity_map.get(change_type, CompatibilityLevel.WARNING)
    
    def _is_conditional_compilation_macro(self, macro: Macro) -> bool:
        """Check if a macro is likely a conditional compilation directive"""
        # Common patterns for conditional compilation macros
        conditional_patterns = [
            r'^QT_NO_.*',           # Qt feature disable macros
            r'^QT_FEATURE_.*',      # Qt feature macros
            r'^Q_.*_EXPORT$',       # Qt export macros
            r'.*_H$',               # Header guards
            r'.*_HPP$',             # Header guards
            r'.*_INCLUDED$',        # Header guards
            r'^HAVE_.*',            # CMake/autotools feature macros
            r'^USE_.*',             # Usage control macros
            r'^ENABLE_.*',          # Feature enable macros
            r'^DISABLE_.*',         # Feature disable macros
        ]
        
        # Check if it matches conditional compilation patterns
        for pattern in conditional_patterns:
            if re.match(pattern, macro.name):
                return True
        
        # Also consider macros with no value as conditional compilation
        return macro.value is None or macro.value == ""
    
    def _get_macro_severity_level(self, change_type: ChangeType, macro: Macro) -> CompatibilityLevel:
        """Get severity level for a macro change, considering macro type"""
        base_level = self._get_severity_level(change_type)
        
        # For conditional compilation macros, reduce severity
        if self._is_conditional_compilation_macro(macro):
            if change_type == ChangeType.MACRO_REMOVED:
                return CompatibilityLevel.WARNING  # Reduced from CRITICAL
            elif change_type == ChangeType.MACRO_VALUE_CHANGED:
                return CompatibilityLevel.INFO     # Reduced from WARNING
        
        return base_level
    
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
            macro = old_macros[removed_macro]
            level = self._get_macro_severity_level(ChangeType.MACRO_REMOVED, macro)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.MACRO_REMOVED,
                level=level,
                description=f"Macro '{removed_macro}' has been removed",
                element_name=removed_macro,
                element_type="macro"
            ))
        
        # Check added macros
        for added_macro in new_names - old_names:
            macro = new_macros[added_macro]
            level = self._get_macro_severity_level(ChangeType.MACRO_ADDED, macro)
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
                level = self._get_macro_severity_level(ChangeType.MACRO_VALUE_CHANGED, old_macro)
                
                # Format macro signatures properly, handling None values
                old_value = old_macro.value if old_macro.value is not None else ""
                new_value = new_macro.value if new_macro.value is not None else ""
                
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.MACRO_VALUE_CHANGED,
                    level=level,
                    old_signature=f"#define {macro_name} {old_value}".strip(),
                    new_signature=f"#define {macro_name} {new_value}".strip(),
                    description=f"Macro '{macro_name}' value changed",
                    element_name=macro_name,
                    element_type="macro"
                ))
