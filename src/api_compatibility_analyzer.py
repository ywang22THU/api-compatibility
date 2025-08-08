#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Compatibility Analyzer
Compares different versions of APIs and identifies breaking changes
"""

import json
import sys
import os
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum as PyEnum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parser import APIDefinition, Class, Function, Enum, Macro, Parameter


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
            CompatibilityLevel.CRITICAL: 7, 
            CompatibilityLevel.WARNING: 3,
            CompatibilityLevel.INFO: 1
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
    
    def to_dict(self) -> dict:
        return {
            'change_type': self.change_type.value,
            'level': self.level.value,
            'level_description': self.level.description,
            'severity_score': self.level.severity_score,
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
    risk_level: str
    total_issues: int
    error_count: int
    critical_count: int
    warning_count: int
    info_count: int
    
    def to_dict(self) -> dict:
        return {
            'total_score': self.total_score,
            'max_possible_score': self.max_possible_score,
            'incompatibility_percentage': self.incompatibility_percentage,
            'risk_level': self.risk_level,
            'total_issues': self.total_issues,
            'breakdown': {
                'error': self.error_count,
                'critical': self.critical_count,
                'warning': self.warning_count,
                'info': self.info_count
            }
        }


class CompatibilityChecker:
    """API compatibility checker with severity assessment"""
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
        self._change_type_severity_map = self._initialize_severity_mapping()
    
    def _initialize_severity_mapping(self) -> Dict[ChangeType, CompatibilityLevel]:
        """Map change types to their severity levels"""
        return {
            # Function related - ERROR level (compilation breaking)
            ChangeType.FUNCTION_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_RETURN_TYPE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED: CompatibilityLevel.ERROR,
            
            # Function related - CRITICAL level (behavioral changes)
            ChangeType.FUNCTION_SIGNATURE_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.FUNCTION_MODIFIER_CHANGED: CompatibilityLevel.CRITICAL,
            
            # Function related - WARNING level (parameter additions with no defaults)
            ChangeType.FUNCTION_PARAMETER_ADDED: CompatibilityLevel.WARNING,  # Will be adjusted based on default values
            
            # Function related - INFO level (additions)
            ChangeType.FUNCTION_ADDED: CompatibilityLevel.INFO,
            
            # Class related - ERROR level
            ChangeType.CLASS_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.CLASS_INHERITANCE_CHANGED: CompatibilityLevel.ERROR,
            
            # Class related - CRITICAL level
            ChangeType.CLASS_FINAL_MODIFIER_CHANGED: CompatibilityLevel.CRITICAL,
            
            # Class related - INFO level
            ChangeType.CLASS_ADDED: CompatibilityLevel.INFO,
            
            # Enum related - ERROR level
            ChangeType.ENUM_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.ENUM_MEMBER_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.ENUM_MEMBER_VALUE_CHANGED: CompatibilityLevel.ERROR,
            
            # Enum related - INFO level
            ChangeType.ENUM_ADDED: CompatibilityLevel.INFO,
            ChangeType.ENUM_MEMBER_ADDED: CompatibilityLevel.INFO,
            
            # Macro related - CRITICAL level (can affect compilation/behavior)
            ChangeType.MACRO_REMOVED: CompatibilityLevel.CRITICAL,
            ChangeType.MACRO_VALUE_CHANGED: CompatibilityLevel.CRITICAL,
            
            # Macro related - INFO level
            ChangeType.MACRO_ADDED: CompatibilityLevel.INFO,
        }
    
    def _get_severity_level(self, change_type: ChangeType, context: dict = None) -> CompatibilityLevel:
        """Get severity level for a change type with context consideration"""
        base_level = self._change_type_severity_map.get(change_type, CompatibilityLevel.WARNING)
        
        # Special handling for function parameter additions
        if change_type == ChangeType.FUNCTION_PARAMETER_ADDED and context:
            has_defaults = context.get('has_default_values', False)
            if has_defaults:
                return CompatibilityLevel.INFO  # Backward compatible
            else:
                return CompatibilityLevel.ERROR  # Breaking change
        
        return base_level
    
    def check_compatibility(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check compatibility between two API versions"""
        self.issues = []
        
        # Check class compatibility
        self._check_classes_compatibility(old_api.classes, new_api.classes)
        
        # Check function compatibility
        self._check_functions_compatibility(old_api.functions, new_api.functions)
        
        # Check enum compatibility
        self._check_enums_compatibility(old_api.enums, new_api.enums)
        
        # Check macro compatibility
        self._check_macros_compatibility(old_api.macros, new_api.macros)
        
        return self.issues
    
    def _check_classes_compatibility(self, old_classes: Dict[str, Class], new_classes: Dict[str, Class]):
        """Check class compatibility"""
        old_names = set(old_classes.keys())
        new_names = set(new_classes.keys())
        
        # Check removed classes
        for removed_class in old_names - new_names:
            level = self._get_severity_level(ChangeType.CLASS_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.CLASS_REMOVED,
                level=level,
                description=f"Class '{removed_class}' has been removed",
                element_name=removed_class,
                element_type="class"
            ))
        
        # Check added classes
        for added_class in new_names - old_names:
            level = self._get_severity_level(ChangeType.CLASS_ADDED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.CLASS_ADDED,
                level=level,
                description=f"Class '{added_class}' has been added",
                element_name=added_class,
                element_type="class"
            ))
        
        # Check common classes
        for class_name in old_names & new_names:
            old_class = old_classes[class_name]
            new_class = new_classes[class_name]
            self._check_single_class_compatibility(old_class, new_class)
    
    def _check_single_class_compatibility(self, old_class: Class, new_class: Class):
        """Check single class compatibility"""
        class_name = old_class.name
        
        # Check inheritance changes
        if set(old_class.base_classes) != set(new_class.base_classes):
            level = self._get_severity_level(ChangeType.CLASS_INHERITANCE_CHANGED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.CLASS_INHERITANCE_CHANGED,
                level=level,
                old_signature=f"Inheritance: {', '.join(old_class.base_classes)}",
                new_signature=f"Inheritance: {', '.join(new_class.base_classes)}",
                description=f"Class '{class_name}' inheritance has changed",
                element_name=class_name,
                element_type="class"
            ))
        
        # Check final modifier changes
        if old_class.is_final != new_class.is_final:
            level = self._get_severity_level(ChangeType.CLASS_FINAL_MODIFIER_CHANGED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.CLASS_FINAL_MODIFIER_CHANGED,
                level=level,
                old_signature=f"final: {old_class.is_final}",
                new_signature=f"final: {new_class.is_final}",
                description=f"Class '{class_name}' final modifier has changed",
                element_name=class_name,
                element_type="class"
            ))
        
        # Check method compatibility
        old_methods = {m.name: m for m in old_class.methods}
        new_methods = {m.name: m for m in new_class.methods}
        
        self._check_methods_compatibility(old_methods, new_methods, class_name)
    
    def _check_methods_compatibility(self, old_methods: Dict[str, Function], 
                                   new_methods: Dict[str, Function], class_name: str = ""):
        """Check method compatibility"""
        old_names = set(old_methods.keys())
        new_names = set(new_methods.keys())
        
        # Check removed methods
        for removed_method in old_names - new_names:
            method = old_methods[removed_method]
            if method.access_level == "public":  # Only care about public interfaces
                level = self._get_severity_level(ChangeType.FUNCTION_REMOVED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    level=level,
                    old_signature=method.signature(),
                    description=f"Method '{removed_method}' has been removed",
                    element_name=f"{class_name}::{removed_method}" if class_name else removed_method,
                    element_type="method"
                ))
        
        # Check added methods
        for added_method in new_names - old_names:
            method = new_methods[added_method]
            if method.access_level == "public":
                level = self._get_severity_level(ChangeType.FUNCTION_ADDED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_ADDED,
                    level=level,
                    new_signature=method.signature(),
                    description=f"Method '{added_method}' has been added",
                    element_name=f"{class_name}::{added_method}" if class_name else added_method,
                    element_type="method"
                ))
        
        # Check common methods
        for method_name in old_names & new_names:
            old_method = old_methods[method_name]
            new_method = new_methods[method_name]
            if old_method.access_level == "public":  # Only care about public interfaces
                self._check_single_method_compatibility(old_method, new_method, class_name)
    
    def _check_single_method_compatibility(self, old_method: Function, new_method: Function, class_name: str = ""):
        """Check single method compatibility"""
        method_name = old_method.name
        full_name = f"{class_name}::{method_name}" if class_name else method_name
        
        # Check return type
        if old_method.return_type != new_method.return_type:
            level = self._get_severity_level(ChangeType.FUNCTION_RETURN_TYPE_CHANGED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_RETURN_TYPE_CHANGED,
                level=level,
                old_signature=old_method.signature(),
                new_signature=new_method.signature(),
                description=f"Method '{method_name}' return type changed from '{old_method.return_type}' to '{new_method.return_type}'",
                element_name=full_name,
                element_type="method"
            ))
        
        # Check parameter compatibility
        self._check_parameters_compatibility(old_method, new_method, full_name)
        
        # Check modifier changes
        self._check_method_modifiers(old_method, new_method, full_name)
    
    def _check_parameters_compatibility(self, old_method: Function, new_method: Function, full_name: str):
        """Check parameter compatibility"""
        old_params = old_method.parameters
        new_params = new_method.parameters
        
        # Check parameter count changes
        if len(old_params) > len(new_params):
            level = self._get_severity_level(ChangeType.FUNCTION_PARAMETER_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_REMOVED,
                level=level,
                old_signature=old_method.signature(),
                new_signature=new_method.signature(),
                description=f"Method '{old_method.name}' has fewer parameters",
                element_name=full_name,
                element_type="method"
            ))
        elif len(old_params) < len(new_params):
            # Check if new parameters have default values
            new_required_params = [p for p in new_params[len(old_params):] if p.default_value is None]
            has_defaults = len(new_required_params) == 0
            
            level = self._get_severity_level(ChangeType.FUNCTION_PARAMETER_ADDED, 
                                           {'has_default_values': has_defaults})
            
            if new_required_params:
                description = f"Method '{old_method.name}' added required parameters"
            else:
                description = f"Method '{old_method.name}' added parameters with default values"
                
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_ADDED,
                level=level,
                old_signature=old_method.signature(),
                new_signature=new_method.signature(),
                description=description,
                element_name=full_name,
                element_type="method"
            ))
        
        # Check corresponding parameter types
        min_len = min(len(old_params), len(new_params))
        for i in range(min_len):
            old_param = old_params[i]
            new_param = new_params[i]
            
            if old_param.type != new_param.type:
                level = self._get_severity_level(ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED,
                    level=level,
                    old_signature=str(old_param),
                    new_signature=str(new_param),
                    description=f"Method '{old_method.name}' parameter '{old_param.name}' type changed from '{old_param.type}' to '{new_param.type}'",
                    element_name=full_name,
                    element_type="method"
                ))
    
    def _check_method_modifiers(self, old_method: Function, new_method: Function, full_name: str):
        """Check method modifier changes"""
        modifiers_to_check = [
            ('is_virtual', 'virtual'),
            ('is_static', 'static'),
            ('is_const', 'const'),
            ('is_noexcept', 'noexcept'),
            ('is_final', 'final')
        ]
        
        for attr, modifier_name in modifiers_to_check:
            old_value = getattr(old_method, attr)
            new_value = getattr(new_method, attr)
            
            if old_value != new_value:
                level = self._get_severity_level(ChangeType.FUNCTION_MODIFIER_CHANGED)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_MODIFIER_CHANGED,
                    level=level,
                    old_signature=old_method.signature(),
                    new_signature=new_method.signature(),
                    description=f"Method '{old_method.name}' {modifier_name} modifier changed",
                    element_name=full_name,
                    element_type="method"
                ))
    
    def _check_functions_compatibility(self, old_functions: Dict[str, Function], 
                                     new_functions: Dict[str, Function]):
        """Check global function compatibility"""
        self._check_methods_compatibility(old_functions, new_functions)
    
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


