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
        """Parse global functions from content"""
        # Preprocess content to remove comments and preprocessor directives
        content = self.preprocess_content(content)
        
        # Find all global functions
        global_functions = self._find_global_functions(content)
        
        # Add to API definition
        for func in global_functions:
            api_def.functions[func.name] = func
    
    def _find_global_functions(self, content: str) -> List[Function]:
        """Find all global function declarations/definitions in content"""
        functions = []
        
        # Remove class definitions to avoid parsing member functions as global functions
        content_without_classes = self._remove_class_definitions(content)
        
        # Split content into lines for processing
        lines = content_without_classes.split('\n')
        
        # Parse line by line, handling multi-line function declarations
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines, comments, and preprocessor directives
            if not line or line.startswith('//') or line.startswith('#'):
                i += 1
                continue
            
            # Skip common non-function patterns
            if self._should_skip_line(line):
                i += 1
                continue
            
            # Only try to parse if line looks like it could be a function
            if self._could_be_function_line(line):
                # Check if this might be a function declaration/definition
                function_text, lines_consumed = self._extract_function_text(lines, i)
                
                if function_text:
                    func = self._parse_global_function(function_text)
                    if func:
                        functions.append(func)
                
                i += lines_consumed if lines_consumed > 0 else 1
            else:
                i += 1
        
        return functions
    
    def _remove_class_definitions(self, content: str) -> str:
        """Remove class definitions to avoid parsing member functions"""
        result = []
        lines = content.split('\n')
        brace_count = 0
        in_class = False
        in_namespace = False
        namespace_brace_count = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Handle namespace blocks
            if re.match(r'^\s*namespace\s+\w+\s*\{', line_stripped):
                in_namespace = True
                namespace_brace_count = line_stripped.count('{') - line_stripped.count('}')
                result.append(line)
                continue
            
            if in_namespace:
                namespace_brace_count += line_stripped.count('{') - line_stripped.count('}')
                if namespace_brace_count <= 0:
                    in_namespace = False
                    result.append(line)
                    continue
            
            # Check for class declaration with optional Q_XXX_EXPORT macro
            # Patterns: class Name {, class final Name {, class Q_XXX_EXPORT Name {, class Q_XXX_EXPORT final Name {
            class_patterns = [
                r'^\s*class\s+(Q_\w+_EXPORT\s+)?(final\s+)?\w+.*\{',  # class with optional export and final
                r'^\s*struct\s+(Q_\w+_EXPORT\s+)?\w+.*\{',           # struct with optional export
                r'^\s*class\s+(Q_\w+_EXPORT\s+)?(final\s+)?\w+\s*:.*\{',  # class with inheritance
                r'^\s*struct\s+(Q_\w+_EXPORT\s+)?\w+\s*:.*\{',       # struct with inheritance
            ]
            
            is_class_start = False
            for pattern in class_patterns:
                if re.match(pattern, line_stripped):
                    is_class_start = True
                    break
            
            if is_class_start:
                in_class = True
                brace_count = line_stripped.count('{') - line_stripped.count('}')
                continue
            
            if in_class:
                brace_count += line_stripped.count('{') - line_stripped.count('}')
                if brace_count <= 0:
                    in_class = False
                continue
            
            # Only add line if not inside a class
            if not in_class:
                result.append(line)
        
        return '\n'.join(result)
    
    def _should_skip_line(self, line: str) -> bool:
        """Check if line should be skipped (not a function)"""
        skip_patterns = [
            r'^\s*typedef\s+',           # typedef statements
            r'^\s*using\s+',             # using statements  
            r'^\s*namespace\s+',         # namespace declarations
            r'^\s*extern\s+"C"\s*\{',    # extern "C" blocks
            r'^\s*template\s*<',         # template declarations (for now)
            r'^\s*enum\s+',              # enum declarations
            r'^\s*struct\s+\w+\s*;',     # forward struct declarations
            r'^\s*class\s+\w+\s*;',      # forward class declarations
            r'^\s*\}',                   # closing braces
            r'^\s*\{',                   # opening braces
            r'^\s*#',                    # preprocessor directives
            r'^\s*//',                   # comment lines
            r'^\s*/\*',                  # comment block starts
            r'^\s*\*/',                  # comment block ends
            r'^\s*\*',                   # comment block middle
            r'^\s*;',                    # empty statements
            r'^\s*$',                    # empty lines
            r'^\s*Q_DECLARE_',           # Qt declare macros
            r'^\s*Q_OBJECT\s*$',         # Q_OBJECT macro
            r'^\s*Q_GADGET\s*$',         # Q_GADGET macro
            r'^\s*Q_INTERFACE\s*\(',     # Q_INTERFACE macro
            r'^\s*public\s*:',           # access specifiers
            r'^\s*private\s*:',          # access specifiers
            r'^\s*protected\s*:',        # access specifiers
            r'^\s*signals\s*:',          # Qt signals
            r'^\s*slots\s*:',            # Qt slots
            r'^\s*Q_SIGNALS\s*:',        # Qt Q_SIGNALS
            r'^\s*Q_SLOTS\s*:',          # Qt Q_SLOTS
        ]
        
        # Check if line contains only operators or special characters
        if re.match(r'^\s*[{}();,=\[\]<>!&|+\-*/%^~?:]*\s*$', line):
            return True
        
        # Check if line is a variable declaration (contains = but not function-like)
        if '=' in line and '(' not in line and not re.search(r'\w+\s*\([^)]*\)', line):
            return True
        
        for pattern in skip_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _could_be_function_line(self, line: str) -> bool:
        """Check if line could potentially be the start of a function"""
        # Must contain parentheses to be a function
        if '(' not in line:
            return False
        
        # Skip obvious non-functions
        if any(keyword in line for keyword in ['if', 'while', 'for', 'switch', 'catch', 'sizeof']):
            return False
        
        # Skip macro calls (usually uppercase)
        if re.match(r'^\s*[A-Z_][A-Z0-9_]*\s*\(', line):
            return False
        
        # Skip Qt-specific macros
        qt_macros = ['Q_OBJECT', 'Q_GADGET', 'Q_DECLARE_', 'Q_PROPERTY', 'Q_CLASSINFO', 
                    'Q_INTERFACES', 'Q_ENUMS', 'Q_FLAGS', 'Q_EMIT', 'Q_FOREVER']
        if any(macro in line for macro in qt_macros):
            return False
        
        # Skip constructor calls or casts
        if re.match(r'^\s*\w+\s*\(.*\)\s*[;,]?\s*$', line) and not re.search(r'\w+\s+\w+\s*\(', line):
            return False
        
        # Basic function pattern: should have return_type function_name(params)
        # Look for pattern: word(s) followed by word followed by (
        if re.search(r'\w+\s+\w+\s*\(', line):
            return True
        
        # Could be continuation of previous line
        return True
    
    
    def _extract_function_text(self, lines: List[str], start_idx: int) -> tuple[str, int]:
        """Extract complete function declaration/definition text"""
        function_lines = []
        i = start_idx
        paren_count = 0
        found_opening_paren = False
        
        while i < len(lines):
            line = lines[i].strip()
            function_lines.append(line)
            
            # Count parentheses to find complete function signature
            paren_count += line.count('(') - line.count(')')
            
            if '(' in line:
                found_opening_paren = True
            
            # If we have a complete function signature
            if found_opening_paren and paren_count == 0:
                # Check if this ends with semicolon (declaration) or opening brace (definition)
                if line.endswith(';') or line.endswith('{'):
                    break
                # If next line starts with '{', include it
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
                    i += 1
                    function_lines.append(lines[i].strip())
                    break
            
            i += 1
            
            # Safety check: don't go too far for a single function
            if i - start_idx > 10:
                break
        
        if found_opening_paren and paren_count == 0:
            return ' '.join(function_lines), i - start_idx + 1
        
        return "", 0
    
    def _parse_global_function(self, function_text: str) -> Optional[Function]:
        """Parse a global function from its text"""
        # Clean up the function text
        function_text = function_text.strip().rstrip(';').rstrip('{')
        
        # Skip if this doesn't look like a function
        if not function_text or '(' not in function_text:
            return None
        
        # Additional validation - skip obvious non-functions
        if self._is_definitely_not_function(function_text):
            return None
        
        # Extract modifiers
        modifiers = self._extract_global_function_modifiers(function_text)
        
        # Clean line for parsing
        clean_text = self._clean_global_function_text(function_text)
        
        # Match function pattern: return_type function_name(parameter_list)
        # Handle multiple spaces and newlines
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # More flexible pattern to handle various function formats
        pattern = r'^(.*?)\s+(\w+)\s*\(([^)]*)\)(?:\s*(const|noexcept|override|final|.*?))*$'
        match = re.match(pattern, clean_text)
        
        if not match:
            return None
        
        return_type = match.group(1).strip()
        function_name = match.group(2)
        params_str = match.group(3)
        
        # Skip if return type is empty or looks like a keyword
        if not return_type or return_type in ['class', 'struct', 'enum', 'namespace']:
            return None
        
        # Skip constructors/destructors (they shouldn't be global)
        if function_name.startswith('~') or return_type == function_name:
            return None
        
        # Additional validation for function name
        if not self._is_valid_function_name(function_name):
            return None
        
        # Parse parameters
        parameters = self._parse_parameters(params_str)
        
        return Function(
            name=function_name,
            return_type=return_type,
            parameters=parameters,
            access_level="public",  # Global functions are always public
            **modifiers
        )
    
    def _is_definitely_not_function(self, text: str) -> bool:
        """Check if text is definitely not a function"""
        # Convert to single line for easier checking
        line = re.sub(r'\s+', ' ', text).strip()
        
        # Skip variable declarations with initialization
        if re.match(r'^.*\w+\s*=\s*.*$', line) and not re.search(r'\w+\s*\([^)]*\)\s*=', line):
            return True
        
        # Skip array declarations
        if re.search(r'\[\s*\]', line):
            return True
        
        # Skip pointer declarations without function signature
        if '*' in line and not re.search(r'\w+\s*\([^)]*\)', line):
            return True
        
        # Skip obvious control flow statements
        control_keywords = ['if', 'while', 'for', 'switch', 'do', 'catch', 'try']
        if any(f'\\b{keyword}\\b' for keyword in control_keywords if re.search(f'\\b{keyword}\\b', line)):
            return True
        
        return False
    
    def _is_valid_function_name(self, name: str) -> bool:
        """Check if name is a valid function name"""
        # Must be valid C++ identifier
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            return False
        
        # Skip C++ keywords
        cpp_keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof',
            'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void',
            'volatile', 'while', 'class', 'public', 'private', 'protected',
            'virtual', 'inline', 'friend', 'new', 'delete', 'this', 'operator'
        ]
        
        if name in cpp_keywords:
            return False
        
        return True
    
    def _extract_global_function_modifiers(self, function_text: str) -> dict:
        """Extract function modifiers for global functions"""
        return {
            'is_virtual': False,  # Global functions can't be virtual
            'is_static': 'static' in function_text,
            'is_const': False,    # Global functions can't be const
            'is_noexcept': 'noexcept' in function_text,
            'is_override': False, # Global functions can't override
            'is_final': False,    # Global functions can't be final
            'is_pure_virtual': False,  # Global functions can't be pure virtual
            'is_inline': 'inline' in function_text,
            'is_extern': 'extern' in function_text,
            'is_constexpr': 'constexpr' in function_text
        }
    
    def _clean_global_function_text(self, function_text: str) -> str:
        """Clean function text for parsing"""
        clean_text = function_text
        
        # Remove common modifiers
        modifiers_to_remove = ['static', 'inline', 'extern', 'noexcept', 'constexpr']
        for modifier in modifiers_to_remove:
            clean_text = re.sub(r'\b' + modifier + r'\b', '', clean_text)
        
        # Remove C++ attributes
        clean_text = re.sub(r'\[\[.*?\]\]', '', clean_text)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def parse_method(self, line: str, access_level: str) -> Optional[Function]:
        """Parse method definition from a single line, removing Qt/C++ macros and attributes"""
        line = line.strip().rstrip(';')
        if not line or line.startswith('//'):
            return None
        # Check modifiers
        modifiers = self._extract_modifiers(line)
        # Remove modifiers, Qt macros, and attributes for parsing
        clean_line = line
        # Remove standard modifiers (including constexpr)
        modifiers_to_remove = ['virtual', 'static', 'override', 'final', 'const', 'noexcept', 'inline', 'extern', 'constexpr']
        for modifier in modifiers_to_remove:
            clean_line = re.sub(r'\b' + modifier + r'\b', '', clean_line)
        
        # Remove C++ attributes like [[nodiscard]], [[deprecated]], etc.
        clean_line = re.sub(r'\[\[.*?\]\]', '', clean_line)
        
        # Remove Qt macros and deprecated markers
        qt_macros = [
            'Q_DECL_EXPORT', 'Q_DECL_DEPRECATED', 'Q_DECL_CONSTEXPR', 'Q_DECL_NOEXCEPT',
            'Q_DECL_OVERRIDE', 'Q_DECL_FINAL', 'Q_DECL_INLINE', 'Q_DECL_NOTHROW',
            'QT_DEPRECATED', 'Q_REQUIRED_RESULT', 'Q_MAYBE_UNUSED', 'Q_NODISCARD'
        ]
        for macro in qt_macros:
            clean_line = re.sub(r'\b' + macro + r'\b', '', clean_line)
        
        # Clean up extra whitespace
        clean_line = re.sub(r'\s+', ' ', clean_line).strip()
        clean_line = clean_line.replace('= 0', '').strip()
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
        """Extract function modifiers from line, including deprecated marker"""
        return {
            'is_virtual': 'virtual' in line,
            'is_static': 'static' in line,
            'is_const': line.endswith(' const'),
            'is_noexcept': 'noexcept' in line,
            'is_override': 'override' in line,
            'is_final': 'final' in line,
            'is_pure_virtual': line.endswith('= 0'),
            'is_inline': 'inline' in line,
            'is_extern': 'extern' in line,
            'is_constexpr': 'constexpr' in line,
            'is_deprecated': 'QT_DEPRECATED' in line or 'Q_DECL_DEPRECATED' in line
        }
    
    def _clean_line_for_parsing(self, line: str) -> str:
        """Remove modifiers from line for easier parsing"""
        clean_line = line
        modifiers_to_remove = ['virtual', 'static', 'override', 'final', 'const', 'noexcept', 'inline', 'extern', 'constexpr']
        for modifier in modifiers_to_remove:
            clean_line = re.sub(r'\b' + modifier + r'\b', '', clean_line)
        
        # Remove C++ attributes
        clean_line = re.sub(r'\[\[.*?\]\]', '', clean_line)
        
        # Clean up and remove pure virtual marker
        clean_line = re.sub(r'\s+', ' ', clean_line).strip()
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
        
        # Handle special case of void parameter
        if param_str == 'void':
            return None
        
        # Match parameter pattern: type name [= default_value]
        # Also handle cases where parameter name might be missing
        pattern = r'^(.*?)\s+(\w+)(?:\s*=\s*(.+))?$'
        match = re.match(pattern, param_str)
        
        if match:
            param_type = match.group(1).strip()
            param_name = match.group(2)
            default_value = match.group(3).strip() if match.group(3) else None
            
            return Parameter(name=param_name, type=param_type, default_value=default_value)
        else:
            # Handle case where only type is provided (no parameter name)
            # This is common in function declarations
            param_type = param_str.strip()
            if param_type and param_type != 'void':
                return Parameter(name="", type=param_type, default_value=None)
        
        return None
