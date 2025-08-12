#!/usr/bin/env python3
"""
Unified Processing State Management System
Tracks completion status and prevents redundant expensive operations across profiles
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Processing status values"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    SKIPPED = "skipped"


class ProcessingStep(str, Enum):
    """Processing step identifiers"""
    # Discovery steps
    PROPUBLICA_DISCOVERY = "propublica_discovery"
    XML_DOWNLOAD = "xml_download"
    SCHEDULE_I_EXTRACTION = "schedule_i_extraction"
    
    # Analysis steps  
    FINANCIAL_SCORING = "financial_scoring"
    NETWORK_ANALYSIS = "network_analysis"
    BOARD_CONNECTION_ANALYSIS = "board_connection_analysis"
    
    # AI-powered steps (expensive)
    AI_CLASSIFICATION = "ai_classification"
    AI_OPPORTUNITY_MATCHING = "ai_opportunity_matching"
    AI_COMPETITIVE_ANALYSIS = "ai_competitive_analysis"
    AI_RISK_ASSESSMENT = "ai_risk_assessment"
    
    # Government steps
    GRANTS_GOV_FETCH = "grants_gov_fetch"
    USASPENDING_FETCH = "usaspending_fetch"
    STATE_GRANTS_FETCH = "state_grants_fetch"
    
    # Commercial steps
    FOUNDATION_DIRECTORY_FETCH = "foundation_directory_fetch"
    CSR_ANALYSIS = "csr_analysis"


@dataclass
class StepExecution:
    """Individual step execution record"""
    step: ProcessingStep
    status: ProcessingStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    result_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_completed(self) -> bool:
        """Check if step is successfully completed"""
        return self.status == ProcessingStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status == ProcessingStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if step is in progress"""
        return self.status == ProcessingStatus.IN_PROGRESS
    
    def should_retry(self, max_age: timedelta = timedelta(hours=1)) -> bool:
        """Check if failed step should be retried"""
        if self.status != ProcessingStatus.FAILED:
            return False
        if not self.completed_at:
            return True
        return datetime.now() - self.completed_at > max_age
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepExecution':
        """Create from dictionary"""
        data = data.copy()
        # Convert ISO format back to datetime
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        # Convert string enums back to enum objects
        data['step'] = ProcessingStep(data['step'])
        data['status'] = ProcessingStatus(data['status'])
        
        return cls(**data)


