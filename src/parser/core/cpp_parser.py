"""
Main C++ parser that coordinates all specialized parsers
"""

import os
import re
import logging
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from .base_parser import BaseParser
from .macro_parser import MacroParser
from .enum_parser import EnumParser
from .class_parser import ClassParser
from .function_parser import FunctionParser
from ..models import APIDefinition


def _parse_single_file(file_path: str) -> APIDefinition:
    """
    Parse a single file - standalone function for multiprocessing
    This function needs to be at module level for pickling
    """
    logger = logging.getLogger(__name__)
    try:
        parser = CppParser()
        return parser.parse_file(file_path)
    except Exception as e:
        logger.warning(f"Failed to parse {file_path}: {e}")
        return APIDefinition()


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
        
        return api_def
    
    def parse_directory(self, dir_path: str, exclude_dirs: List[str] = None, 
                       path_patterns: Optional[List[str]] = None, max_workers: int = None) -> APIDefinition:
        """
        Parse all header files in directory with optional parallel processing
        
        Args:
            dir_path: Directory path to parse
            exclude_dirs: List of directory names to exclude (ignored if path_patterns is used)
            path_patterns: List of regex patterns to match directory paths (e.g., ['qt/*/src'])
            max_workers: Maximum number of worker processes (default: CPU count)
        """
        if exclude_dirs is None:
            exclude_dirs = ['3rdparty', 'third_party', 'thirdparty', 'icons', 'tests', 'test', 
                           'examples', 'example', 'docs', 'doc', 'build', 'cmake-build-debug', 
                           'cmake-build-release', '.git', '.vscode', '__pycache__']
        
        # Collect all header files
        header_files = self._find_files_by_patterns(dir_path, path_patterns, exclude_dirs)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Found {len(header_files)} header files to parse")
        
        if max_workers <= 1 or len(header_files) < 2:
            # Sequential processing for small number of files or when parallel is disabled
            return self._parse_files_sequential(header_files)
        else:
            # Parallel processing
            return self._parse_files_parallel(header_files, max_workers)
    
    def _find_files_by_exclusion(self, dir_path: str, exclude_dirs: List[str]) -> List[str]:
        """Find header files using directory exclusion (original method)"""
        header_files = []
        for root, dirs, files in os.walk(dir_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(('.h', '.hpp', '.hxx')) and not file.endswith('_p.h'):
                    file_path = os.path.join(root, file)
                    header_files.append(file_path)
        return header_files

    def _find_files_by_patterns(self, dir_path: str, path_patterns: List[str], exclude_dirs: List[str]) -> List[str]:
        """Find header files using regex path patterns"""
        header_files = []
        logger = logging.getLogger(__name__)
        
        # Convert glob-like patterns to regex patterns
        regex_patterns = []
        for pattern in path_patterns:
            # Convert common glob patterns to regex
            # Replace * with [^/\\]* (match any character except path separator)
            # Replace ** with .* (match any character including path separator)
            regex_pattern = pattern.replace('**', '___DOUBLE_STAR___')
            regex_pattern = regex_pattern.replace('*', '[^/\\\\]*')
            regex_pattern = regex_pattern.replace('___DOUBLE_STAR___', '.*')
            
            regex_patterns.append(re.compile(regex_pattern, re.IGNORECASE))
            logger.debug(f"Converted pattern '{pattern}' to regex: {regex_pattern}")
        
        # Walk through all directories and match patterns
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Get relative path from dir_path
            rel_path = os.path.relpath(root, dir_path)
            if rel_path == '.':
                rel_path = ''
            
            # Normalize path separators for matching
            normalized_path = rel_path.replace('\\', '/')
            
            # Check if this directory matches any pattern
            matches_pattern = False
            for regex_pattern in regex_patterns:
                if regex_pattern.search(normalized_path) or regex_pattern.search(rel_path):
                    matches_pattern = True
                    logger.debug(f"Path '{normalized_path}' matches pattern")
                    break
            
            if matches_pattern:
                # Add header files from this directory
                for file in files:
                    if file.endswith(('.h', '.hpp', '.hxx')) and not file.endswith('_p.h'):
                        file_path = os.path.join(root, file)
                        header_files.append(file_path)
                        logger.debug(f"Added file: {file_path}")
        
        return header_files
    
    def _parse_files_sequential(self, file_paths: List[str]) -> APIDefinition:
        """Parse files sequentially"""
        logger = logging.getLogger(__name__)
        combined_api = APIDefinition()
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                logger.debug(f"Parsing [{i}/{len(file_paths)}]: {os.path.basename(file_path)}")
                api_def = self.parse_file(file_path)
                self._merge_api_definitions(combined_api, api_def)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                raise e
        
        return combined_api
    
    def _parse_files_parallel(self, file_paths: List[str], max_workers: int = 0) -> APIDefinition:
        """Parse files in parallel using ProcessPoolExecutor"""
        logger = logging.getLogger(__name__)
        
        if max_workers == 0:
            max_workers = min(cpu_count(), len(file_paths))
        
        logger.debug(f"Using {max_workers} worker processes for parallel parsing")
        
        combined_api = APIDefinition()
        completed_count = 0
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(_parse_single_file, file_path): file_path 
                    for file_path in file_paths
                }
                
                # Process completed tasks as they finish
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    completed_count += 1
                    
                    try:
                        api_def = future.result()
                        self._merge_api_definitions(combined_api, api_def)
                        logger.debug(f"Completed [{completed_count}/{len(file_paths)}]: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
        
        except KeyboardInterrupt:
            logger.info("Parsing interrupted by user")
        except Exception as e:
            logger.error(f"Error in parallel parsing: {e}")
            logger.info("Falling back to sequential parsing...")
            return self._parse_files_sequential(file_paths)
        
        return combined_api
    
    def parse(self, content: str, api_def: APIDefinition) -> None:
        """Implementation of abstract method"""
        # This method is not used in the main parser
        pass
    
    def _merge_api_definitions(self, target: APIDefinition, source: APIDefinition):
        """Merge two API definitions"""
        target.classes.update(source.classes)
        target.enums.update(source.enums)
        target.macros.update(source.macros)
        target.constants.update(source.constants)