def load_api_from_json(json_path: str) -> APIDefinition:
    """Load API definition from JSON file"""
    def dict_to_obj(d, cls):
        if isinstance(d, dict):
            obj = cls.__new__(cls)
            for key, value in d.items():
                if hasattr(cls, '__dataclass_fields__') and key in cls.__dataclass_fields__:
                    field_type = cls.__dataclass_fields__[key].type
                    if hasattr(field_type, '__origin__'):  # Generic types like List, Dict
                        if field_type.__origin__ is list:
                            item_type = field_type.__args__[0]
                            setattr(obj, key, [dict_to_obj(item, item_type) for item in value])
                        elif field_type.__origin__ is dict:
                            value_type = field_type.__args__[1]
                            setattr(obj, key, {k: dict_to_obj(v, value_type) for k, v in value.items()})
                        else:
                            setattr(obj, key, value)
                    else:
                        setattr(obj, key, value)
                else:
                    setattr(obj, key, value)
            return obj
        else:
            return d
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return dict_to_obj(data, APIDefinition)


def format_text_report(issues: List[CompatibilityIssue], summary: Dict[str, int], 
                      incompatibility_score: IncompatibilityScore = None) -> str:
    """Format compatibility report as text"""
    report = []
    report.append("API Compatibility Analysis Report")
    report.append("=" * 40)
    report.append("")
    
    # Overall incompatibility assessment
    if incompatibility_score:
        report.append("INCOMPATIBILITY ASSESSMENT:")
        report.append("-" * 30)
        report.append(f"  Risk Level: {incompatibility_score.risk_level}")
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


