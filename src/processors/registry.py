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
    Get an enhanced summary of all registered processors with client architecture insights.
    
    Returns:
        Dictionary with processor information including client integration status
    """
    engine = get_workflow_engine()
    processor_names = engine.registry.list_processors()
    
    processors_info = []
    client_integration_count = 0
    version_2_count = 0
    
    for name in processor_names:
        info = engine.registry.get_processor_info(name)
        if info:
            # Enhanced info with client architecture details
            enhanced_info = info.copy()
            
            # Check for new client architecture integration
            if _is_client_integrated_processor(name, info):
                enhanced_info['client_integrated'] = True
                enhanced_info['architecture'] = 'unified_client'
                client_integration_count += 1
            else:
                enhanced_info['client_integrated'] = False
                enhanced_info['architecture'] = 'legacy'
            
            # Check version for architecture upgrades
            version = info.get('version', '1.0.0')
            if version.startswith('2.'):
                version_2_count += 1
                enhanced_info['architecture_version'] = '2.0'
            else:
                enhanced_info['architecture_version'] = '1.0'
            
            processors_info.append(enhanced_info)
    
    # Group by type
    by_type = {}
    for info in processors_info:
        proc_type = info.get('processor_type', 'unknown')
        if proc_type not in by_type:
            by_type[proc_type] = []
        by_type[proc_type].append(info)
    
    # Enhanced architecture insights
    architecture_stats = {
        'total_processors': len(processors_info),
        'client_integrated': client_integration_count,
        'legacy_architecture': len(processors_info) - client_integration_count,
        'version_2_processors': version_2_count,
        'migration_completion': (client_integration_count / len(processors_info) * 100) if processors_info else 0
    }
    
    return {
        'total_processors': len(processors_info),
        'by_type': by_type,
        'processor_names': processor_names,
        'processors_info': processors_info,
        'architecture_stats': architecture_stats,
        'migration_insights': _get_migration_insights(processors_info)
    }


def _is_client_integrated_processor(name: str, info: Dict[str, Any]) -> bool:
    """
    Check if a processor uses the new unified client architecture.
    
    Args:
        name: Processor name
        info: Processor info dictionary
        
    Returns:
        True if processor uses unified client architecture
    """
    # Check for known migrated processors
    migrated_processors = {
        'grants_gov_fetch',
        'propublica_fetch', 
        'usaspending_fetch',
        'foundation_directory_fetch',
        'va_state_grants_fetch'
    }
    
    if name in migrated_processors:
        return True
    
    # Check version indicator
    version = info.get('version', '1.0.0')
    if version.startswith('2.'):
        return True
    
    # Check if processor type is data_collection with recent updates
    proc_type = info.get('processor_type', '')
    if proc_type == 'data_collection' and version != '1.0.0':
        return True
    
    return False


def _get_migration_insights(processors_info: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate insights about the processor architecture migration.
    
    Args:
        processors_info: List of processor information dictionaries
        
    Returns:
        Dictionary with migration insights
    """
    data_collection_processors = [
        p for p in processors_info 
        if p.get('processor_type') == 'data_collection'
    ]
    
    migrated_data_collection = [
        p for p in data_collection_processors 
        if p.get('client_integrated', False)
    ]
    
    return {
        'data_collection_total': len(data_collection_processors),
        'data_collection_migrated': len(migrated_data_collection),
        'data_collection_migration_rate': (
            len(migrated_data_collection) / len(data_collection_processors) * 100 
            if data_collection_processors else 0
        ),
        'priority_processors_status': {
            'grants_gov_fetch': _get_processor_migration_status('grants_gov_fetch', processors_info),
            'propublica_fetch': _get_processor_migration_status('propublica_fetch', processors_info),
            'usaspending_fetch': _get_processor_migration_status('usaspending_fetch', processors_info),
            'foundation_directory_fetch': _get_processor_migration_status('foundation_directory_fetch', processors_info),
            'va_state_grants_fetch': _get_processor_migration_status('va_state_grants_fetch', processors_info)
        },
        'architecture_benefits': [
            'Unified HTTP client abstraction',
            'Consistent error handling',
            'Automatic rate limiting',
            'Enhanced caching capabilities',
            'Simplified testing interfaces'
        ]
    }


