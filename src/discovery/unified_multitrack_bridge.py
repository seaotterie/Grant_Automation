"""
Unified MultiTrack Discovery Bridge
Phase 3B: Architectural integration between MultiTrackDiscoveryEngine and UnifiedDiscoveryEngine

This bridge combines the best of both architectures:
- MultiTrack: Session management, progress tracking, concurrent execution
- Unified: Strategy pattern, client architecture integration, simplified discovery

Architecture Pattern: Adapter Pattern + Strategy Pattern
"""
import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

# Import from MultiTrack system
from .base_discoverer import DiscoverySession, DiscoveryStatus, DiscoveryResult
from .discovery_engine import MultiTrackDiscoveryEngine

# Import from Unified system  
from .discovery_strategy import (
    UnifiedDiscoveryEngine, 
    GovernmentDiscoveryStrategy, 
    FoundationDiscoveryStrategy,
    CorporateDiscoveryStrategy
)

# Import unified client architecture from Phase 2
from ..core.data_models import (
    BaseOpportunity, 
    GovernmentOpportunity, 
    FoundationOpportunity, 
    CorporateOpportunity,
    OpportunityCollection,
    FundingSourceType
)
from ..profiles.models import OrganizationProfile
from ..core.data_models import FundingSourceType


@dataclass
class BridgedDiscoverySession:
    """Enhanced discovery session that bridges both architectures"""
    session_id: str
    profile: OrganizationProfile
    funding_types: List[FundingSourceType]
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    
    # MultiTrack capabilities
    progress_updates: List[Dict[str, Any]] = field(default_factory=list)
    api_calls_made: int = 0
    cache_hits: int = 0
    errors_by_strategy: Dict[str, str] = field(default_factory=dict)
    
    # Unified results
    opportunity_collection: Optional[OpportunityCollection] = None
    results_by_strategy: Dict[str, List[BaseOpportunity]] = field(default_factory=dict)
    strategy_execution_times: Dict[str, float] = field(default_factory=dict)
    
    # Statistics
    total_opportunities: int = 0
    avg_relevance_score: float = 0.0
    top_opportunities: List[BaseOpportunity] = field(default_factory=list)


