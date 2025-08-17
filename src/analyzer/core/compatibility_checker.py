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
from ..checkers import ClassChecker, FunctionChecker, EnumChecker, MacroChecker


class CompatibilityChecker:
    """Main compatibility checker that coordinates all specialized checkers"""
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
        self.class_checker = ClassChecker()
        self.function_checker = FunctionChecker()
        self.enum_checker = EnumChecker()
        self.macro_checker = MacroChecker()
    
    def check_compatibility(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check compatibility between two API versions"""
        self.issues = []
        
        # Run all checkers and collect issues
        self.issues.extend(self.class_checker.check(old_api, new_api))
        # self.issues.extend(self.function_checker.check(old_api, new_api))
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
            total_score += issue.level.severity_score
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
        
        # Determine risk level based on percentage and issue types
        risk_level = self._determine_risk_level(incompatibility_percentage, error_count, critical_count)
        
        return IncompatibilityScore(
            total_score=total_score,
            max_possible_score=max_possible_score,
            incompatibility_percentage=incompatibility_percentage,
            risk_level=risk_level,
            total_issues=len(self.issues),
            error_count=error_count,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count
        )
    
    def _determine_risk_level(self, percentage: float, error_count: int, critical_count: int) -> str:
        """Determine overall risk level"""
        if error_count > 0:
            if percentage >= 80:
                return "CATASTROPHIC"
            elif percentage >= 60:
                return "VERY HIGH"
            else:
                return "HIGH"
        elif critical_count > 0:
            if percentage >= 70:
                return "HIGH"
            elif percentage >= 50:
                return "MODERATE-HIGH"
            else:
                return "MODERATE"
        elif percentage >= 30:
            return "LOW-MODERATE"
        elif percentage > 0:
            return "LOW"
        else:
            return "NONE"
    
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
