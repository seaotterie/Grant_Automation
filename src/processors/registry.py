"""
Processor Registry
Automatically discovers and registers all available processors.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import importlib.util
import inspect

from src.core.base_processor import BaseProcessor
from src.core.workflow_engine import get_workflow_engine


class ProcessorAutoRegistry:
    """
    Automatically discovers and registers processors from the processors directory.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registered_processors: List[str] = []
    
    def discover_and_register_all(self) -> int:
        """
        Discover all processor modules and register them.
        
        Returns:
            Number of processors registered
        """
        processors_dir = Path(__file__).parent
        registered_count = 0
        
        # Walk through all Python files in the processors directory
        for processor_file in processors_dir.rglob("*.py"):
            if processor_file.name in ["__init__.py", "registry.py"]:
                continue
            
            try:
                registered_count += self._register_processor_from_file(processor_file)
            except Exception as e:
                self.logger.error(f"Failed to register processor from {processor_file}: {e}")
        
        self.logger.info(f"Registered {registered_count} processors")
        return registered_count
    
    def _register_processor_from_file(self, processor_file: Path) -> int:
        """
        Register processor from a specific file.
        
        Args:
            processor_file: Path to processor Python file
            
        Returns:
            Number of processors registered from this file
        """
        # Create module name from file path
        relative_path = processor_file.relative_to(Path(__file__).parent.parent)
        module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, processor_file)
            if not spec or not spec.loader:
                return 0
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            registered_count = 0
            
            # Look for BaseProcessor subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != BaseProcessor and 
                    issubclass(obj, BaseProcessor) and 
                    obj.__module__ == module_name):
                    
                    try:
                        # Register the processor
                        engine = get_workflow_engine()
                        engine.register_processor(obj)
                        
                        processor_name = obj().metadata.name
                        self.registered_processors.append(processor_name)
                        registered_count += 1
                        
                        self.logger.info(f"Registered processor: {processor_name} from {processor_file.name}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to register processor {name}: {e}")
            
            # Also try to call register_processor function if it exists
            if hasattr(module, 'register_processor'):
                try:
                    module.register_processor()
                    self.logger.debug(f"Called register_processor() from {processor_file.name}")
                except Exception as e:
                    self.logger.warning(f"register_processor() failed in {processor_file.name}: {e}")
            
            return registered_count
            
        except Exception as e:
            self.logger.error(f"Failed to import processor module {processor_file}: {e}")
            return 0
    
    def get_registered_processors(self) -> List[str]:
        """Get list of registered processor names."""
        return self.registered_processors.copy()


# Global registry instance
_auto_registry: ProcessorAutoRegistry = None


def get_auto_registry() -> ProcessorAutoRegistry:
    """Get the global auto registry instance."""
    global _auto_registry
    if _auto_registry is None:
        _auto_registry = ProcessorAutoRegistry()
    return _auto_registry


def register_all_processors() -> int:
    """
    Discover and register all processors.
    
    Returns:
        Number of processors registered
    """
    registry = get_auto_registry()
    return registry.discover_and_register_all()


def get_processor_summary() -> Dict[str, Any]:
    """
    Get a summary of all registered processors.
    
    Returns:
        Dictionary with processor information
    """
    engine = get_workflow_engine()
    processor_names = engine.registry.list_processors()
    
    processors_info = []
    for name in processor_names:
        info = engine.registry.get_processor_info(name)
        if info:
            processors_info.append(info)
    
    # Group by type
    by_type = {}
    for info in processors_info:
        proc_type = info.get('processor_type', 'unknown')
        if proc_type not in by_type:
            by_type[proc_type] = []
        by_type[proc_type].append(info)
    
    return {
        'total_processors': len(processors_info),
        'by_type': by_type,
        'processor_names': processor_names,
        'processors_info': processors_info
    }