"""
Main C++ parser that coordinates all specialized parsers
"""

import os
from typing import List
from .base_parser import BaseParser
from .macro_parser import MacroParser
from .enum_parser import EnumParser
from .class_parser import ClassParser
from ..models import APIDefinition


class CppParser(BaseParser):
    """Main C++ header file parser"""
    
    def __init__(self):
        super().__init__()
        self.macro_parser = MacroParser()
        self.enum_parser = EnumParser()
        self.class_parser = ClassParser()
        self.current_access_level = "private"
        self.namespace_stack = []
    
    def parse_file(self, file_path: str) -> APIDefinition:
        """Parse single header file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Preprocessing: remove comments
        content = self.preprocess_content(content)
        
        api_def = APIDefinition()
        
        # Parse various elements using specialized parsers
        self.macro_parser.parse(content, api_def)
        self.enum_parser.parse(content, api_def)
        self.class_parser.parse(content, api_def)
        self._parse_global_functions(content, api_def)
        
        return api_def
    
    def parse_directory(self, dir_path: str, exclude_dirs: List[str] = None) -> APIDefinition:
        """Parse all header files in directory"""
        if exclude_dirs is None:
            exclude_dirs = ['3rdparty', 'tests', 'icons', 'build', 'cmake', '.git', '__pycache__']
        
        combined_api = APIDefinition()
        
        for root, dirs, files in os.walk(dir_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(('.h', '.hpp', '.hxx')) and not file.endswith('_p.h'):
                    file_path = os.path.join(root, file)
                    try:
                        api_def = self.parse_file(file_path)
                        self._merge_api_definitions(combined_api, api_def)
                    except Exception as e:
                        print(f"Warning: Failed to parse {file_path}: {e}")
        
        return combined_api
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Implementation of abstract method"""
        # This method is not used in the main parser
        pass
    
    def _parse_global_functions(self, content: str, api_def: APIDefinition):
        """Parse global functions (placeholder for future implementation)"""
        # TODO: Implement global function parsing
        pass
    
    def _merge_api_definitions(self, target: APIDefinition, source: APIDefinition):
        """Merge two API definitions"""
        target.classes.update(source.classes)
        target.functions.update(source.functions)
        target.enums.update(source.enums)
        target.macros.update(source.macros)
        target.constants.update(source.constants)
