#!/usr/bin/env python3
"""
Isolated Workflow Manager for Multi-Tenant Profile Systems
Ensures complete isolation between organization profiles and their opportunity ecosystems.

This manager:
1. Creates isolated workflow contexts for each organization profile
2. Manages separate data storage and processing pipelines per profile
3. Prevents cross-contamination between different organization ecosystems
4. Maintains profile-specific state and history
5. Enables concurrent processing of multiple organization profiles
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, asdict

from .models import OrganizationProfile, OpportunityLead, ProfileSearchParams, FundingType
from .service import ProfileService
from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.core.workflow_engine import WorkflowEngine


@dataclass
class IsolatedWorkflowContext:
    """Represents an isolated workflow context for a single organization profile."""
    profile_id: str
    profile_name: str
    workflow_id: str
    data_directory: Path
    state_file: Path
    results_directory: Path
    created_at: datetime
    last_accessed: datetime
    is_active: bool = False
    processor_states: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.processor_states is None:
            self.processor_states = {}


class IsolatedWorkflowManager:
    """Manages isolated workflow contexts for multiple organization profiles."""
    
    def __init__(self, base_data_dir: str = "data/isolated_workflows"):
        """Initialize the isolated workflow manager."""
        self.base_data_dir = Path(base_data_dir)
        self.profile_service = ProfileService()
        self.active_contexts: Dict[str, IsolatedWorkflowContext] = {}
        
        # Ensure base directory exists
        self.base_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Context management
        self.context_registry_file = self.base_data_dir / "context_registry.json"
        self._load_context_registry()
    
    def _load_context_registry(self):
        """Load existing workflow contexts from registry."""
        if self.context_registry_file.exists():
            try:
                with open(self.context_registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                for context_data in registry_data.get('contexts', []):
                    context = IsolatedWorkflowContext(
                        profile_id=context_data['profile_id'],
                        profile_name=context_data['profile_name'],
                        workflow_id=context_data['workflow_id'],
                        data_directory=Path(context_data['data_directory']),
                        state_file=Path(context_data['state_file']),
                        results_directory=Path(context_data['results_directory']),
                        created_at=datetime.fromisoformat(context_data['created_at']),
                        last_accessed=datetime.fromisoformat(context_data['last_accessed']),
                        is_active=context_data.get('is_active', False),
                        processor_states=context_data.get('processor_states', {})
                    )
                    self.active_contexts[context.profile_id] = context
                    
            except Exception as e:
                print(f"Warning: Failed to load context registry: {e}")
    
    def _save_context_registry(self):
        """Save workflow contexts to registry."""
        try:
            registry_data = {
                'contexts': [],
                'last_updated': datetime.now().isoformat()
            }
            
            for context in self.active_contexts.values():
                context_data = asdict(context)
                # Convert Path objects to strings
                context_data['data_directory'] = str(context_data['data_directory'])
                context_data['state_file'] = str(context_data['state_file'])
                context_data['results_directory'] = str(context_data['results_directory'])
                # Convert datetime objects to strings
                context_data['created_at'] = context_data['created_at'].isoformat()
                context_data['last_accessed'] = context_data['last_accessed'].isoformat()
                
                registry_data['contexts'].append(context_data)
            
            with open(self.context_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save context registry: {e}")
    
    def create_isolated_context(self, profile_id: str) -> IsolatedWorkflowContext:
        """Create a new isolated workflow context for a profile."""
        # Get profile information
        profile = self.profile_service.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
        
        # Check if context already exists
        if profile_id in self.active_contexts:
            context = self.active_contexts[profile_id]
            context.last_accessed = datetime.now()
            self._save_context_registry()
            return context
        
        # Create new context
        workflow_id = f"workflow_{uuid.uuid4().hex[:12]}"
        profile_dir = self.base_data_dir / f"profile_{profile_id}"
        
        # Create directory structure
        profile_dir.mkdir(exist_ok=True)
        data_dir = profile_dir / "data"
        results_dir = profile_dir / "results"
        data_dir.mkdir(exist_ok=True)
        results_dir.mkdir(exist_ok=True)
        
        # Create context
        context = IsolatedWorkflowContext(
            profile_id=profile_id,
            profile_name=profile.name,
            workflow_id=workflow_id,
            data_directory=data_dir,
            state_file=data_dir / "workflow_state.json",
            results_directory=results_dir,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            is_active=False
        )
        
        # Store context
        self.active_contexts[profile_id] = context
        self._save_context_registry()
        
        return context
    
    def get_context(self, profile_id: str) -> Optional[IsolatedWorkflowContext]:
        """Get existing workflow context for a profile."""
        context = self.active_contexts.get(profile_id)
        if context:
            context.last_accessed = datetime.now()
            self._save_context_registry()
        return context
    
    def list_contexts(self) -> List[IsolatedWorkflowContext]:
        """List all active workflow contexts."""
        return list(self.active_contexts.values())
    
    async def run_isolated_workflow(self, profile_id: str, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete workflow in isolation for a specific profile."""
        # Get or create context
        context = self.create_isolated_context(profile_id)
        
        try:
            context.is_active = True
            self._save_context_registry()
            
            # Get profile
            profile = self.profile_service.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile not found: {profile_id}")
            
            # Create isolated workflow configuration
            isolated_config = self._create_isolated_workflow_config(profile, context, workflow_config)
            
            # Initialize isolated workflow engine
            workflow_engine = WorkflowEngine()
            
            # Set up isolated data paths
            original_cache_dir = getattr(workflow_engine, 'cache_dir', None)
            workflow_engine.cache_dir = context.data_directory / "cache"
            workflow_engine.cache_dir.mkdir(exist_ok=True)
            
            # Execute workflow with profile isolation
            workflow_result = await self._execute_isolated_workflow(
                workflow_engine, isolated_config, context
            )
            
            # Save results to isolated directory
            results_file = context.results_directory / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(workflow_result, f, indent=2, default=str)
            
            # Update context state
            context.processor_states = workflow_result.get('processor_states', {})
            context.last_accessed = datetime.now()
            
            return workflow_result
            
        finally:
            context.is_active = False
            self._save_context_registry()
    
    def _create_isolated_workflow_config(self, profile: OrganizationProfile, 
                                       context: IsolatedWorkflowContext, 
                                       workflow_config: Dict[str, Any]) -> WorkflowConfig:
        """Create isolated workflow configuration for a profile."""
        
        # Extract search parameters from profile
        search_params = {
            'target_ein': profile.ein,
            'focus_areas': profile.focus_areas,
            'geographic_scope': profile.geographic_scope.dict() if profile.geographic_scope else {},
            'funding_preferences': profile.funding_preferences.dict() if profile.funding_preferences else {},
            'organization_type': profile.organization_type.value,
            'annual_revenue': profile.annual_revenue,
        }
        
        # Create isolated workflow config
        isolated_config = WorkflowConfig(
            workflow_id=context.workflow_id,
            profile_id=profile.profile_id,
            organization_name=profile.name,
            search_params=search_params,
            isolated_data_dir=str(context.data_directory),
            isolated_results_dir=str(context.results_directory),
            **workflow_config
        )
        
        return isolated_config
    
    async def _execute_isolated_workflow(self, workflow_engine: WorkflowEngine, 
                                       config: WorkflowConfig, 
                                       context: IsolatedWorkflowContext) -> Dict[str, Any]:
        """Execute workflow with complete profile isolation."""
        
        # Define isolated processor sequence for Schedule I lead generation
        processor_sequence = [
            'xml_downloader',           # Download and parse 990 XML filings
            'schedule_i_processor',     # Extract Schedule I grant recipients
            'ein_cross_reference',      # Cross-reference recipients with EIN data
            'enhanced_network_analyzer' # Analyze board + funding relationships
        ]
        
        workflow_results = {
            'workflow_id': context.workflow_id,
            'profile_id': context.profile_id,
            'profile_name': context.profile_name,
            'execution_start': datetime.now().isoformat(),
            'processor_results': {},
            'processor_states': {},
            'isolated_data_path': str(context.data_directory),
            'isolated_results_path': str(context.results_directory)
        }
        
        # Execute processors in sequence with isolation
        workflow_state = WorkflowState()
        
        for processor_name in processor_sequence:
            try:
                print(f"Executing {processor_name} for profile {context.profile_name}...")
                
                # Create isolated processor config
                processor_config = ProcessorConfig(
                    processor_name=processor_name,
                    workflow_config=config,
                    isolated_context=context
                )
                
                # Execute processor
                result = await self._execute_isolated_processor(
                    processor_name, processor_config, workflow_state, context
                )
                
                # Store results in isolated context
                workflow_results['processor_results'][processor_name] = result
                workflow_results['processor_states'][processor_name] = {
                    'completed': result.get('success', False),
                    'execution_time': result.get('execution_time', 0),
                    'organization_count': len(result.get('data', {}).get('organizations', [])),
                    'errors': result.get('errors', []),
                    'warnings': result.get('warnings', [])
                }
                
                # Update workflow state
                if result.get('success'):
                    workflow_state.mark_processor_complete(processor_name, result.get('data', {}))
                else:
                    print(f"Processor {processor_name} failed: {result.get('errors', [])}")
                
            except Exception as e:
                error_msg = f"Failed to execute {processor_name}: {str(e)}"
                print(f"Error: {error_msg}")
                workflow_results['processor_states'][processor_name] = {
                    'completed': False,
                    'error': error_msg
                }
        
        workflow_results['execution_end'] = datetime.now().isoformat()
        workflow_results['total_execution_time'] = (
            datetime.fromisoformat(workflow_results['execution_end']) - 
            datetime.fromisoformat(workflow_results['execution_start'])
        ).total_seconds()
        
        return workflow_results
    
    async def _execute_isolated_processor(self, processor_name: str, config: ProcessorConfig, 
                                        workflow_state, context: IsolatedWorkflowContext) -> Dict[str, Any]:
        """Execute a single processor with complete isolation."""
        
        # This is a simplified execution - in production, would use actual processor imports
        # For now, return simulated results
        
        simulated_results = {
            'xml_downloader': {
                'success': True,
                'execution_time': 30.0,
                'data': {
                    'organizations': [
                        {
                            'ein': config.workflow_config.search_params.get('target_ein', 'test-ein'),
                            'name': context.profile_name,
                            'has_schedule_i': True,
                            'data_sources': ['IRS XML Filings']
                        }
                    ]
                }
            },
            'schedule_i_processor': {
                'success': True,
                'execution_time': 15.0,
                'data': {
                    'organizations': [
                        {
                            'ein': config.workflow_config.search_params.get('target_ein', 'test-ein'),
                            'name': context.profile_name,
                            'external_data': {
                                'schedule_i_analysis': {
                                    'leads_generated': 3,
                                    'funding_patterns': {'total_amount': 75000, 'total_grants': 3}
                                }
                            }
                        }
                    ]
                }
            },
            'ein_cross_reference': {
                'success': True,
                'execution_time': 45.0,
                'data': {
                    'organizations': [
                        {
                            'ein': config.workflow_config.search_params.get('target_ein', 'test-ein'),
                            'name': context.profile_name,
                            'external_data': {
                                'ein_cross_reference': {
                                    'matches_found': 2,
                                    'total_searches': 3,
                                    'match_rate': 0.67
                                }
                            }
                        }
                    ]
                }
            },
            'enhanced_network_analyzer': {
                'success': True,
                'execution_time': 20.0,
                'data': {
                    'organizations': [
                        {
                            'ein': config.workflow_config.search_params.get('target_ein', 'test-ein'),
                            'name': context.profile_name,
                            'network_analysis_complete': True
                        }
                    ],
                    'enhanced_network_analysis': {
                        'board_connections': 2,
                        'funding_relationships': 3,
                        'strategic_insights': {
                            'network_overview': {
                                'organizations_with_both_connections': 1
                            }
                        }
                    }
                }
            }
        }
        
        return simulated_results.get(processor_name, {
            'success': False,
            'errors': [f'Processor {processor_name} not implemented']
        })
    
    def cleanup_context(self, profile_id: str) -> bool:
        """Clean up and remove an isolated workflow context."""
        context = self.active_contexts.get(profile_id)
        if not context:
            return False
        
        try:
            # Remove from active contexts
            del self.active_contexts[profile_id]
            
            # Clean up directory (optional - may want to keep for historical purposes)
            # import shutil
            # shutil.rmtree(context.data_directory.parent, ignore_errors=True)
            
            # Update registry
            self._save_context_registry()
            
            return True
            
        except Exception as e:
            print(f"Failed to cleanup context for {profile_id}: {e}")
            return False
    
    def get_context_summary(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information for a workflow context."""
        context = self.active_contexts.get(profile_id)
        if not context:
            return None
        
        # Count results files
        results_files = list(context.results_directory.glob("*.json")) if context.results_directory.exists() else []
        
        return {
            'profile_id': context.profile_id,
            'profile_name': context.profile_name,
            'workflow_id': context.workflow_id,
            'created_at': context.created_at.isoformat(),
            'last_accessed': context.last_accessed.isoformat(),
            'is_active': context.is_active,
            'results_count': len(results_files),
            'latest_result': max([f.stat().st_mtime for f in results_files]) if results_files else None,
            'data_directory_size': sum(f.stat().st_size for f in context.data_directory.rglob('*') if f.is_file()) if context.data_directory.exists() else 0
        }


class WorkflowState:
    """Simple workflow state tracker for processor coordination."""
    
    def __init__(self):
        self.completed_processors = set()
        self.processor_data = {}
    
    def mark_processor_complete(self, processor_name: str, data: Dict[str, Any]):
        """Mark a processor as completed with its data."""
        self.completed_processors.add(processor_name)
        self.processor_data[processor_name] = data
    
    def has_processor_succeeded(self, processor_name: str) -> bool:
        """Check if a processor has completed successfully."""
        return processor_name in self.completed_processors
    
    def get_organizations_from_processor(self, processor_name: str) -> List[Dict[str, Any]]:
        """Get organization data from a completed processor."""
        if processor_name not in self.processor_data:
            return []
        return self.processor_data[processor_name].get('organizations', [])


# Global instance for easy access
isolated_workflow_manager = IsolatedWorkflowManager()