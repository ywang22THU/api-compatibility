#!/usr/bin/env python3
"""
API Compatibility Analysis Tool
Analyzes compatibility differences between two C++ API versions and generates detailed reports
"""

import json
import argparse
from typing import Dict, List, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import sys
from pathlib import Path


class Severity(Enum):
    """Issue severity levels"""
    ERROR = "ERROR"        # Breaking changes that will cause compilation failures
    CRITICAL = "CRITICAL"  # Serious behavioral changes that may cause runtime errors
    WARNING = "WARNING"    # Changes that may affect functionality
    INFO = "INFO"         # Informational changes, usually new features


@dataclass
class CompatibilityIssue:
    """Compatibility issue"""
    severity: Severity
    category: str
    description: str
    details: str
    file_path: str = ""
    old_signature: str = ""
    new_signature: str = ""


class APICompatibilityAnalyzer:
    """API compatibility analyzer"""
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
    
    def analyze(self, v1_path: str, v2_path: str) -> List[CompatibilityIssue]:
        """Analyze compatibility between two API versions"""
        # Load API data
        with open(v1_path, 'r', encoding='utf-8') as f:
            v1_data = json.load(f)
        
        with open(v2_path, 'r', encoding='utf-8') as f:
            v2_data = json.load(f)
        
        # Clear previous analysis results
        self.issues = []
        
        # Analyze header file level changes
        self._analyze_header_files(v1_data, v2_data)
        
        # Analyze specific API changes
        for file_path in v1_data.get('header_files', {}):
            v1_file_data = v1_data['header_files'][file_path]
            v2_file_data = v2_data.get('header_files', {}).get(file_path, {})
            
            self._analyze_file_apis(file_path, v1_file_data, v2_file_data)
        
        # Analyze newly added header files
        for file_path in v2_data.get('header_files', {}):
            if file_path not in v1_data.get('header_files', {}):
                self._analyze_new_file(file_path, v2_data['header_files'][file_path])
        
        return self.issues
    
    def _analyze_header_files(self, v1_data: Dict, v2_data: Dict):
        """Analyze header file level changes"""
        v1_files = set(v1_data.get('header_files', {}).keys())
        v2_files = set(v2_data.get('header_files', {}).keys())
        
        # Check for removed header files
        removed_files = v1_files - v2_files
        for file_path in removed_files:
            self.issues.append(CompatibilityIssue(
                severity=Severity.ERROR,
                category="File Removal",
                description=f"Header file removed: {file_path}",
                details="Complete removal of header file will cause compilation failures for code depending on this file",
                file_path=file_path
            ))
        
        # Check for newly added header files
        added_files = v2_files - v1_files
        for file_path in added_files:
            self.issues.append(CompatibilityIssue(
                severity=Severity.INFO,
                category="File Addition",
                description=f"New header file added: {file_path}",
                details="Newly added header file provides additional functionality without affecting existing code compatibility",
                file_path=file_path
            ))
    
    def _analyze_file_apis(self, file_path: str, v1_data: Dict, v2_data: Dict):
        """Analyze API changes in a single file"""
        # Analyze enums
        self._analyze_enums(file_path, v1_data.get('enums', []), v2_data.get('enums', []))
        
        # Analyze classes
        self._analyze_classes(file_path, v1_data.get('classes', []), v2_data.get('classes', []))
        
        # Analyze functions
        self._analyze_functions(file_path, v1_data.get('functions', []), v2_data.get('functions', []))
    
    def _analyze_new_file(self, file_path: str, file_data: Dict):
        """Analyze content in newly added files"""
        # All APIs in new files are new features
        for enum_data in file_data.get('enums', []):
            self.issues.append(CompatibilityIssue(
                severity=Severity.INFO,
                category="Enum Addition",
                description=f"New enum added: {enum_data['name']}",
                details=f"New enum type added in new file {file_path}",
                file_path=file_path
            ))
        
        for class_data in file_data.get('classes', []):
            self.issues.append(CompatibilityIssue(
                severity=Severity.INFO,
                category="Class Addition",
                description=f"New class added: {class_data['name']}",
                details=f"New class added in new file {file_path}",
                file_path=file_path
            ))
        
        for func_data in file_data.get('functions', []):
            self.issues.append(CompatibilityIssue(
                severity=Severity.INFO,
                category="Function Addition",
                description=f"New function added: {func_data['name']}",
                details=f"New function added in new file {file_path}",
                file_path=file_path
            ))
    
    def _analyze_enums(self, file_path: str, v1_enums: List[Dict], v2_enums: List[Dict]):
        """Analyze enum changes"""
        v1_enum_map = {enum['name']: enum for enum in v1_enums}
        v2_enum_map = {enum['name']: enum for enum in v2_enums}
        
        # Check for removed enums
        for enum_name in v1_enum_map:
            if enum_name not in v2_enum_map:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Enum Removal",
                    description=f"Enum removed: {enum_name}",
                    details="Removing enum will cause compilation failures for code using this enum",
                    file_path=file_path
                ))
        
        # Check enum value changes
        for enum_name in v1_enum_map:
            if enum_name in v2_enum_map:
                self._analyze_enum_values(file_path, enum_name, 
                                        v1_enum_map[enum_name], v2_enum_map[enum_name])
        
        # Check for newly added enums
        for enum_name in v2_enum_map:
            if enum_name not in v1_enum_map:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.INFO,
                    category="Enum Addition",
                    description=f"New enum added: {enum_name}",
                    details="New enum does not affect existing code compatibility",
                    file_path=file_path
                ))
    
    def _analyze_enum_values(self, file_path: str, enum_name: str, v1_enum: Dict, v2_enum: Dict):
        """Analyze enum value changes"""
        v1_values = {val['name']: val['value'] for val in v1_enum.get('enumerators', [])}
        v2_values = {val['name']: val['value'] for val in v2_enum.get('enumerators', [])}
        
        # Check for removed enum values
        for val_name in v1_values:
            if val_name not in v2_values:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Enum Value Removal",
                    description=f"Enum value removed: {enum_name}::{val_name}",
                    details="Removing enum value will cause compilation failures for code using this value",
                    file_path=file_path
                ))
        
        # Check enum value changes
        for val_name in v1_values:
            if val_name in v2_values and v1_values[val_name] != v2_values[val_name]:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.CRITICAL,
                    category="Enum Value Change",
                    description=f"Enum value changed: {enum_name}::{val_name}",
                    details=f"Value changed from {v1_values[val_name]} to {v2_values[val_name]}, may cause runtime behavior changes",
                    file_path=file_path,
                    old_signature=f"{val_name} = {v1_values[val_name]}",
                    new_signature=f"{val_name} = {v2_values[val_name]}"
                ))
        
        # Check for newly added enum values
        for val_name in v2_values:
            if val_name not in v1_values:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.INFO,
                    category="Enum Value Addition",
                    description=f"New enum value added: {enum_name}::{val_name}",
                    details="New enum value typically does not affect existing code compatibility",
                    file_path=file_path
                ))
    
    def _analyze_classes(self, file_path: str, v1_classes: List[Dict], v2_classes: List[Dict]):
        """Analyze class changes"""
        v1_class_map = {cls['name']: cls for cls in v1_classes}
        v2_class_map = {cls['name']: cls for cls in v2_classes}
        
        # Check for removed classes
        for class_name in v1_class_map:
            if class_name not in v2_class_map:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Class Removal",
                    description=f"Class removed: {class_name}",
                    details="Removing class will cause compilation failures for code using this class",
                    file_path=file_path
                ))
        
        # Check class changes
        for class_name in v1_class_map:
            if class_name in v2_class_map:
                self._analyze_class_changes(file_path, class_name,
                                          v1_class_map[class_name], v2_class_map[class_name])
        
        # Check for newly added classes
        for class_name in v2_class_map:
            if class_name not in v1_class_map:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.INFO,
                    category="Class Addition",
                    description=f"New class added: {class_name}",
                    details="New class does not affect existing code compatibility",
                    file_path=file_path
                ))
    
    def _analyze_class_changes(self, file_path: str, class_name: str, v1_class: Dict, v2_class: Dict):
        """Analyze specific class changes"""
        # Analyze inheritance relationship changes
        self._analyze_inheritance_changes(file_path, class_name, v1_class, v2_class)
        
        # Analyze member variable changes
        self._analyze_field_changes(file_path, class_name, v1_class, v2_class)
        
        # Analyze member function changes
        self._analyze_method_changes(file_path, class_name, v1_class, v2_class)
    
    def _analyze_inheritance_changes(self, file_path: str, class_name: str, v1_class: Dict, v2_class: Dict):
        """Analyze inheritance relationship changes"""
        v1_bases = {base['name']: base for base in v1_class.get('bases', [])}
        v2_bases = {base['name']: base for base in v2_class.get('bases', [])}
        
        # Check for removed base classes
        for base_name in v1_bases:
            if base_name not in v2_bases:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Base Class Removal",
                    description=f"Class {class_name} removed base class: {base_name}",
                    details="Removing base class may cause compilation errors and runtime issues",
                    file_path=file_path
                ))
        
        # Check for newly added base classes
        for base_name in v2_bases:
            if base_name not in v1_bases:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.WARNING,
                    category="Base Class Addition",
                    description=f"Class {class_name} added new base class: {base_name}",
                    details="Adding base class may change object layout and vtable structure",
                    file_path=file_path
                ))
    
    def _analyze_field_changes(self, file_path: str, class_name: str, v1_class: Dict, v2_class: Dict):
        """Analyze member variable changes"""
        v1_fields = {field['name']: field for field in v1_class.get('fields', [])}
        v2_fields = {field['name']: field for field in v2_class.get('fields', [])}
        
        # Check for removed member variables
        for field_name in v1_fields:
            if field_name not in v2_fields:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Member Variable Removal",
                    description=f"Class {class_name} removed member variable: {field_name}",
                    details="Removing public member variable will cause compilation errors",
                    file_path=file_path
                ))
        
        # Check member variable type changes
        for field_name in v1_fields:
            if field_name in v2_fields:
                v1_field = v1_fields[field_name]
                v2_field = v2_fields[field_name]
                if v1_field['type'] != v2_field['type']:
                    self.issues.append(CompatibilityIssue(
                        severity=Severity.ERROR,
                        category="Member Variable Type Change",
                        description=f"Class {class_name} member variable {field_name} type changed",
                        details=f"Type changed from {v1_field['type']} to {v2_field['type']}",
                        file_path=file_path,
                        old_signature=f"{v1_field['type']} {field_name}",
                        new_signature=f"{v2_field['type']} {field_name}"
                    ))
                
                # Check access permission changes
                if v1_field['access'] != v2_field['access']:
                    severity = Severity.ERROR if v2_field['access'] == 'PRIVATE' else Severity.WARNING
                    self.issues.append(CompatibilityIssue(
                        severity=severity,
                        category="Member Variable Access Change",
                        description=f"Class {class_name} member variable {field_name} access permission changed",
                        details=f"Access changed from {v1_field['access']} to {v2_field['access']}",
                        file_path=file_path
                    ))
        
        # Check for newly added member variables
        for field_name in v2_fields:
            if field_name not in v1_fields:
                self.issues.append(CompatibilityIssue(
                    severity=Severity.WARNING,
                    category="Member Variable Addition",
                    description=f"Class {class_name} added new member variable: {field_name}",
                    details="Adding member variable may change object size and memory layout",
                    file_path=file_path
                ))
    
    def _analyze_method_changes(self, file_path: str, class_name: str, v1_class: Dict, v2_class: Dict):
        """Analyze member function changes"""
        v1_methods = self._create_method_map(v1_class.get('methods', []))
        v2_methods = self._create_method_map(v2_class.get('methods', []))
        
        # Check for removed methods
        for method_sig in v1_methods:
            if method_sig not in v2_methods:
                method = v1_methods[method_sig]
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Method Removal",
                    description=f"Class {class_name} removed method: {method['name']}",
                    details="Removing public method will cause compilation failures for code calling this method",
                    file_path=file_path,
                    old_signature=self._format_method_signature(method)
                ))
        
        # Check method changes
        for method_sig in v1_methods:
            if method_sig in v2_methods:
                self._analyze_method_details(file_path, class_name, 
                                           v1_methods[method_sig], v2_methods[method_sig])
        
        # Check for newly added methods
        for method_sig in v2_methods:
            if method_sig not in v1_methods:
                method = v2_methods[method_sig]
                self.issues.append(CompatibilityIssue(
                    severity=Severity.INFO,
                    category="Method Addition",
                    description=f"Class {class_name} added new method: {method['name']}",
                    details="New method typically does not affect existing code compatibility",
                    file_path=file_path,
                    new_signature=self._format_method_signature(method)
                ))
    
    def _create_method_map(self, methods: List[Dict]) -> Dict[str, Dict]:
        """Create method mapping using method signature as key"""
        method_map = {}
        for method in methods:
            # Create method signature: method name + parameter types
            param_types = [param['type'] for param in method.get('parameters', [])]
            signature = f"{method['name']}({','.join(param_types)})"
            method_map[signature] = method
        return method_map
    
    def _analyze_method_details(self, file_path: str, class_name: str, v1_method: Dict, v2_method: Dict):
        """Analyze detailed method changes"""
        method_name = v1_method['name']
        
        # Check return type changes
        if v1_method['return_type'] != v2_method['return_type']:
            self.issues.append(CompatibilityIssue(
                severity=Severity.ERROR,
                category="Method Return Type Change",
                description=f"Class {class_name} method {method_name} return type changed",
                details=f"Return type changed from {v1_method['return_type']} to {v2_method['return_type']}",
                file_path=file_path,
                old_signature=self._format_method_signature(v1_method),
                new_signature=self._format_method_signature(v2_method)
            ))
        
        # Check exception specification changes
        if v1_method.get('exception_spec', '') != v2_method.get('exception_spec', ''):
            severity = Severity.WARNING if v2_method.get('exception_spec') == 'noexcept' else Severity.CRITICAL
            self.issues.append(CompatibilityIssue(
                severity=severity,
                category="Method Exception Specification Change",
                description=f"Class {class_name} method {method_name} exception specification changed",
                details=f"Exception specification changed from '{v1_method.get('exception_spec', '')}' to '{v2_method.get('exception_spec', '')}'",
                file_path=file_path
            ))
        
        # Check virtual function attribute changes
        if v1_method.get('is_virtual', False) != v2_method.get('is_virtual', False):
            self.issues.append(CompatibilityIssue(
                severity=Severity.CRITICAL,
                category="Method Virtual Attribute Change",
                description=f"Class {class_name} method {method_name} virtual function attribute changed",
                details="Virtual function attribute change affects polymorphic behavior and vtable structure",
                file_path=file_path
            ))
        
        # Check access permission changes
        if v1_method.get('access', 'PUBLIC') != v2_method.get('access', 'PUBLIC'):
            severity = Severity.ERROR if v2_method.get('access') == 'PRIVATE' else Severity.WARNING
            self.issues.append(CompatibilityIssue(
                severity=severity,
                category="Method Access Permission Change",
                description=f"Class {class_name} method {method_name} access permission changed",
                details=f"Access changed from {v1_method.get('access', 'PUBLIC')} to {v2_method.get('access', 'PUBLIC')}",
                file_path=file_path
            ))
    
    def _analyze_functions(self, file_path: str, v1_functions: List[Dict], v2_functions: List[Dict]):
        """Analyze global function changes"""
        v1_func_map = self._create_function_map(v1_functions)
        v2_func_map = self._create_function_map(v2_functions)
        
        # Check for removed functions
        for func_sig in v1_func_map:
            if func_sig not in v2_func_map:
                func = v1_func_map[func_sig]
                self.issues.append(CompatibilityIssue(
                    severity=Severity.ERROR,
                    category="Function Removal",
                    description=f"Global function removed: {func['name']}",
                    details="Removing global function will cause compilation failures for code calling this function",
                    file_path=file_path,
                    old_signature=self._format_function_signature(func)
                ))
        
        # Check function changes
        for func_sig in v1_func_map:
            if func_sig in v2_func_map:
                v1_func = v1_func_map[func_sig]
                v2_func = v2_func_map[func_sig]
                
                # Check return type changes
                if v1_func['return_type'] != v2_func['return_type']:
                    self.issues.append(CompatibilityIssue(
                        severity=Severity.ERROR,
                        category="Function Return Type Change",
                        description=f"Function {v1_func['name']} return type changed",
                        details=f"Return type changed from {v1_func['return_type']} to {v2_func['return_type']}",
                        file_path=file_path,
                        old_signature=self._format_function_signature(v1_func),
                        new_signature=self._format_function_signature(v2_func)
                    ))
        
        # Check for newly added functions
        for func_sig in v2_func_map:
            if func_sig not in v1_func_map:
                func = v2_func_map[func_sig]
                self.issues.append(CompatibilityIssue(
                    severity=Severity.INFO,
                    category="Function Addition",
                    description=f"New global function added: {func['name']}",
                    details="New function does not affect existing code compatibility",
                    file_path=file_path,
                    new_signature=self._format_function_signature(func)
                ))
    
    def _create_function_map(self, functions: List[Dict]) -> Dict[str, Dict]:
        """Create function mapping"""
        func_map = {}
        for func in functions:
            param_types = [param['type'] for param in func.get('parameters', [])]
            signature = f"{func['name']}({','.join(param_types)})"
            func_map[signature] = func
        return func_map
    
    def _format_method_signature(self, method: Dict) -> str:
        """Format method signature"""
        params = [f"{p['type']} {p['name']}" for p in method.get('parameters', [])]
        return f"{method['return_type']} {method['name']}({', '.join(params)})"
    
    def _format_function_signature(self, func: Dict) -> str:
        """Format function signature"""
        params = [f"{p['type']} {p['name']}" for p in func.get('parameters', [])]
        return f"{func['return_type']} {func['name']}({', '.join(params)})"


