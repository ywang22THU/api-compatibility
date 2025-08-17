"""
Class parser for C++ class definitions
"""

import re
from .base_parser import BaseParser
from .function_parser import FunctionParser
from ..models import APIDefinition, Class


class ClassParser(BaseParser):
    """Parser for C++ class definitions"""
    
    def __init__(self):
        super().__init__()
        self.function_parser = FunctionParser()
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Parse class definitions from content"""
        # First remove forward declarations to avoid parsing them
        content = self._remove_forward_declarations(content)
        
        # Match class definition with optional Q_XXX_EXPORT macro
        # Pattern: class Q_XXX_EXPORT ClassName : inheritance { body }
        pattern = r'class\s+(Q_\w+_EXPORT\s+)?(final\s+)?(\w+)(?:\s*:\s*([^{]+))?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            export_macro = match.group(1)
            is_final = match.group(2) is not None
            name = match.group(3)
            inheritance = match.group(4)
            body = match.group(5)
            
            # Skip classes without Q_XXX_EXPORT macro (not public API)
            if not export_macro:
                continue
            
            # Skip private classes (those with 'private' in name)
            if self._is_private_class(name):
                print("skip private class : {}".format(name))
                continue
            
            class_obj = Class(name=name, is_final=is_final)
            
            # Store the export macro information
            class_obj.export_macro = export_macro.strip()
            
            # Parse inheritance relationships
            if inheritance:
                class_obj.base_classes = self._parse_inheritance(inheritance)
            
            # Parse class body
            self._parse_class_body(body, class_obj)
            
            api_def.classes[name] = class_obj
    
    def _parse_inheritance(self, inheritance: str) -> list[str]:
        """Parse class inheritance relationships"""
        base_classes = []
        for base in inheritance.split(','):
            base = base.strip()
            # Remove access modifiers
            base = re.sub(r'^(public|protected|private)\s+', '', base)
            if base:
                base_classes.append(base)
        return base_classes
    
    def _remove_forward_declarations(self, content: str) -> str:
        """Remove forward class declarations to avoid parsing them"""
        # Pattern to match forward declarations like:
        # class ClassName;
        # struct StructName;
        # Also handle QT_FORWARD_DECLARE_CLASS and similar macros
        forward_patterns = [
            r'^\s*class\s+\w+\s*;\s*$',                    # class Name;
            r'^\s*struct\s+\w+\s*;\s*$',                   # struct Name;
            r'^\s*QT_FORWARD_DECLARE_CLASS\s*\(\s*\w+\s*\)\s*;\s*$',  # QT_FORWARD_DECLARE_CLASS(Name);
            r'^\s*Q_DECLARE_METATYPE\s*\(\s*[^)]+\s*\)\s*;\s*$',      # Q_DECLARE_METATYPE declarations
        ]
        
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            is_forward_declaration = False
            
            for pattern in forward_patterns:
                if re.match(pattern, line, re.MULTILINE):
                    is_forward_declaration = True
                    break
            
            if not is_forward_declaration:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _is_private_class(self, class_name: str) -> bool:
        """Check if a class should be considered private and excluded"""
        private_indicators = [
            'private',     # Contains 'private' directly
            'Private',     # Contains 'Private' (Qt style)
            'Internal',    # Internal classes
            'Detail',      # Detail namespace classes
            'Impl',        # Implementation classes
            '_p',          # Private suffix pattern
            '_impl',       # Implementation suffix
            'Details',     # Details namespace
        ]
        
        class_name_lower = class_name.lower()
        
        # Check if class name contains any private indicators
        for indicator in private_indicators:
            if indicator.lower() in class_name_lower:
                return True
        
        # Check for specific naming patterns
        if (class_name.endswith('Private') or 
            class_name.endswith('Impl') or 
            class_name.endswith('Internal') or
            class_name.startswith('Q') and 'Private' in class_name or
            '_' in class_name and ('private' in class_name_lower or 'impl' in class_name_lower)):
            return True
        
        return False
    
    def _parse_class_body(self, body: str, class_obj: Class) -> None:
        """Parse class body content"""
        current_access = "private"  # Class default is private
        
        lines = body.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check access modifiers
            if line in ['public:', 'protected:', 'private:']:
                current_access = line[:-1]
                i += 1
                continue
            
            # Handle Qt macros
            if self._handle_qt_macros(line, class_obj, current_access):
                i += 1
                continue
            
            # Parse methods
            method = self.function_parser.parse_method(line, current_access)
            if method:
                class_obj.methods.append(method)
            
            i += 1
    
    def _handle_qt_macros(self, line: str, class_obj: Class, current_access: str) -> bool:
        """
        Handle Qt macros and expand them into appropriate class members
        Returns True if the line was handled as a Qt macro
        """
        # Handle Q_DISABLE_COPY macro
        # Q_DISABLE_COPY(ClassName) -> private copy constructor and assignment operator
        disable_copy_match = re.match(r'Q_DISABLE_COPY\s*\(\s*(\w+)\s*\)', line)
        if disable_copy_match:
            class_name = disable_copy_match.group(1)
            self._add_disabled_copy_members(class_obj, class_name)
            return True
        
        # Handle Q_PROPERTY macro
        # Q_PROPERTY(Type name READ getter WRITE setter NOTIFY signal)
        property_match = re.match(r'Q_PROPERTY\s*\(\s*([^)]+)\s*\)', line)
        if property_match:
            property_content = property_match.group(1)
            self._parse_q_property(class_obj, property_content, current_access)
            return True
        
        return False
    
    def _add_disabled_copy_members(self, class_obj: Class, class_name: str) -> None:
        """Add disabled copy constructor and assignment operator"""
        from ..models import Function, Parameter
        
        # Add private copy constructor: ClassName(const ClassName&)
        copy_constructor = Function(
            name=class_name,
            return_type="",  # Constructors have no return type
            parameters=[
                Parameter(
                    name="other",
                    type=f"const {class_name}&",
                    default_value=""
                )
            ],
            access_level="private",
            is_constructor=True,
            is_deleted=True,  # C++11 style, but we'll mark as private to indicate disabled
            is_virtual=False,
            is_static=False,
            is_const=False,
            is_noexcept=False,
            is_override=False,
            is_final=False,
            is_pure_virtual=False,
            is_inline=False,
            is_extern=False
        )
        class_obj.methods.append(copy_constructor)
        
        # Add private assignment operator: ClassName& operator=(const ClassName&)
        assignment_operator = Function(
            name="operator=",
            return_type=f"{class_name}&",
            parameters=[
                Parameter(
                    name="other",
                    type=f"const {class_name}&",
                    default_value=""
                )
            ],
            access_level="private",
            is_deleted=True,  # Mark as disabled
            is_virtual=False,
            is_static=False,
            is_const=False,
            is_noexcept=False,
            is_override=False,
            is_final=False,
            is_pure_virtual=False,
            is_inline=False,
            is_extern=False
        )
        class_obj.methods.append(assignment_operator)
    
    def _parse_q_property(self, class_obj: Class, property_content: str, current_access: str) -> None:
        """
        Parse Q_PROPERTY macro and generate getter/setter methods
        Format: Type name READ getter WRITE setter NOTIFY signal
        """
        from ..models import Function, Parameter, Member
        
        # Parse the property content
        parts = property_content.split()
        if len(parts) < 2:
            return
        
        property_type = parts[0]
        property_name = parts[1]
        
        # Parse READ, WRITE, NOTIFY keywords
        getter_name = None
        setter_name = None
        notify_signal = None
        
        i = 2
        while i < len(parts):
            if parts[i] == "READ" and i + 1 < len(parts):
                getter_name = parts[i + 1]
                i += 2
            elif parts[i] == "WRITE" and i + 1 < len(parts):
                setter_name = parts[i + 1]
                i += 2
            elif parts[i] == "NOTIFY" and i + 1 < len(parts):
                notify_signal = parts[i + 1]
                i += 2
            else:
                i += 1
        
        # Add property as a member variable
        property_member = Member(
            name=f"m_{property_name}",  # Follow Qt convention
            type=property_type,
            access_level="private",  # Properties are usually backed by private members
            is_static=False,
            is_const=False
        )
        class_obj.members.append(property_member)
        
        # Add getter method if specified
        if getter_name:
            getter = Function(
                name=getter_name,
                return_type=property_type,
                parameters=[],
                access_level="public",  # Property getters are usually public
                is_const=True,  # Getters are usually const
                is_virtual=False,
                is_static=False,
                is_noexcept=False,
                is_override=False,
                is_final=False,
                is_pure_virtual=False,
                is_inline=True,  # Property getters are usually inline
                is_extern=False
            )
            class_obj.methods.append(getter)
        
        # Add setter method if specified
        if setter_name:
            setter = Function(
                name=setter_name,
                return_type="void",
                parameters=[
                    Parameter(
                        name="value",
                        type=f"const {property_type}&" if not self._is_primitive_type(property_type) else property_type,
                        default_value=""
                    )
                ],
                access_level="public",  # Property setters are usually public
                is_const=False,
                is_virtual=False,
                is_static=False,
                is_noexcept=False,
                is_override=False,
                is_final=False,
                is_pure_virtual=False,
                is_inline=True,  # Property setters are usually inline
                is_extern=False
            )
            class_obj.methods.append(setter)
        
        # Add notify signal if specified (signals are like methods but special)
        if notify_signal:
            signal = Function(
                name=notify_signal,
                return_type="void",
                parameters=[],
                access_level="signals",  # Qt-specific access level
                is_const=False,
                is_virtual=False,
                is_static=False,
                is_noexcept=False,
                is_override=False,
                is_final=False,
                is_pure_virtual=False,
                is_inline=False,
                is_extern=False
            )
            class_obj.methods.append(signal)
    
    def _is_primitive_type(self, type_name: str) -> bool:
        """Check if a type is a primitive type that doesn't need const reference"""
        primitive_types = {
            'bool', 'char', 'signed char', 'unsigned char',
            'short', 'unsigned short', 'int', 'unsigned int',
            'long', 'unsigned long', 'long long', 'unsigned long long',
            'float', 'double', 'long double',
            'wchar_t', 'char16_t', 'char32_t'
        }
        return type_name in primitive_types
