"""
JSON serialization utilities for API definitions
"""

import json
from typing import Any, Dict
from ..models import APIDefinition


class JSONSerializer:
    """Handles JSON serialization of API definitions"""
    
    @staticmethod
    def serialize_obj(obj: Any) -> Any:
        """Convert object to JSON serializable format"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, list):
                    result[key] = [JSONSerializer.serialize_obj(item) for item in value]
                elif isinstance(value, dict):
                    result[key] = {k: JSONSerializer.serialize_obj(v) for k, v in value.items()}
                else:
                    result[key] = JSONSerializer.serialize_obj(value)
            return result
        else:
            return obj
    
    @staticmethod
    def to_json(api_def: APIDefinition) -> Dict[str, Any]:
        """Convert API definition to JSON serializable dictionary"""
        return JSONSerializer.serialize_obj(api_def)
    
    @staticmethod
    def save_to_file(api_def: APIDefinition, file_path: str, indent: int = 2) -> None:
        """Save API definition to JSON file"""
        json_data = JSONSerializer.to_json(api_def)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
