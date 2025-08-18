"""
Class compatibility checker
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition, Class, Function

from .base_checker import BaseChecker
from ..models.compatibility_models import CompatibilityIssue, ChangeType, CompatibilityLevel


class ClassChecker(BaseChecker):
    """Checker for class compatibility"""
    
    def __init__(self):
        super().__init__()
        self._change_type_severity_map = self._initialize_severity_mapping()
    
    def _initialize_severity_mapping(self) -> Dict[ChangeType, CompatibilityLevel]:
        """Map change types to their severity levels for classes"""
        return {
            ChangeType.CLASS_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.CLASS_INHERITANCE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.CLASS_FINAL_MODIFIER_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.CLASS_ADDED: CompatibilityLevel.INFO,
            ChangeType.FUNCTION_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_ADDED: CompatibilityLevel.INFO,
            ChangeType.FUNCTION_RETURN_TYPE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_ADDED: CompatibilityLevel.WARNING,
            ChangeType.FUNCTION_SIGNATURE_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.FUNCTION_MODIFIER_CHANGED: CompatibilityLevel.CRITICAL,
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
    
    def _calculate_adjusted_severity_score(self, change_type: ChangeType, old_method: Function = None, context: dict = None) -> float:
        """Calculate severity score with deprecated function adjustment"""
        level = self._get_severity_level(change_type, context)
        base_score = level.severity_score
        
        # Apply 0.5 multiplier for deprecated functions
        if old_method and getattr(old_method, 'is_deprecated', False):
            return base_score * 0.5
        
        return base_score
    
    def check(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check class compatibility"""
        self.issues = []
        self._check_classes_compatibility(old_api.classes, new_api.classes)
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
                score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_REMOVED, method)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_REMOVED,
                    level=level,
                    severity_score=score,
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
            score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_RETURN_TYPE_CHANGED, old_method)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_RETURN_TYPE_CHANGED,
                level=level,
                severity_score=score,
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
            score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_PARAMETER_REMOVED, old_method)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_REMOVED,
                level=level,
                severity_score=score,
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
            score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_PARAMETER_ADDED, old_method,
                                                           {'has_default_values': has_defaults})
            
            if new_required_params:
                description = f"Method '{old_method.name}' added required parameters"
            else:
                description = f"Method '{old_method.name}' added parameters with default values"
                
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_ADDED,
                level=level,
                severity_score=score,
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
                score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED, old_method)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED,
                    level=level,
                    severity_score=score,
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
                score = self._calculate_adjusted_severity_score(ChangeType.FUNCTION_MODIFIER_CHANGED, old_method)
                self.issues.append(CompatibilityIssue(
                    change_type=ChangeType.FUNCTION_MODIFIER_CHANGED,
                    level=level,
                    severity_score=score,
                    old_signature=old_method.signature(),
                    new_signature=new_method.signature(),
                    description=f"Method '{old_method.name}' {modifier_name} modifier changed",
                    element_name=full_name,
                    element_type="method"
                ))