def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(
        description="API Compatibility Analyzer - Compare two API versions and generate compatibility report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Basic usage with JSON output
        python api_compatibility_analyzer.py api_v1.json api_v2.json -o report.json
        
        # Text format output
        python api_compatibility_analyzer.py api_v1.json api_v2.json --format text -o report.txt
        
        # Output to stdout
        python api_compatibility_analyzer.py api_v1.json api_v2.json --format text
                """
    )
    
    parser.add_argument(
        'old_api',
        help='Path to the old API JSON file'
    )
    
    parser.add_argument(
        'new_api', 
        help='Path to the new API JSON file'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    for api_file in [args.old_api, args.new_api]:
        if not os.path.exists(api_file):
            print(f"Error: API file does not exist: {api_file}")
            sys.exit(1)
    
    try:
        # Load API definitions
        print(f"Loading old API from: {args.old_api}")
        old_api = load_api_from_json(args.old_api)
        
        print(f"Loading new API from: {args.new_api}")
        new_api = load_api_from_json(args.new_api)
        
        # Perform compatibility check
        print("Performing compatibility analysis...")
        checker = CompatibilityChecker()
        issues = checker.check_compatibility(old_api, new_api)
        summary = checker.generate_summary()
        incompatibility_score = checker.calculate_incompatibility_score()
        
        print(f"Analysis complete. Found {summary['total_issues']} issues.")
        print(f"Risk Level: {incompatibility_score.risk_level}")
        print(f"Incompatibility: {incompatibility_score.incompatibility_percentage:.1f}%")
        
        # Generate report
        if args.format == 'json':
            report_data = {
                'incompatibility_assessment': incompatibility_score.to_dict(),
                'summary': summary,
                'issues': [issue.to_dict() for issue in issues]
            }
            output_content = json.dumps(report_data, indent=2, ensure_ascii=False)
        else:  # text format
            output_content = format_text_report(issues, summary, incompatibility_score)
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"Report saved to: {args.output}")
        else:
            print("\n" + output_content)
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python api_compatibility_analyzer.py <old_api.json> <new_api.json> [--output <output_file>] [--format <json|text>]")
        sys.exit(1)
    main()
