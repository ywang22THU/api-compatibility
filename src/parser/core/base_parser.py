"""
Base parser class with common functionality
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import APIDefinition
from ..utils import TextProcessor


class BaseParser(ABC):
    """Base class for all specialized parsers"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    @abstractmethod
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Parse content and update API definition"""
        pass
    
    def preprocess_content(self, content: str) -> str:
        """Common preprocessing steps"""
        # Remove comments first
        content = self.text_processor.remove_comments(content)
        # Remove preprocessor directives except #define
        content = self.text_processor.remove_preprocessor_directives(content)
        return content
