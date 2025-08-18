"""
Compatibility analysis models and data structures
"""

from dataclasses import dataclass
from enum import Enum as PyEnum
from typing import Optional


class CompatibilityLevel(PyEnum):
    """Compatibility level with severity scoring"""
    ERROR = "error"           # Breaking changes that cause compilation failure (score: 10)
    CRITICAL = "critical"     # Serious behavioral changes that may cause runtime errors (score: 7)
    WARNING = "warning"       # Changes that might affect functionality (score: 3)
    INFO = "info"            # Informational changes, usually backward compatible additions (score: 1)
    
    @property
    def severity_score(self) -> int:
        """Get severity score for incompatibility calculation"""
        scores = {
            CompatibilityLevel.ERROR: 10,
            CompatibilityLevel.CRITICAL: 5, 
            CompatibilityLevel.WARNING: 1,
            CompatibilityLevel.INFO: 0
        }
        return scores[self]
    
    @property
    def description(self) -> str:
        """Get human-readable description"""
        descriptions = {
            CompatibilityLevel.ERROR: "Will cause compilation failure",
            CompatibilityLevel.CRITICAL: "May cause runtime errors",
            CompatibilityLevel.WARNING: "Needs attention but won't immediately fail",
            CompatibilityLevel.INFO: "Backward compatible, usually new features"
        }
        return descriptions[self]


class ChangeType(PyEnum):
    """Change type"""
    # Function related
    FUNCTION_ADDED = "function_added"
    FUNCTION_REMOVED = "function_removed"
    FUNCTION_SIGNATURE_CHANGED = "function_signature_changed"
    FUNCTION_RETURN_TYPE_CHANGED = "function_return_type_changed"
    FUNCTION_PARAMETER_ADDED = "function_parameter_added"
    FUNCTION_PARAMETER_REMOVED = "function_parameter_removed"
    FUNCTION_PARAMETER_TYPE_CHANGED = "function_parameter_type_changed"
    FUNCTION_MODIFIER_CHANGED = "function_modifier_changed"
    
    # Class related
    CLASS_ADDED = "class_added"
    CLASS_REMOVED = "class_removed"
    CLASS_INHERITANCE_CHANGED = "class_inheritance_changed"
    CLASS_FINAL_MODIFIER_CHANGED = "class_final_modifier_changed"
    
    # Enum related
    ENUM_ADDED = "enum_added"
    ENUM_REMOVED = "enum_removed"
    ENUM_MEMBER_ADDED = "enum_member_added"
    ENUM_MEMBER_REMOVED = "enum_member_removed"
    ENUM_MEMBER_VALUE_CHANGED = "enum_member_value_changed"
    
    # Macro related
    MACRO_ADDED = "macro_added"
    MACRO_REMOVED = "macro_removed"
    MACRO_VALUE_CHANGED = "macro_value_changed"


@dataclass
class CompatibilityIssue:
    """Compatibility issue"""
    change_type: ChangeType
    level: CompatibilityLevel
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    description: str = ""
    element_name: str = ""
    element_type: str = ""  # class, function, enum, macro
    severity_score: Optional[float] = None  # Custom severity score, overrides level.severity_score
    
    @property
    def effective_severity_score(self) -> float:
        """Get effective severity score (custom or default from level)"""
        return self.severity_score if self.severity_score is not None else self.level.severity_score
    
    def to_dict(self) -> dict:
        return {
            'change_type': self.change_type.value,
            'level': self.level.value,
            'level_description': self.level.description,
            'severity_score': self.effective_severity_score,
            'old_signature': self.old_signature,
            'new_signature': self.new_signature,
            'description': self.description,
            'element_name': self.element_name,
            'element_type': self.element_type
        }


@dataclass
class IncompatibilityScore:
    """Overall incompatibility assessment"""
    total_score: float
    max_possible_score: float
    incompatibility_percentage: float
    total_issues: int
    error_count: int
    critical_count: int
    warning_count: int
    info_count: int
    # New fields for old API compatibility assessment
    old_api_count: int = 0  # Total number of APIs in old version
    broken_old_api_count: int = 0  # Number of old APIs affected by ERROR level changes
    old_api_breakage_percentage: float = 0.0  # Percentage of old APIs that are broken
    
    def to_dict(self) -> dict:
        return {
            'total_score': self.total_score,
            'max_possible_score': self.max_possible_score,
            'incompatibility_percentage': self.incompatibility_percentage,
            'total_issues': self.total_issues,
            'breakdown': {
                'error': self.error_count,
                'critical': self.critical_count,
                'warning': self.warning_count,
                'info': self.info_count
            },
            'old_api_compatibility': {
                'total_old_apis': self.old_api_count,
                'broken_old_apis': self.broken_old_api_count,
                'breakage_percentage': self.old_api_breakage_percentage
            }
        }
