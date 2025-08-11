"""
Function compatibility checker
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition, Function

from .base_checker import BaseChecker
from ..models.compatibility_models import CompatibilityIssue, ChangeType, CompatibilityLevel


class FunctionChecker(BaseChecker):
    """Checker for global function compatibility"""
    
    def __init__(self):
        super().__init__()
        self._change_type_severity_map = self._initialize_severity_mapping()
    
    def _initialize_severity_mapping(self) -> Dict[ChangeType, CompatibilityLevel]:
        """Map change types to their severity levels for functions"""
        return {
            ChangeType.FUNCTION_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_RETURN_TYPE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_REMOVED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_PARAMETER_TYPE_CHANGED: CompatibilityLevel.ERROR,
            ChangeType.FUNCTION_SIGNATURE_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.FUNCTION_MODIFIER_CHANGED: CompatibilityLevel.CRITICAL,
            ChangeType.FUNCTION_PARAMETER_ADDED: CompatibilityLevel.WARNING,
            ChangeType.FUNCTION_ADDED: CompatibilityLevel.INFO,
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
    
    def check(self, old_api: APIDefinition, new_api: APIDefinition) -> List[CompatibilityIssue]:
        """Check global function compatibility"""
        self.issues = []
        self._check_functions_compatibility(old_api.functions, new_api.functions)
        return self.issues
    
    def _check_functions_compatibility(self, old_functions: Dict[str, Function], 
                                     new_functions: Dict[str, Function]):
        """Check global function compatibility"""
        old_names = set(old_functions.keys())
        new_names = set(new_functions.keys())
        
        # Check removed functions
        for removed_function in old_names - new_names:
            function = old_functions[removed_function]
            level = self._get_severity_level(ChangeType.FUNCTION_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_REMOVED,
                level=level,
                old_signature=function.signature(),
                description=f"Function '{removed_function}' has been removed",
                element_name=removed_function,
                element_type="function"
            ))
        
        # Check added functions
        for added_function in new_names - old_names:
            function = new_functions[added_function]
            level = self._get_severity_level(ChangeType.FUNCTION_ADDED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_ADDED,
                level=level,
                new_signature=function.signature(),
                description=f"Function '{added_function}' has been added",
                element_name=added_function,
                element_type="function"
            ))
        
        # Check common functions
        for function_name in old_names & new_names:
            old_function = old_functions[function_name]
            new_function = new_functions[function_name]
            self._check_single_function_compatibility(old_function, new_function)
    
    def _check_single_function_compatibility(self, old_function: Function, new_function: Function):
        """Check single function compatibility"""
        function_name = old_function.name
        
        # Check return type
        if old_function.return_type != new_function.return_type:
            level = self._get_severity_level(ChangeType.FUNCTION_RETURN_TYPE_CHANGED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_RETURN_TYPE_CHANGED,
                level=level,
                old_signature=old_function.signature(),
                new_signature=new_function.signature(),
                description=f"Function '{function_name}' return type changed from '{old_function.return_type}' to '{new_function.return_type}'",
                element_name=function_name,
                element_type="function"
            ))
        
        # Check parameter compatibility
        self._check_parameters_compatibility(old_function, new_function)
        
        # Check modifier changes
        self._check_function_modifiers(old_function, new_function)
    
    def _check_parameters_compatibility(self, old_function: Function, new_function: Function):
        """Check parameter compatibility"""
        old_params = old_function.parameters
        new_params = new_function.parameters
        
        # Check parameter count changes
        if len(old_params) > len(new_params):
            level = self._get_severity_level(ChangeType.FUNCTION_PARAMETER_REMOVED)
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_REMOVED,
                level=level,
                old_signature=old_function.signature(),
                new_signature=new_function.signature(),
                description=f"Function '{old_function.name}' has fewer parameters",
                element_name=old_function.name,
                element_type="function"
            ))
        elif len(old_params) < len(new_params):
            # Check if new parameters have default values
            new_required_params = [p for p in new_params[len(old_params):] if p.default_value is None]
            has_defaults = len(new_required_params) == 0
            
            level = self._get_severity_level(ChangeType.FUNCTION_PARAMETER_ADDED, 
                                           {'has_default_values': has_defaults})
            
            if new_required_params:
                description = f"Function '{old_function.name}' added required parameters"
            else:
                description = f"Function '{old_function.name}' added parameters with default values"
                
            self.issues.append(CompatibilityIssue(
                change_type=ChangeType.FUNCTION_PARAMETER_ADDED,
                level=level,
                old_signature=old_function.signature(),
                new_signature=new_function.signature(),
                description=description,
                element_name=old_function.name,
                element_type="function"
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
                    description=f"Function '{old_function.name}' parameter '{old_param.name}' type changed from '{old_param.type}' to '{new_param.type}'",
                    element_name=old_function.name,
                    element_type="function"
                ))
    
    def _check_function_modifiers(self, old_function: Function, new_function: Function):
        """Check function modifier changes"""
        modifiers_to_check = [
            ('is_virtual', 'virtual'),
            ('is_static', 'static'),
            ('is_const', 'const'),
            ('is_noexcept', 'noexcept'),
            ('is_final', 'final')
        ]
        
        for attr, modifier_name in modifiers_to_check:
            if hasattr(old_function, attr) and hasattr(new_function, attr):
                old_value = getattr(old_function, attr)
                new_value = getattr(new_function, attr)
                
                if old_value != new_value:
                    level = self._get_severity_level(ChangeType.FUNCTION_MODIFIER_CHANGED)
                    self.issues.append(CompatibilityIssue(
                        change_type=ChangeType.FUNCTION_MODIFIER_CHANGED,
                        level=level,
                        old_signature=old_function.signature(),
                        new_signature=new_function.signature(),
                        description=f"Function '{old_function.name}' {modifier_name} modifier changed",
                        element_name=old_function.name,
                        element_type="function"
                    ))