def generate_report(issues: List[CompatibilityIssue], output_path: str = None):
    """Generate compatibility analysis report"""
    
    # Count issues by severity
    severity_counts = {severity: 0 for severity in Severity}
    for issue in issues:
        severity_counts[issue.severity] += 1
    
    # Sort by severity
    severity_order = [Severity.ERROR, Severity.CRITICAL, Severity.WARNING, Severity.INFO]
    sorted_issues = sorted(issues, key=lambda x: severity_order.index(x.severity))
    
    # Generate report content
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("API Compatibility Analysis Report")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append(f"Total {len(issues)} compatibility issues found:")
    for severity in severity_order:
        count = severity_counts[severity]
        if count > 0:
            report_lines.append(f"  - {severity.value}: {count} issues")
    report_lines.append("")
    
    # Severity level descriptions
    report_lines.append("## Severity Level Descriptions")
    report_lines.append("- ERROR: Breaking changes that will cause compilation failures")
    report_lines.append("- CRITICAL: Serious behavioral changes that may cause runtime errors")  
    report_lines.append("- WARNING: Changes that may affect functionality")
    report_lines.append("- INFO: Informational changes, usually new features")
    report_lines.append("")
    
    # Detailed issue list
    report_lines.append("## Detailed Issue List")
    report_lines.append("")
    
    current_severity = None
    for issue in sorted_issues:
        if current_severity != issue.severity:
            current_severity = issue.severity
            report_lines.append(f"### {issue.severity.value} Level Issues")
            report_lines.append("")
        
        report_lines.append(f"**{issue.category}**")
        report_lines.append(f"- Description: {issue.description}")
        report_lines.append(f"- Details: {issue.details}")
        if issue.file_path:
            report_lines.append(f"- File: {issue.file_path}")
        if issue.old_signature:
            report_lines.append(f"- Original signature: `{issue.old_signature}`")
        if issue.new_signature:
            report_lines.append(f"- New signature: `{issue.new_signature}`")
        report_lines.append("")
    
    # Output report
    report_content = '\n'.join(report_lines)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report saved to: {output_path}")
    else:
        print(report_content)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="API Compatibility Analysis Tool")
    parser.add_argument('v1_api', help='Path to the first version API JSON file')
    parser.add_argument('v2_api', help='Path to the second version API JSON file')
    parser.add_argument('-o', '--output', help='Output report file path (optional)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', 
                       help='Output format (text or json)')
    
    args = parser.parse_args()
    
    # Check input files
    if not Path(args.v1_api).exists():
        print(f"Error: File does not exist {args.v1_api}")
        sys.exit(1)
    
    if not Path(args.v2_api).exists():
        print(f"Error: File does not exist {args.v2_api}")
        sys.exit(1)
    
    # Execute analysis
    analyzer = APICompatibilityAnalyzer()
    issues = analyzer.analyze(args.v1_api, args.v2_api)
    
    # Generate report
    if args.format == 'json':
        # JSON format output
        json_output = {
            'summary': {
                'total_issues': len(issues),
                'by_severity': {severity.value: sum(1 for issue in issues if issue.severity == severity) 
                               for severity in Severity}
            },
            'issues': [
                {
                    'severity': issue.severity.value,
                    'category': issue.category,
                    'description': issue.description,
                    'details': issue.details,
                    'file_path': issue.file_path,
                    'old_signature': issue.old_signature,
                    'new_signature': issue.new_signature
                }
                for issue in issues
            ]
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=2, ensure_ascii=False)
            print(f"JSON report saved to: {args.output}")
        else:
            print(json.dumps(json_output, indent=2, ensure_ascii=False))
    else:
        # Text format output
        generate_report(issues, args.output)


if __name__ == '__main__':
    main()