class UnifiedMultiTrackBridge:
    """
    Bridge that unifies the MultiTrack and Unified discovery architectures
    
    Key Features:
    1. Session management from MultiTrack
    2. Strategy pattern from Unified  
    3. Phase 2 unified client architecture integration
    4. Concurrent strategy execution
    5. Real-time progress tracking
    6. Comprehensive error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize strategy engines
        self.unified_engine = UnifiedDiscoveryEngine()
        self.multitrack_engine = MultiTrackDiscoveryEngine()
        
        # Active sessions tracking
        self.active_sessions: Dict[str, BridgedDiscoverySession] = {}
        
        # Strategy mapping for unified client integration
        self.strategy_mapping = {
            FundingSourceType.GOVERNMENT_FEDERAL: "government",
            FundingSourceType.GOVERNMENT_STATE: "government", 
            FundingSourceType.FOUNDATION_PRIVATE: "foundation",
            FundingSourceType.FOUNDATION_CORPORATE: "foundation",
            FundingSourceType.CORPORATE_CSR: "corporate",
            FundingSourceType.CORPORATE_SPONSORSHIP: "corporate"
        }
    
    async def discover_opportunities(
        self,
        profile: OrganizationProfile,
        funding_types: Optional[List[FundingSourceType]] = None,
        max_results_per_type: int = 1000,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> BridgedDiscoverySession:
        """
        Execute unified multi-track discovery with session management
        
        Args:
            profile: Organization profile to search for
            funding_types: Types of funding to search (defaults to profile preferences)
            max_results_per_type: Maximum results per funding type
            progress_callback: Optional callback for progress updates
            
        Returns:
            BridgedDiscoverySession with complete results
        """
        
        # Use default funding types if not specified
        if not funding_types:
            funding_types = [
                FundingSourceType.GOVERNMENT_FEDERAL,
                FundingSourceType.GOVERNMENT_STATE,
                FundingSourceType.FOUNDATION_CORPORATE,
                FundingSourceType.CORPORATE_CSR
            ]
        
        # Create bridged session
        session = BridgedDiscoverySession(
            session_id=f"bridge_{uuid.uuid4().hex[:12]}",
            profile=profile,
            funding_types=funding_types,
            status=DiscoveryStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.active_sessions[session.session_id] = session
        
        try:
            # Update status and notify
            session.status = DiscoveryStatus.RUNNING
            await self._send_progress_update(session, progress_callback, {
                "status": "started",
                "message": f"Starting unified multi-track discovery for {profile.name}",
                "funding_types": [ft.value for ft in funding_types],
                "strategies": list(set(self.strategy_mapping[ft] for ft in funding_types))
            })
            
            # Create opportunity collection
            session.opportunity_collection = OpportunityCollection(
                collection_id=session.session_id,
                name=f"Multi-Track Discovery: {profile.name}",
                profile_used=getattr(profile, 'ein', None)
            )
            
            # Execute discovery using unified strategies with concurrent execution
            await self._execute_unified_strategies(session, profile, max_results_per_type, progress_callback)
            
            # Calculate final statistics
            await self._calculate_session_statistics(session)
            
            # Complete session
            session.status = DiscoveryStatus.COMPLETED
            session.completed_at = datetime.now()
            session.execution_time_seconds = (
                session.completed_at - session.started_at
            ).total_seconds()
            
            await self._send_progress_update(session, progress_callback, {
                "status": "completed",
                "message": f"Multi-track discovery completed",
                "total_opportunities": session.total_opportunities,
                "execution_time": session.execution_time_seconds,
                "avg_relevance_score": session.avg_relevance_score
            })
            
        except Exception as e:
            self.logger.error(f"Bridged discovery failed: {e}", exc_info=True)
            session.status = DiscoveryStatus.ERROR
            session.completed_at = datetime.now()
            if session.started_at:
                session.execution_time_seconds = (
                    session.completed_at - session.started_at
                ).total_seconds()
            
            await self._send_progress_update(session, progress_callback, {
                "status": "error",
                "message": f"Discovery failed: {str(e)}",
                "error": str(e)
            })
        
        return session
    
    async def _execute_unified_strategies(
        self,
        session: BridgedDiscoverySession,
        profile: OrganizationProfile,
        max_results_per_type: int,
        progress_callback: Optional[Callable]
    ):
        """Execute discovery using unified strategies with concurrent execution"""
        
        # Group funding types by strategy
        strategy_groups = {}
        for funding_type in session.funding_types:
            strategy_name = self.strategy_mapping.get(funding_type)
            if strategy_name:
                if strategy_name not in strategy_groups:
                    strategy_groups[strategy_name] = []
                strategy_groups[strategy_name].append(funding_type)
        
        # Execute strategies concurrently
        strategy_tasks = []
        for strategy_name, funding_types in strategy_groups.items():
            task = asyncio.create_task(
                self._execute_single_strategy(
                    session, strategy_name, profile, max_results_per_type, progress_callback
                )
            )
            strategy_tasks.append((strategy_name, task))
        
        # Wait for all strategies to complete
        for strategy_name, task in strategy_tasks:
            try:
                strategy_start = datetime.now()
                results = await task
                strategy_end = datetime.now()
                
                # Record execution time
                session.strategy_execution_times[strategy_name] = (
                    strategy_end - strategy_start
                ).total_seconds()
                
                # Store results
                session.results_by_strategy[strategy_name] = results
                
                # Add to opportunity collection
                for opportunity in results:
                    session.opportunity_collection.add_opportunity(opportunity)
                
                await self._send_progress_update(session, progress_callback, {
                    "status": "strategy_completed",
                    "strategy": strategy_name,
                    "message": f"Completed {strategy_name} discovery",
                    "results_count": len(results),
                    "execution_time": session.strategy_execution_times[strategy_name]
                })
                
            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} failed: {e}")
                session.errors_by_strategy[strategy_name] = str(e)
                
                await self._send_progress_update(session, progress_callback, {
                    "status": "strategy_error",
                    "strategy": strategy_name,
                    "message": f"Strategy {strategy_name} failed: {str(e)}",
                    "error": str(e)
                })
    
    async def _execute_single_strategy(
        self,
        session: BridgedDiscoverySession,
        strategy_name: str,
        profile: OrganizationProfile,
        max_results: int,
        progress_callback: Optional[Callable]
    ) -> List[BaseOpportunity]:
        """Execute a single discovery strategy"""
        
        try:
            # Get strategy from unified engine
            strategy = self.unified_engine.strategies.get(strategy_name)
            if not strategy:
                raise ValueError(f"Strategy {strategy_name} not found")
            
            # Create strategy-specific progress callback
            def strategy_progress_callback(message: str):
                asyncio.create_task(
                    self._send_progress_update(session, progress_callback, {
                        "status": "strategy_progress",
                        "strategy": strategy_name,
                        "message": message
                    })
                )
            
            # Execute strategy discovery
            opportunities = await strategy.discover_opportunities(
                profile=profile,
                max_results=max_results,
                progress_callback=strategy_progress_callback
            )
            
            # Update API call tracking
            session.api_calls_made += getattr(strategy, '_api_calls_made', 0)
            
            return opportunities if opportunities else []
            
        except Exception as e:
            self.logger.error(f"Single strategy execution failed for {strategy_name}: {e}")
            raise
    
    async def _calculate_session_statistics(self, session: BridgedDiscoverySession):
        """Calculate comprehensive session statistics"""
        
        if not session.opportunity_collection:
            return
        
        # Get all opportunities
        all_opportunities = []
        for opportunities in session.results_by_strategy.values():
            all_opportunities.extend(opportunities)
        
        session.total_opportunities = len(all_opportunities)
        
        if all_opportunities:
            # Calculate average relevance score
            total_score = sum(getattr(opp, 'relevance_score', 0) for opp in all_opportunities)
            session.avg_relevance_score = total_score / len(all_opportunities)
            
            # Get top 10 opportunities by relevance score
            sorted_opportunities = sorted(
                all_opportunities,
                key=lambda x: getattr(x, 'relevance_score', 0),
                reverse=True
            )
            session.top_opportunities = sorted_opportunities[:10]
    
    async def _send_progress_update(
        self,
        session: BridgedDiscoverySession,
        progress_callback: Optional[Callable],
        update_data: Dict[str, Any]
    ):
        """Send progress update with session tracking"""
        
        # Add session context
        update_data.update({
            "session_id": session.session_id,
            "profile_name": session.profile.name,
            "timestamp": datetime.now().isoformat()
        })
        
        # Store update in session
        session.progress_updates.append(update_data)
        
        # Send to callback if provided
        if progress_callback:
            try:
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(session.session_id, update_data)
                else:
                    progress_callback(session.session_id, update_data)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def get_session(self, session_id: str) -> Optional[BridgedDiscoverySession]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "profile_name": session.profile.name,
            "status": session.status.value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "execution_time_seconds": session.execution_time_seconds,
            "funding_types_searched": [ft.value for ft in session.funding_types],
            "total_opportunities": session.total_opportunities,
            "avg_relevance_score": session.avg_relevance_score,
            "results_by_strategy": {
                strategy: len(results) for strategy, results in session.results_by_strategy.items()
            },
            "strategy_execution_times": session.strategy_execution_times,
            "errors": session.errors_by_strategy,
            "api_calls_made": session.api_calls_made,
            "cache_hits": session.cache_hits,
            "progress_updates_count": len(session.progress_updates),
            "top_opportunities": [
                {
                    "title": getattr(opp, 'title', ''),
                    "funder_name": getattr(opp, 'funder_name', ''),
                    "funding_amount_max": getattr(opp, 'funding_amount_max', 0),
                    "relevance_score": getattr(opp, 'relevance_score', 0),
                    "source_type": getattr(opp, 'source_type', '').value if hasattr(getattr(opp, 'source_type', ''), 'value') else str(getattr(opp, 'source_type', ''))
                }
                for opp in session.top_opportunities[:5]
            ]
        }
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get overall bridge status"""
        
        # Get active session counts
        active_sessions = len([s for s in self.active_sessions.values() 
                             if s.status == DiscoveryStatus.RUNNING])
        
        completed_sessions = len([s for s in self.active_sessions.values() 
                                if s.status == DiscoveryStatus.COMPLETED])
        
        error_sessions = len([s for s in self.active_sessions.values() 
                            if s.status == DiscoveryStatus.ERROR])
        
        return {
            "bridge_status": "operational",
            "architecture": "unified_multitrack_bridge",
            "last_check": datetime.now().isoformat(),
            "total_sessions": len(self.active_sessions),
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "error_sessions": error_sessions,
            "success_rate": completed_sessions / len(self.active_sessions) if self.active_sessions else 0.0,
            "unified_engine_status": "integrated",
            "multitrack_engine_status": "bridged",
            "capabilities": {
                "concurrent_strategy_execution": True,
                "real_time_progress_tracking": True,
                "unified_client_architecture": True,
                "session_management": True,
                "comprehensive_error_handling": True,
                "strategy_pattern_integration": True,
                "phase_2_client_integration": True
            },
            "strategies_available": list(self.unified_engine.strategies.keys())
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, session in self.active_sessions.items():
            if (session.completed_at and session.completed_at < cutoff_time) or \
               (session.started_at and session.started_at < cutoff_time and 
                session.status != DiscoveryStatus.RUNNING):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        return len(sessions_to_remove)


# Global bridge instance
_unified_bridge: Optional[UnifiedMultiTrackBridge] = None


def get_unified_bridge() -> UnifiedMultiTrackBridge:
    """Get global unified bridge instance"""
    global _unified_bridge
    if _unified_bridge is None:
        _unified_bridge = UnifiedMultiTrackBridge()
    return _unified_bridge