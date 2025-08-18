"""
Report generation utilities
"""

import json
from typing import List, Dict
from ..models.compatibility_models import CompatibilityIssue, IncompatibilityScore, CompatibilityLevel


class ReportGenerator:
    """Generate compatibility analysis reports in various formats"""
    
    @staticmethod
    def generate_json_report(issues: List[CompatibilityIssue], summary: Dict[str, int], 
                           incompatibility_score: IncompatibilityScore) -> str:
        """Generate JSON format report"""
        report_data = {
            'incompatibility_assessment': incompatibility_score.to_dict(),
            'summary': summary,
            'issues': [issue.to_dict() for issue in issues]
        }
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_text_report(issues: List[CompatibilityIssue], summary: Dict[str, int], 
                           incompatibility_score: IncompatibilityScore = None) -> str:
        """Generate text format report"""
        report = []
        report.append("API Compatibility Analysis Report")
        report.append("=" * 40)
        report.append("")
        
        # Overall incompatibility assessment
        if incompatibility_score:
            report.append("INCOMPATIBILITY ASSESSMENT:")
            report.append("-" * 30)
            report.append(f"  Incompatibility Score: {incompatibility_score.total_score:.1f}/{incompatibility_score.max_possible_score:.1f}")
            report.append(f"  Incompatibility Percentage: {incompatibility_score.incompatibility_percentage:.1f}%")
            report.append("")
            
            report.append("ISSUE BREAKDOWN:")
            report.append("-" * 16)
            report.append(f"  ERROR (Compilation Breaking): {incompatibility_score.error_count}")
            report.append(f"  CRITICAL (Runtime Risk): {incompatibility_score.critical_count}")
            report.append(f"  WARNING (Attention Needed): {incompatibility_score.warning_count}")
            report.append(f"  INFO (New Features): {incompatibility_score.info_count}")
            report.append("")
        
        # Legacy summary
        report.append("Summary:")
        report.append(f"  Total issues: {summary['total_issues']}")
        report.append(f"  Breaking changes: {summary['breaking_changes']}")
        report.append(f"  Backward compatible: {summary['backward_compatible']}")
        report.append(f"  API additions: {summary['api_additions']}")
        report.append("")
        
        if issues:
            # Group by severity level
            error_issues = [i for i in issues if i.level == CompatibilityLevel.ERROR]
            critical_issues = [i for i in issues if i.level == CompatibilityLevel.CRITICAL]
            warning_issues = [i for i in issues if i.level == CompatibilityLevel.WARNING]
            info_issues = [i for i in issues if i.level == CompatibilityLevel.INFO]
            
            def format_issue_section(title: str, issue_list: List[CompatibilityIssue], description: str):
                if issue_list:
                    report.append(f"{title}:")
                    report.append(f"({description})")
                    report.append("-" * len(title))
                    for issue in issue_list:
                        report.append(f"  • {issue.description}")
                        if issue.old_signature:
                            report.append(f"    Old: {issue.old_signature}")
                        if issue.new_signature:
                            report.append(f"    New: {issue.new_signature}")
                        report.append("")
            
            format_issue_section("ERROR LEVEL ISSUES", error_issues, 
                                "Will cause compilation failure")
            format_issue_section("CRITICAL LEVEL ISSUES", critical_issues,
                                "May cause runtime errors")
            format_issue_section("WARNING LEVEL ISSUES", warning_issues,
                                "Needs attention but won't immediately fail")
            format_issue_section("INFO LEVEL ISSUES", info_issues,
                                "Backward compatible, usually new features")
        else:
            report.append("No compatibility issues found!")
        
        return "\n".join(report)
