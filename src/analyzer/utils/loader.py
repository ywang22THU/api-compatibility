"""
API data loader utilities
"""

import json
import sys
from pathlib import Path

# Add parent parser module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from parser import APIDefinition


def load_api_from_json(json_path: str) -> APIDefinition:
    """Load API definition from JSON file"""
    def dict_to_obj(d, cls):
        if isinstance(d, dict):
            obj = cls.__new__(cls)
            for key, value in d.items():
                if hasattr(cls, '__dataclass_fields__') and key in cls.__dataclass_fields__:
                    field_type = cls.__dataclass_fields__[key].type
                    if hasattr(field_type, '__origin__'):  # Generic types like List, Dict
                        if field_type.__origin__ is list:
                            item_type = field_type.__args__[0]
                            setattr(obj, key, [dict_to_obj(item, item_type) for item in value])
                        elif field_type.__origin__ is dict:
                            value_type = field_type.__args__[1]
                            setattr(obj, key, {k: dict_to_obj(v, value_type) for k, v in value.items()})
                        else:
                            setattr(obj, key, value)
                    else:
                        setattr(obj, key, value)
                else:
                    setattr(obj, key, value)
            return obj
        else:
            return d
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return dict_to_obj(data, APIDefinition)
