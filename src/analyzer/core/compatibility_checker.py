"""
Main compatibility checker that coordinates all specialized checkers
"""

from typing import List, Dict
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition

from ..models.compatibility_models import CompatibilityIssue, IncompatibilityScore, CompatibilityLevel
from ..checkers import ClassChecker, EnumChecker, MacroChecker


class CompatibilityChecker:
    """Main compatibility checker that coordinates all specialized checkers"""
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
        self.old_api = None  # Store old API for compatibility analysis
        self.class_checker = ClassChecker()
        self.enum_checker = EnumChecker()
        self.macro_checker = MacroChecker()
    
    def check_compatibility(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check compatibility between two API versions"""
        self.issues = []
        self.old_api = old_api  # Store for old API count calculation
        
        # Run all checkers and collect issues
        self.issues.extend(self.class_checker.check(old_api, new_api))
        self.issues.extend(self.enum_checker.check(old_api, new_api))
        self.issues.extend(self.macro_checker.check(old_api, new_api))
        
        return self.issues
    
    def calculate_incompatibility_score(self) -> IncompatibilityScore:
        """Calculate overall incompatibility score"""
        total_score = 0.0
        error_count = 0
        critical_count = 0
        warning_count = 0
        info_count = 0
        
        # Count issues by severity and calculate score
        for issue in self.issues:
            total_score += issue.effective_severity_score
            if issue.level == CompatibilityLevel.ERROR:
                error_count += 1
            elif issue.level == CompatibilityLevel.CRITICAL:
                critical_count += 1
            elif issue.level == CompatibilityLevel.WARNING:
                warning_count += 1
            elif issue.level == CompatibilityLevel.INFO:
                info_count += 1
        
        # Calculate maximum possible score (assuming all issues were ERROR level)
        max_possible_score = len(self.issues) * CompatibilityLevel.ERROR.severity_score
        
        # Calculate incompatibility percentage
        if max_possible_score > 0:
            incompatibility_percentage = (total_score / max_possible_score) * 100
        else:
            incompatibility_percentage = 0.0
        
        # Calculate old API compatibility metrics
        old_api_count = 0
        broken_old_api_count = 0
        old_api_breakage_percentage = 0.0
        
        if hasattr(self, 'old_api') and self.old_api:
            old_api_count = self._count_old_api_elements(self.old_api)
            broken_old_api_count = self._count_broken_old_apis()
            if old_api_count > 0:
                old_api_breakage_percentage = (broken_old_api_count / old_api_count) * 100
        
        return IncompatibilityScore(
            total_score=total_score,
            max_possible_score=max_possible_score,
            incompatibility_percentage=incompatibility_percentage,
            total_issues=len(self.issues),
            error_count=error_count,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            old_api_count=old_api_count,
            broken_old_api_count=broken_old_api_count,
            old_api_breakage_percentage=old_api_breakage_percentage
        )
    
    def generate_summary(self) -> Dict[str, int]:
        """Generate compatibility summary (backward compatibility)"""
        summary = {
            'total_issues': len(self.issues),
            'breaking_changes': 0,
            'backward_compatible': 0,
            'api_additions': 0,
            'compatible': 0
        }
        
        # Map new levels to old categories for backward compatibility
        for issue in self.issues:
            if issue.level in [CompatibilityLevel.ERROR, CompatibilityLevel.CRITICAL]:
                summary['breaking_changes'] += 1
            elif issue.level == CompatibilityLevel.WARNING:
                summary['backward_compatible'] += 1
            elif issue.level == CompatibilityLevel.INFO:
                summary['api_additions'] += 1
        
        return summary
    
    def _count_old_api_elements(self, old_api: APIDefinition) -> int:
        """Count total number of API elements in old version"""
        count = 0
        
        # Count classes and their methods
        for class_def in old_api.classes.values():
            count += 1  # Count the class itself
            count += len(class_def.methods)  # Count all methods
        
        # Count enums and their members
        for enum_def in old_api.enums.values():
            count += 1  # Count the enum itself
            count += len(enum_def.members)  # Count all enum members
        
        # Count macros
        count += len(old_api.macros)
        
        return count
    
    def _count_broken_old_apis(self) -> int:
        """Count unique old API elements affected by above INFO level changes"""
        broken_apis = set()
        
        for issue in self.issues:
            if issue.level != CompatibilityLevel.INFO:
                # Create a unique identifier for the old API element
                if issue.element_type == "class":
                    broken_apis.add(f"class:{issue.element_name}")
                elif issue.element_type == "method":
                    # Extract class name from element_name if it contains "::"
                    if "::" in issue.element_name:
                        class_name = issue.element_name.split("::")[0]
                        broken_apis.add(f"class:{class_name}")
                    broken_apis.add(f"method:{issue.element_name}")
                elif issue.element_type == "enum":
                    broken_apis.add(f"enum:{issue.element_name}")
                elif issue.element_type == "enum_member":
                    # Extract enum name from element_name if it contains "::"
                    if "::" in issue.element_name:
                        enum_name = issue.element_name.split("::")[0]
                        broken_apis.add(f"enum:{enum_name}")
                    broken_apis.add(f"enum_member:{issue.element_name}")
                elif issue.element_type == "macro":
                    broken_apis.add(f"macro:{issue.element_name}")
                else:
                    # Generic handling for other types
                    broken_apis.add(f"{issue.element_type}:{issue.element_name}")
        
        return len(broken_apis)
    
    def _get_broken_old_api_breakdown(self) -> Dict[str, int]:
        """Get breakdown of broken old API elements by type"""
        breakdown = {
            'classes': 0,
            'methods': 0,
            'enums': 0,
            'enum_members': 0,
            'macros': 0,
            'other': 0
        }
        
        broken_apis = set()
        
        for issue in self.issues:
            if issue.level != CompatibilityLevel.INFO:
                element_key = f"{issue.element_type}:{issue.element_name}"
                if element_key not in broken_apis:
                    broken_apis.add(element_key)
                    
                    if issue.element_type == "class":
                        breakdown['classes'] += 1
                    elif issue.element_type == "method":
                        breakdown['methods'] += 1
                    elif issue.element_type == "enum":
                        breakdown['enums'] += 1
                    elif issue.element_type == "enum_member":
                        breakdown['enum_members'] += 1
                    elif issue.element_type == "macro":
                        breakdown['macros'] += 1
                    else:
                        breakdown['other'] += 1
        
        # Return only non-zero counts
        return {k: v for k, v in breakdown.items() if v > 0}
