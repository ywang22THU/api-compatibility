"""
Text processing utilities for C++ code parsing
"""

import re
from typing import List


class TextProcessor:
    """Utilities for processing C++ source text"""
    
    @staticmethod
    def remove_comments(content: str) -> str:
        """Remove C++ comments from source code"""
        # Remove single line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content
    
    @staticmethod
    def remove_preprocessor_directives(content: str) -> str:
        """Remove preprocessor directives except #define macros"""
        # Remove #include directives
        content = re.sub(r'^\s*#include\s+[<"][^>"]*[>"].*?$', '', content, flags=re.MULTILINE)
        
        # Remove #pragma directives
        content = re.sub(r'^\s*#pragma\s+.*?$', '', content, flags=re.MULTILINE)
        
        # Remove conditional compilation directives but keep the content
        # This removes #if, #ifdef, #ifndef, #else, #elif, #endif
        content = re.sub(r'^\s*#(?:if|ifdef|ifndef|else|elif|endif)(?:\s+.*?)?$', '', content, flags=re.MULTILINE)
        
        # Remove other preprocessor directives (except #define)
        content = re.sub(r'^\s*#(?!define)[a-zA-Z_][a-zA-Z0-9_]*.*?$', '', content, flags=re.MULTILINE)
        
        return content
    
    @staticmethod
    def extract_balanced_braces(content: str, start_pos: int) -> tuple[str, int]:
        """
        Extract content within balanced braces starting from position
        Returns (extracted_content, end_position)
        """
        brace_count = 0
        start_brace_found = False
        start_extract = start_pos
        
        for i in range(start_pos, len(content)):
            if content[i] == '{':
                if not start_brace_found:
                    start_extract = i + 1
                    start_brace_found = True
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0 and start_brace_found:
                    return content[start_extract:i], i
        
        return "", len(content)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text"""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def split_parameters(params_str: str) -> List[str]:
        """Split parameter string respecting nested templates"""
        if not params_str.strip():
            return []
        
        params = []
        current_param = ""
        paren_count = 0
        angle_count = 0
        
        for char in params_str:
            if char == ',' and paren_count == 0 and angle_count == 0:
                if current_param.strip():
                    params.append(current_param.strip())
                current_param = ""
            else:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == '<':
                    angle_count += 1
                elif char == '>':
                    angle_count -= 1
                current_param += char
        
        if current_param.strip():
            params.append(current_param.strip())
        
        return params
