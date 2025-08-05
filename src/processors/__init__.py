"""
Processor Registry

This module provides a central registry for all processors in the system.
It handles auto-discovery and instantiation of processors.
"""

import importlib
from typing import Dict, Optional, List
from pathlib import Path

from src.core.base_processor import BaseProcessor


# Central processor registry
_PROCESSOR_REGISTRY: Dict[str, BaseProcessor] = {}


def register_processor(processor: BaseProcessor):
    """Register a processor in the global registry."""
    _PROCESSOR_REGISTRY[processor.metadata.name] = processor


def get_processor(name: str) -> Optional[BaseProcessor]:
    """Get a processor by name from the registry."""
    return _PROCESSOR_REGISTRY.get(name)


def list_processors() -> List[str]:
    """Get a list of all registered processor names."""
    return list(_PROCESSOR_REGISTRY.keys())


def get_all_processors() -> Dict[str, BaseProcessor]:
    """Get all registered processors."""
    return _PROCESSOR_REGISTRY.copy()


def auto_register_processors():
    """Automatically discover and register all processors."""
    # Clear existing registry
    _PROCESSOR_REGISTRY.clear()
    
    # Register processors from each category
    _register_category_processors("lookup")
    _register_category_processors("filtering") 
    _register_category_processors("data_collection")
    _register_category_processors("analysis")


def _register_category_processors(category: str):
    """Register processors from a specific category."""
    category_path = Path(__file__).parent / category
    
    if not category_path.exists():
        return
    
    # Find all Python files in the category
    for py_file in category_path.glob("*.py"):
        if py_file.name.startswith("__") or py_file.name.startswith("test_"):
            continue
            
        module_name = py_file.stem
        try:
            # Import the module
            module = importlib.import_module(f"src.processors.{category}.{module_name}")
            
            # Look for get_processor function
            if hasattr(module, "get_processor"):
                processor = module.get_processor()
                if processor and isinstance(processor, BaseProcessor):
                    register_processor(processor)
                    print(f"Registered processor: {processor.metadata.name}")
        
        except Exception as e:
            print(f"Failed to register processor from {category}/{module_name}: {e}")


# Auto-register processors on import
auto_register_processors()