"""
Enum compatibility checker
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition, Enum

from .base_checker import BaseChecker
from ..models.compatibility_models import CompatibilityIssue, ChangeType, CompatibilityLevel


class EnumChecker(BaseChecker):
    """Checker for enum compatibility"""
    
    def __init__(self):
        super().__init__()
        self._change_type_severity_map = self._initialize_severity_mapping()
    
    def _initialize_severity_mapping(self) -> Dict[ChangeType, CompatibilityLevel]:
        """Map change types to their severity levels for enums"""
        return {
            ChangeType.ENUM_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.ENUM_MEMBER_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.ENUM_MEMBER_VALUE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.ENUM_ADDED: CompatibilityLevel.INFO,
            ChangeType.ENUM_MEMBER_ADDED: CompatibilityLevel.INFO,
        }
    
    def _get_severity_level(self, change_type: ChangeType) -> CompatibilityLevel:
        """Get severity level for a change type"""
        return self._change_type_severity_map.get(change_type, CompatibilityLevel.WARNING)
    
    def check(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check enum compatibility"""
        self.issues = []
        self._check_enums_compatibility(old_api.enums, new_api.enums)
        return self.issues
    
    def _check_enums_compatibility(self, old_enums: Dict[str, Enum], new_enums: Dict[str, Enum]):
        """Check enum compatibility"""
        old_names = set(old_enums.keys())
        new_names = set(new_enums.keys())
        
        # Check removed enums
        for removed_enum in old_names - new_names:
            level = self._get_severity_level(ChangeType.ENUM_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.ENUM_REMOVED,
                level=level,
                description=f"Enum '{removed_enum}' has been removed",
                element_name=removed_enum,
                element_type="enum"
            ))
        
        # Check added enums
        for added_enum in new_names - old_names:
            level = self._get_severity_level(ChangeType.ENUM_ADDED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.ENUM_ADDED,
                level=level,
                description=f"Enum '{added_enum}' has been added",
                element_name=added_enum,
                element_type="enum"
            ))
        
        # Check common enums
        for enum_name in old_names & new_names:
            old_enum = old_enums[enum_name]
            new_enum = new_enums[enum_name]
            self._check_single_enum_compatibility(old_enum, new_enum)
    
    def _check_single_enum_compatibility(self, old_enum: Enum, new_enum: Enum):
        """Check single enum compatibility"""
        enum_name = old_enum.name
        
        old_members = {m.name: m for m in old_enum.members}
        new_members = {m.name: m for m in new_enum.members}
        
        old_member_names = set(old_members.keys())
        new_member_names = set(new_members.keys())
        
        # Check removed enum members
        for removed_member in old_member_names - new_member_names:
            level = self._get_severity_level(ChangeType.ENUM_MEMBER_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.ENUM_MEMBER_REMOVED,
                level=level,
                description=f"Enum '{enum_name}' member '{removed_member}' has been removed",
                element_name=f"{enum_name}::{removed_member}",
                element_type="enum_member"
            ))
        
        # Check added enum members
        for added_member in new_member_names - old_member_names:
            level = self._get_severity_level(ChangeType.ENUM_MEMBER_ADDED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.ENUM_MEMBER_ADDED,
                level=level,
                description=f"Enum '{enum_name}' added member '{added_member}'",
                element_name=f"{enum_name}::{added_member}",
                element_type="enum_member"
            ))
        
        # Check enum member value changes
        for member_name in old_member_names & new_member_names:
            old_member = old_members[member_name]
            new_member = new_members[member_name]
            
            if old_member.value != new_member.value:
                level = self._get_severity_level(ChangeType.ENUM_MEMBER_VALUE_CHANGED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.ENUM_MEMBER_VALUE_CHANGED,
                    level=level,
                    old_signature=f"{member_name} = {old_member.value}",
                    new_signature=f"{member_name} = {new_member.value}",
                    description=f"Enum '{enum_name}' member '{member_name}' value changed",
                    element_name=f"{enum_name}::{member_name}",
                    element_type="enum_member"
                ))