def _get_processor_migration_status(processor_name: str, processors_info: List[Dict[str, Any]]) -> Dict[str, str]:
    """Get migration status for a specific processor."""
    processor_info = next((p for p in processors_info if p.get('name') == processor_name), None)
    
    if not processor_info:
        return {'status': 'not_found', 'version': 'unknown', 'architecture': 'unknown'}
    
    return {
        'status': 'migrated' if processor_info.get('client_integrated', False) else 'pending',
        'version': processor_info.get('version', 'unknown'),
        'architecture': processor_info.get('architecture', 'unknown')
    }


def get_architecture_overview() -> Dict[str, Any]:
    """
    Get comprehensive overview of the processor architecture and client integration status.
    
    Returns:
        Dictionary with detailed architecture insights for dashboard display
    """
    summary = get_processor_summary()
    architecture_stats = summary.get('architecture_stats', {})
    migration_insights = summary.get('migration_insights', {})
    
    # Core statistics
    total_processors = architecture_stats.get('total_processors', 0)
    client_integrated = architecture_stats.get('client_integrated', 0)
    migration_completion = architecture_stats.get('migration_completion', 0)
    
    # Data collection processor focus
    data_collection_stats = {
        'total': migration_insights.get('data_collection_total', 0),
        'migrated': migration_insights.get('data_collection_migrated', 0),
        'migration_rate': migration_insights.get('data_collection_migration_rate', 0)
    }
    
    # Priority processor status
    priority_status = migration_insights.get('priority_processors_status', {})
    
    return {
        'overview': {
            'total_processors': total_processors,
            'client_integrated': client_integrated,
            'legacy_processors': total_processors - client_integrated,
            'migration_completion_percentage': round(migration_completion, 1),
            'architecture_version': '2.0 Unified Client Architecture'
        },
        'data_collection_focus': data_collection_stats,
        'priority_processors': {
            'total_priority': len(priority_status),
            'migrated_priority': sum(
                1 for status in priority_status.values() 
                if status.get('status') == 'migrated'
            ),
            'processor_details': priority_status
        },
        'architecture_benefits': migration_insights.get('architecture_benefits', []),
        'migration_phase': _determine_migration_phase(migration_completion),
        'next_steps': _get_next_migration_steps(migration_completion, data_collection_stats),
        'technical_improvements': {
            'http_client_consolidation': 'Unified HTTP client across all processors',
            'error_handling': 'Consistent error patterns and recovery',
            'rate_limiting': 'Centralized rate limiting and connection pooling',
            'caching': 'Intelligent response caching for performance',
            'testing': 'Simplified mocking and integration testing'
        }
    }


def _determine_migration_phase(completion_percentage: float) -> Dict[str, str]:
    """Determine current migration phase based on completion percentage."""
    if completion_percentage >= 90:
        return {
            'phase': 'Phase 3: Optimization & Enhancement',
            'status': 'near_complete',
            'description': 'Migration nearly complete, focusing on optimization'
        }
    elif completion_percentage >= 60:
        return {
            'phase': 'Phase 2B: Registry Integration',
            'status': 'advanced_progress',
            'description': 'Core processors migrated, enhancing registry integration'
        }
    elif completion_percentage >= 30:
        return {
            'phase': 'Phase 2A: Core Processor Migration',
            'status': 'good_progress',
            'description': 'Migrating core data collection processors'
        }
    else:
        return {
            'phase': 'Phase 1: Architecture Foundation',
            'status': 'early_stage',
            'description': 'Establishing unified client architecture'
        }


def _get_next_migration_steps(completion_percentage: float, data_collection_stats: Dict[str, Any]) -> List[str]:
    """Get recommended next steps based on migration progress."""
    if completion_percentage >= 90:
        return [
            'Performance optimization and monitoring',
            'Advanced caching strategies',
            'Load balancing enhancements',
            'Documentation and training updates'
        ]
    elif completion_percentage >= 60:
        return [
            'Complete remaining processor migrations',
            'Enhance integration testing suite',
            'Implement advanced error recovery',
            'Optimize resource allocation'
        ]
    elif data_collection_stats.get('migration_rate', 0) >= 80:
        return [
            'Migrate analysis and visualization processors',
            'Enhance discovery engine unification',
            'Implement comprehensive integration tests',
            'Update documentation and examples'
        ]
    else:
        return [
            'Complete core data collection processor migrations',
            'Establish consistent error handling patterns',
            'Implement unified rate limiting',
            'Create migration testing framework'
        ]