@dataclass  
class OpportunityProcessingState:
    """Processing state for a single opportunity across profiles"""
    opportunity_id: str
    source_type: str  # "nonprofit", "government", "commercial", "state"
    organization_name: str
    ein: Optional[str] = None
    steps: Dict[ProcessingStep, StepExecution] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    profiles_using: Set[str] = field(default_factory=set)
    
    def get_step(self, step: ProcessingStep) -> Optional[StepExecution]:
        """Get step execution record"""
        return self.steps.get(step)
    
    def is_step_completed(self, step: ProcessingStep) -> bool:
        """Check if specific step is completed"""
        step_exec = self.steps.get(step)
        return step_exec is not None and step_exec.is_completed()
    
    def should_run_step(self, step: ProcessingStep, force_refresh: bool = False) -> bool:
        """Determine if step should be run"""
        if force_refresh:
            return True
        
        step_exec = self.steps.get(step)
        if not step_exec:
            return True  # Never run before
        
        if step_exec.is_completed():
            return False  # Already completed
        
        if step_exec.is_in_progress():
            # Check if stuck (older than 1 hour)
            if step_exec.started_at and datetime.now() - step_exec.started_at > timedelta(hours=1):
                logger.warning(f"Step {step} appears stuck, allowing restart")
                return True
            return False  # Currently running
        
        if step_exec.is_failed():
            return step_exec.should_retry()
        
        return True
    
    def start_step(self, step: ProcessingStep, metadata: Optional[Dict[str, Any]] = None) -> StepExecution:
        """Mark step as started"""
        step_exec = StepExecution(
            step=step,
            status=ProcessingStatus.IN_PROGRESS,
            started_at=datetime.now(),
            metadata=metadata or {}
        )
        self.steps[step] = step_exec
        self.updated_at = datetime.now()
        return step_exec
    
    def complete_step(self, 
                     step: ProcessingStep, 
                     result_summary: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed"""
        if step not in self.steps:
            logger.warning(f"Completing step {step} that was never started")
            self.start_step(step, metadata)
        
        step_exec = self.steps[step]
        step_exec.status = ProcessingStatus.COMPLETED
        step_exec.completed_at = datetime.now()
        step_exec.result_summary = result_summary
        
        if metadata:
            step_exec.metadata.update(metadata)
        
        # Calculate execution time
        if step_exec.started_at:
            step_exec.execution_time_seconds = (step_exec.completed_at - step_exec.started_at).total_seconds()
        
        self.updated_at = datetime.now()
    
    def fail_step(self, 
                  step: ProcessingStep, 
                  error_message: str,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as failed"""
        if step not in self.steps:
            logger.warning(f"Failing step {step} that was never started")
            self.start_step(step, metadata)
        
        step_exec = self.steps[step]
        step_exec.status = ProcessingStatus.FAILED
        step_exec.completed_at = datetime.now()
        step_exec.error_message = error_message
        
        if metadata:
            step_exec.metadata.update(metadata)
        
        # Calculate execution time
        if step_exec.started_at:
            step_exec.execution_time_seconds = (step_exec.completed_at - step_exec.started_at).total_seconds()
        
        self.updated_at = datetime.now()
    
    def add_profile_usage(self, profile_id: str) -> None:
        """Add profile as using this opportunity"""
        self.profiles_using.add(profile_id)
        self.updated_at = datetime.now()
    
    def remove_profile_usage(self, profile_id: str) -> None:
        """Remove profile from using this opportunity"""
        self.profiles_using.discard(profile_id)
        self.updated_at = datetime.now()
    
    def get_completion_summary(self) -> Dict[str, Any]:
        """Get summary of step completion"""
        total_steps = len(self.steps)
        completed = sum(1 for step in self.steps.values() if step.is_completed())
        failed = sum(1 for step in self.steps.values() if step.is_failed())
        in_progress = sum(1 for step in self.steps.values() if step.is_in_progress())
        
        return {
            'total_steps': total_steps,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'completion_percentage': (completed / total_steps * 100) if total_steps > 0 else 0,
            'profiles_using_count': len(self.profiles_using)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        # Convert set to list
        data['profiles_using'] = list(self.profiles_using)
        # Convert steps dict
        data['steps'] = {step.value: step_exec.to_dict() for step, step_exec in self.steps.items()}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpportunityProcessingState':
        """Create from dictionary"""
        data = data.copy()
        # Convert ISO format back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        # Convert list back to set
        data['profiles_using'] = set(data['profiles_using'])
        # Convert steps dict
        steps_data = data.pop('steps', {})
        data['steps'] = {
            ProcessingStep(step_name): StepExecution.from_dict(step_data)
            for step_name, step_data in steps_data.items()
        }
        return cls(**data)


class ProcessingStateManager:
    """Manages processing state across all opportunities and profiles"""
    
    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path("data/processing_state")
        self.state_file = self.state_dir / "processing_state.json"
        self.opportunities: Dict[str, OpportunityProcessingState] = {}
        self.lock = asyncio.Lock()
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self._load_state()
    
    def _load_state(self) -> None:
        """Load processing state from disk"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    self.opportunities = {
                        opp_id: OpportunityProcessingState.from_dict(data)
                        for opp_id, data in state_data.items()
                    }
                logger.info(f"Loaded processing state for {len(self.opportunities)} opportunities")
            else:
                self.opportunities = {}
        except Exception as e:
            logger.error(f"Failed to load processing state: {e}")
            self.opportunities = {}
    
    async def _save_state(self) -> None:
        """Save processing state to disk"""
        try:
            state_data = {
                opp_id: opp_state.to_dict()
                for opp_id, opp_state in self.opportunities.items()
            }
            
            # Write to temporary file first, then move to avoid corruption
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            temp_file.replace(self.state_file)
            
        except Exception as e:
            logger.error(f"Failed to save processing state: {e}")
    
    async def get_opportunity_state(self, opportunity_id: str) -> Optional[OpportunityProcessingState]:
        """Get processing state for opportunity"""
        async with self.lock:
            return self.opportunities.get(opportunity_id)
    
    async def create_or_get_opportunity_state(self,
                                            opportunity_id: str,
                                            source_type: str,
                                            organization_name: str,
                                            ein: Optional[str] = None) -> OpportunityProcessingState:
        """Create or get existing opportunity processing state"""
        async with self.lock:
            if opportunity_id not in self.opportunities:
                self.opportunities[opportunity_id] = OpportunityProcessingState(
                    opportunity_id=opportunity_id,
                    source_type=source_type,
                    organization_name=organization_name,
                    ein=ein
                )
                await self._save_state()
            
            return self.opportunities[opportunity_id]
    
    async def should_run_step(self, 
                             opportunity_id: str, 
                             step: ProcessingStep,
                             force_refresh: bool = False) -> bool:
        """Check if processing step should be run"""
        async with self.lock:
            if opportunity_id not in self.opportunities:
                return True  # No state means we should run
            
            return self.opportunities[opportunity_id].should_run_step(step, force_refresh)
    
    @asynccontextmanager
    async def execute_step(self, 
                          opportunity_id: str, 
                          step: ProcessingStep,
                          source_type: str,
                          organization_name: str,
                          ein: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Context manager for step execution with automatic state tracking"""
        
        # Get or create opportunity state
        opp_state = await self.create_or_get_opportunity_state(
            opportunity_id=opportunity_id,
            source_type=source_type,
            organization_name=organization_name,
            ein=ein
        )
        
        # Start step
        async with self.lock:
            step_exec = opp_state.start_step(step, metadata)
            await self._save_state()
        
        try:
            yield step_exec
            
            # Mark as completed if we reach here without exception
            async with self.lock:
                opp_state.complete_step(step)
                await self._save_state()
                
        except Exception as e:
            # Mark as failed
            async with self.lock:
                opp_state.fail_step(step, str(e))
                await self._save_state()
            raise
    
    async def add_profile_to_opportunity(self, opportunity_id: str, profile_id: str) -> None:
        """Add profile as using this opportunity"""
        async with self.lock:
            if opportunity_id in self.opportunities:
                self.opportunities[opportunity_id].add_profile_usage(profile_id)
                await self._save_state()
    
    async def remove_profile_from_opportunity(self, opportunity_id: str, profile_id: str) -> None:
        """Remove profile from using this opportunity"""
        async with self.lock:
            if opportunity_id in self.opportunities:
                self.opportunities[opportunity_id].remove_profile_usage(profile_id)
                await self._save_state()
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        async with self.lock:
            total_opportunities = len(self.opportunities)
            
            step_stats = {}
            for step in ProcessingStep:
                completed = sum(1 for opp in self.opportunities.values() if opp.is_step_completed(step))
                step_stats[step.value] = {
                    'completed': completed,
                    'completion_rate': (completed / total_opportunities * 100) if total_opportunities > 0 else 0
                }
            
            # AI step stats (expensive operations)
            ai_steps = [ProcessingStep.AI_CLASSIFICATION, ProcessingStep.AI_OPPORTUNITY_MATCHING, 
                       ProcessingStep.AI_COMPETITIVE_ANALYSIS, ProcessingStep.AI_RISK_ASSESSMENT]
            
            ai_completed = sum(
                1 for opp in self.opportunities.values()
                if any(opp.is_step_completed(step) for step in ai_steps)
            )
            
            return {
                'total_opportunities': total_opportunities,
                'ai_analyses_completed': ai_completed,
                'step_completion_rates': step_stats,
                'opportunities_by_source': self._get_source_distribution()
            }
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of opportunities by source type"""
        distribution = {}
        for opp in self.opportunities.values():
            source = opp.source_type
            distribution[source] = distribution.get(source, 0) + 1
        return distribution
    
    async def cleanup_old_state(self, max_age: timedelta = timedelta(days=30)) -> int:
        """Clean up old processing state entries"""
        async with self.lock:
            cutoff_date = datetime.now() - max_age
            old_opportunities = [
                opp_id for opp_id, opp_state in self.opportunities.items()
                if opp_state.updated_at < cutoff_date and len(opp_state.profiles_using) == 0
            ]
            
            for opp_id in old_opportunities:
                del self.opportunities[opp_id]
            
            if old_opportunities:
                await self._save_state()
                logger.info(f"Cleaned up {len(old_opportunities)} old processing state entries")
            
            return len(old_opportunities)


# Global processing state manager instance
_state_manager: Optional[ProcessingStateManager] = None


def get_processing_state_manager() -> ProcessingStateManager:
    """Get or create global processing state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = ProcessingStateManager()
    return _state_manager


# Convenience functions for common operations
async def should_run_step(opportunity_id: str, step: ProcessingStep, force_refresh: bool = False) -> bool:
    """Check if processing step should be run"""
    manager = get_processing_state_manager()
    return await manager.should_run_step(opportunity_id, step, force_refresh)


async def execute_step(opportunity_id: str, 
                      step: ProcessingStep,
                      source_type: str,
                      organization_name: str,
                      ein: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None):
    """Context manager for step execution with state tracking"""
    manager = get_processing_state_manager()
    return manager.execute_step(
        opportunity_id=opportunity_id,
        step=step,
        source_type=source_type,
        organization_name=organization_name,
        ein=ein,
        metadata=metadata
    )