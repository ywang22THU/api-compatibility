"""
Function parser for methods and functions
"""

import re
from typing import Optional, List
from .base_parser import BaseParser
from ..models import Function, Parameter, APIDefinition
from ..utils import TextProcessor


class FunctionParser(BaseParser):
    """Parser for C++ functions and methods"""
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Implementation of abstract method - placeholder for global functions"""
        # This could be used for parsing global functions in the future
        pass
    
    def parse_method(self, line: str, access_level: str) -> Optional[Function]:
        """Parse method definition from a single line"""
        line = line.strip().rstrip(';')
        
        if not line or line.startswith('//'):
            return None
        
        # Check modifiers
        modifiers = self._extract_modifiers(line)
        
        # Remove modifiers for parsing
        clean_line = self._clean_line_for_parsing(line)
        
        # Match function pattern: return_type function_name(parameter_list)
        pattern = r'(.*?)\s+(\w+)\s*\(([^)]*)\)'
        match = re.match(pattern, clean_line)
        
        if not match:
            return None
        
        return_type = match.group(1).strip()
        function_name = match.group(2)
        params_str = match.group(3)
        
        # Parse parameters
        parameters = self._parse_parameters(params_str)
        
        return Function(
            name=function_name,
            return_type=return_type,
            parameters=parameters,
            access_level=access_level,
            **modifiers
        )
    
    def _extract_modifiers(self, line: str) -> dict:
        """Extract function modifiers from line"""
        return {
            'is_virtual': 'virtual' in line,
            'is_static': 'static' in line,
            'is_const': line.endswith(' const'),
            'is_noexcept': 'noexcept' in line,
            'is_override': 'override' in line,
            'is_final': 'final' in line,
            'is_pure_virtual': line.endswith('= 0')
        }
    
    def _clean_line_for_parsing(self, line: str) -> str:
        """Remove modifiers from line for easier parsing"""
        clean_line = line
        for modifier in ['virtual', 'static', 'override', 'final', 'const', 'noexcept']:
            clean_line = clean_line.replace(modifier, '')
        clean_line = clean_line.replace('= 0', '').strip()
        return clean_line
    
    def _parse_parameters(self, params_str: str) -> List[Parameter]:
        """Parse function parameters from parameter string"""
        parameters = []
        if params_str.strip():
            param_list = TextProcessor.split_parameters(params_str)
            for param in param_list:
                param_obj = self._parse_single_parameter(param)
                if param_obj:
                    parameters.append(param_obj)
        return parameters
    
    def _parse_single_parameter(self, param_str: str) -> Optional[Parameter]:
        """Parse a single function parameter"""
        param_str = param_str.strip()
        
        # Match parameter pattern: type name [= default_value]
        pattern = r'(.*?)\s+(\w+)(?:\s*=\s*(.+))?$'
        match = re.match(pattern, param_str)
        
        if match:
            param_type = match.group(1).strip()
            param_name = match.group(2)
            default_value = match.group(3).strip() if match.group(3) else None
            
            return Parameter(name=param_name, type=param_type, default_value=default_value)
        
        return None
