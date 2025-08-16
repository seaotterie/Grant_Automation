"""
Multi-Track Discovery Engine
Orchestrates discovery across multiple funding sources simultaneously
"""
import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from datetime import datetime, timedelta
from collections import defaultdict

from .base_discoverer import (
    BaseDiscoverer, 
    DiscoveryResult, 
    DiscoverySession, 
    DiscoveryStatus,
    discoverer_registry
)
from .nonprofit_discoverer import NonprofitDiscoverer
from .government_discoverer import GovernmentDiscoverer
from .commercial_discoverer import CommercialDiscoverer
from .state_discoverer import StateDiscoverer
from .entity_discovery_service import get_entity_discovery_service, EntityDiscoveryResult

from src.profiles.models import (
    OrganizationProfile, 
    ProfileSearchParams, 
    FundingType
)
from src.profiles.search_engine import ProfileSearchEngine


class MultiTrackDiscoveryEngine:
    """Main discovery engine that coordinates multiple discovery sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.search_engine = ProfileSearchEngine()
        self.active_sessions: Dict[str, DiscoverySession] = {}
        self.session_results: Dict[str, List[DiscoveryResult]] = {}
        
        # Initialize entity-based discovery service
        self.entity_discovery_service = get_entity_discovery_service()
        
        # Initialize and register discoverers
        self._initialize_discoverers()
    
    def _initialize_discoverers(self):
        """Initialize and register all discoverers"""
        # Register nonprofit discoverer
        nonprofit_discoverer = NonprofitDiscoverer()
        discoverer_registry.register_discoverer(nonprofit_discoverer)
        
        # Register government discoverer
        government_discoverer = GovernmentDiscoverer()
        discoverer_registry.register_discoverer(government_discoverer)
        
        # Register commercial discoverer
        commercial_discoverer = CommercialDiscoverer()
        discoverer_registry.register_discoverer(commercial_discoverer)
        
        # Register state discoverer
        state_discoverer = StateDiscoverer()
        discoverer_registry.register_discoverer(state_discoverer)
    
    async def discover_opportunities(
        self,
        profile: OrganizationProfile,
        funding_types: Optional[List[FundingType]] = None,
        max_results_per_type: int = 100,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> DiscoverySession:
        """
        Main discovery method that coordinates multi-track search
        
        Args:
            profile: Organization profile to search for
            funding_types: Types of funding to search (defaults to profile preferences)
            max_results_per_type: Maximum results per funding type
            progress_callback: Optional callback for progress updates
            
        Returns:
            DiscoverySession with complete results
        """
        
        # Use profile funding preferences if not specified
        if not funding_types:
            funding_types = profile.funding_preferences.funding_types
        
        # Generate search parameters for each funding type
        search_params = self.search_engine.generate_search_params(
            profile, funding_types, max_results_per_type
        )
        
        # Create discovery session
        session = DiscoverySession(
            session_id=f"discovery_{uuid.uuid4().hex[:12]}",
            profile_id=profile.profile_id,
            profile_name=profile.name,
            funding_types=funding_types,
            search_params=search_params,
            status=DiscoveryStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.active_sessions[session.session_id] = session
        self.session_results[session.session_id] = []
        
        try:
            # Start discovery
            session.status = DiscoveryStatus.RUNNING
            if progress_callback:
                progress_callback(session.session_id, {
                    "status": "started",
                    "message": f"Starting multi-track discovery for {profile.name}",
                    "funding_types": [ft.value for ft in funding_types]
                })
            
            # Execute discovery across all funding types concurrently
            await self._execute_concurrent_discovery(
                session, profile, search_params, progress_callback
            )
            
            # Apply Schedule I grantee fast-tracking
            self._apply_schedule_i_fast_tracking(session.session_id, profile, progress_callback)
            
            # Finalize session
            session.status = DiscoveryStatus.COMPLETED
            session.completed_at = datetime.now()
            session.execution_time_seconds = (
                session.completed_at - session.started_at
            ).total_seconds()
            session.total_results = len(self.session_results[session.session_id])
            
            if progress_callback:
                progress_callback(session.session_id, {
                    "status": "completed",
                    "message": f"Discovery completed: {session.total_results} opportunities found",
                    "total_results": session.total_results,
                    "execution_time": session.execution_time_seconds
                })
            
        except Exception as e:
            session.status = DiscoveryStatus.ERROR
            session.completed_at = datetime.now()
            if session.started_at:
                session.execution_time_seconds = (
                    session.completed_at - session.started_at
                ).total_seconds()
            
            if progress_callback:
                progress_callback(session.session_id, {
                    "status": "error",
                    "message": f"Discovery failed: {str(e)}",
                    "error": str(e)
                })
        
        return session
    
    async def _execute_concurrent_discovery(
        self,
        session: DiscoverySession,
        profile: OrganizationProfile,
        search_params: Dict[FundingType, ProfileSearchParams],
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]]
    ):
        """Execute discovery across multiple funding types concurrently"""
        
        # Create discovery tasks for each funding type
        discovery_tasks = []
        
        for funding_type, params in search_params.items():
            discoverers = discoverer_registry.get_discoverers_for_type(funding_type)
            
            if discoverers:
                # Use the first available discoverer for each funding type
                discoverer = discoverers[0]
                
                task = asyncio.create_task(
                    self._execute_single_discoverer(
                        session, discoverer, profile, params, progress_callback
                    )
                )
                discovery_tasks.append(task)
                
                if progress_callback:
                    progress_callback(session.session_id, {
                        "status": "running",
                        "message": f"Starting {funding_type.value} discovery with {discoverer.name}",
                        "funding_type": funding_type.value,
                        "discoverer": discoverer.name
                    })
        
        # Execute all discovery tasks concurrently
        if discovery_tasks:
            await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Update results by type
        results = self.session_results[session.session_id]
        for funding_type in search_params.keys():
            type_results = [r for r in results if r.source_type == funding_type]
            session.results_by_type[funding_type] = len(type_results)
    
    async def _execute_single_discoverer(
        self,
        session: DiscoverySession,
        discoverer: BaseDiscoverer,
        profile: OrganizationProfile,
        search_params: ProfileSearchParams,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]]
    ):
        """Execute discovery for a single discoverer"""
        
        try:
            # Validate search parameters
            if not await discoverer.validate_search_params(search_params):
                error_msg = f"Invalid search parameters for {discoverer.name}"
                session.errors_by_type[discoverer.funding_type] = error_msg
                
                if progress_callback:
                    progress_callback(session.session_id, {
                        "status": "error",
                        "message": error_msg,
                        "funding_type": discoverer.funding_type.value,
                        "discoverer": discoverer.name
                    })
                return
            
            # Pre-discovery setup
            setup_success = await discoverer.pre_discovery_setup(profile)
            if not setup_success:
                error_msg = f"Setup failed for {discoverer.name}"
                session.errors_by_type[discoverer.funding_type] = error_msg
                
                if progress_callback:
                    progress_callback(session.session_id, {
                        "status": "error",
                        "message": error_msg,
                        "funding_type": discoverer.funding_type.value,
                        "discoverer": discoverer.name
                    })
                return
            
            # Execute discovery
            results_count = 0
            max_results = search_params.max_results_per_type
            
            async for result in discoverer.discover_opportunities(
                profile, search_params, max_results
            ):
                # Store result
                self.session_results[session.session_id].append(result)
                results_count += 1
                session.api_calls_made += 1
                
                # Progress update every 10 results
                if results_count % 10 == 0 and progress_callback:
                    progress_callback(session.session_id, {
                        "status": "running",
                        "message": f"Found {results_count} {discoverer.funding_type.value} opportunities",
                        "funding_type": discoverer.funding_type.value,
                        "discoverer": discoverer.name,
                        "results_count": results_count
                    })
            
            # Post-discovery cleanup
            await discoverer.post_discovery_cleanup(session)
            
            # Final progress update
            if progress_callback:
                progress_callback(session.session_id, {
                    "status": "completed",
                    "message": f"Completed {discoverer.funding_type.value} discovery: {results_count} opportunities found",
                    "funding_type": discoverer.funding_type.value,
                    "discoverer": discoverer.name,
                    "results_count": results_count
                })
        
        except Exception as e:
            error_msg = f"Discovery failed for {discoverer.name}: {str(e)}"
            session.errors_by_type[discoverer.funding_type] = error_msg
            
            if progress_callback:
                progress_callback(session.session_id, {
                    "status": "error",
                    "message": error_msg,
                    "funding_type": discoverer.funding_type.value,
                    "discoverer": discoverer.name,
                    "error": str(e)
                })
    
    def get_session_results(
        self,
        session_id: str,
        funding_type: Optional[FundingType] = None,
        min_compatibility_score: Optional[float] = None,
        max_results: Optional[int] = None
    ) -> List[DiscoveryResult]:
        """Get results for a discovery session with optional filtering"""
        
        results = self.session_results.get(session_id, [])
        
        # Apply filters
        if funding_type:
            results = [r for r in results if r.source_type == funding_type]
        
        if min_compatibility_score is not None:
            results = [r for r in results if r.compatibility_score >= min_compatibility_score]
        
        # Sort by compatibility score (descending)
        results.sort(key=lambda r: r.compatibility_score, reverse=True)
        
        # Apply result limit
        if max_results:
            results = results[:max_results]
        
        return results
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of discovery session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        results = self.session_results.get(session_id, [])
        
        # Calculate summary statistics
        total_results = len(results)
        
        # Results by funding type
        results_by_type = defaultdict(int)
        avg_scores_by_type = defaultdict(list)
        
        for result in results:
            results_by_type[result.source_type.value] += 1
            avg_scores_by_type[result.source_type.value].append(result.compatibility_score)
        
        # Calculate average scores
        for funding_type, scores in avg_scores_by_type.items():
            if scores:
                avg_scores_by_type[funding_type] = sum(scores) / len(scores)
            else:
                avg_scores_by_type[funding_type] = 0.0
        
        # Top opportunities
        top_opportunities = sorted(results, key=lambda r: r.compatibility_score, reverse=True)[:10]
        
        # Success rate by discoverer
        success_rates = {}
        for funding_type in session.funding_types:
            if funding_type in session.errors_by_type:
                success_rates[funding_type.value] = 0.0
            else:
                success_rates[funding_type.value] = 1.0
        
        return {
            "session_id": session_id,
            "profile_id": session.profile_id,
            "profile_name": session.profile_name,
            "status": session.status.value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "execution_time_seconds": session.execution_time_seconds,
            "funding_types_searched": [ft.value for ft in session.funding_types],
            "total_results": total_results,
            "results_by_funding_type": dict(results_by_type),
            "avg_compatibility_scores": dict(avg_scores_by_type),
            "success_rates": success_rates,
            "errors": dict(session.errors_by_type),
            "api_calls_made": session.api_calls_made,
            "cache_hits": session.cache_hits,
            "top_opportunities": [
                {
                    "organization_name": opp.organization_name,
                    "funding_type": opp.source_type.value,
                    "program_name": opp.program_name,
                    "funding_amount": opp.funding_amount,
                    "compatibility_score": opp.compatibility_score,
                    "opportunity_id": opp.opportunity_id
                }
                for opp in top_opportunities
            ]
        }
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get overall engine status and health"""
        
        # Get registry status
        registry_status = discoverer_registry.get_registry_status()
        
        # Active sessions
        active_sessions = len([s for s in self.active_sessions.values() 
                             if s.status == DiscoveryStatus.RUNNING])
        
        # Recent session stats
        recent_sessions = [s for s in self.active_sessions.values() 
                          if s.started_at and 
                          (datetime.now() - s.started_at).total_seconds() < 3600]  # Last hour
        
        successful_sessions = len([s for s in recent_sessions 
                                 if s.status == DiscoveryStatus.COMPLETED])
        
        return {
            "engine_status": "operational",
            "last_check": datetime.now().isoformat(),
            "active_sessions": active_sessions,
            "total_sessions": len(self.active_sessions),
            "recent_sessions_last_hour": len(recent_sessions),
            "successful_sessions_last_hour": successful_sessions,
            "success_rate": successful_sessions / len(recent_sessions) if recent_sessions else 0.0,
            "discoverer_registry": registry_status,
            "capabilities": {
                "concurrent_discovery": True,
                "real_time_progress": True,
                "multi_track_search": True,
                "intelligent_scoring": True,
                "result_filtering": True,
                "session_management": True
            }
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old discovery sessions"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if (session.completed_at and session.completed_at < cutoff_time) or \
               (session.started_at and session.started_at < cutoff_time and 
                session.status != DiscoveryStatus.RUNNING):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            if session_id in self.session_results:
                del self.session_results[session_id]
        
        return len(sessions_to_remove)
    
    def _apply_schedule_i_fast_tracking(
        self, 
        session_id: str, 
        profile: OrganizationProfile,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """Apply Schedule I grantee fast-tracking to discovery results"""
        
        if not profile.schedule_i_grantees:
            return  # No grantees to match against
        
        # Get session results
        results = self.session_results.get(session_id, [])
        if not results:
            return  # No results to process
        
        # Import grantee matcher
        from src.utils.grantee_matcher import apply_schedule_i_fast_tracking
        
        # Apply fast-tracking
        updated_results = apply_schedule_i_fast_tracking(results, profile)
        
        # Update session results
        self.session_results[session_id] = updated_results
        
        # Count grantee matches
        grantee_matches = [r for r in updated_results if r.is_schedule_i_grantee]
        
        if grantee_matches and progress_callback:
            progress_callback(session_id, {
                "status": "schedule_i_processed",
                "message": f"Schedule I fast-tracking: {len(grantee_matches)} grantee matches identified",
                "grantee_matches": len(grantee_matches),
                "fast_tracked": len([r for r in grantee_matches if r.funnel_stage.value == "candidates"])
            })
    
    # Enhanced Entity-Based Discovery Methods
    
    async def discover_with_entity_analytics(
        self,
        profile: OrganizationProfile,
        entity_types: List[str] = None,
        max_results: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> DiscoverySession:
        """
        Enhanced discovery using entity-based architecture and shared analytics.
        
        Args:
            profile: Organization profile for discovery
            entity_types: Types to discover ['nonprofits', 'government', 'foundations']
            max_results: Maximum results to return
            filters: Additional discovery filters
            progress_callback: Progress update callback
            
        Returns:
            DiscoverySession with entity-based results
        """
        # Create discovery session
        session_id = f"entity_session_{uuid.uuid4().hex[:12]}"
        
        # Convert entity types to FundingType for compatibility
        funding_types = []
        if 'nonprofits' in (entity_types or []):
            funding_types.append(FundingType.GRANTS)
        if 'government' in (entity_types or []):
            funding_types.append(FundingType.GOVERNMENT)
        
        session = DiscoverySession(
            session_id=session_id,
            profile_id=profile.profile_id,
            profile_name=profile.name,
            funding_types=funding_types,
            search_params={},  # Empty for entity-based discovery
            status=DiscoveryStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Add entity-specific parameters as external data
        session.external_data = {
            "discovery_mode": "entity_based",
            "max_results": max_results,
            "filters": filters or {},
            "use_shared_analytics": True,
            "entity_types": entity_types or ['nonprofits', 'government']
        }
        
        self.active_sessions[session_id] = session
        
        try:
            if progress_callback:
                progress_callback(session_id, {
                    "status": "starting",
                    "message": "Starting entity-based discovery with shared analytics"
                })
            
            # Use entity discovery service
            entity_results = await self.entity_discovery_service.discover_combined_opportunities(
                profile=profile,
                max_results=max_results,
                include_types=entity_types or ['nonprofits', 'government'],
                filters=filters
            )
            
            if progress_callback:
                progress_callback(session_id, {
                    "status": "processing",
                    "message": f"Analyzing {len(entity_results)} entity-based results"
                })
            
            # Convert to legacy format for compatibility
            legacy_results = []
            for entity_result in entity_results:
                legacy_result = entity_result.to_legacy_result()
                legacy_results.append(legacy_result)
            
            # Store results
            self.session_results[session_id] = legacy_results
            
            # Complete session
            session.status = DiscoveryStatus.COMPLETED
            session.completed_at = datetime.now()
            session.total_results = len(legacy_results)
            
            if progress_callback:
                progress_callback(session_id, {
                    "status": "completed",
                    "message": f"Entity-based discovery completed: {len(legacy_results)} results",
                    "results_count": len(legacy_results),
                    "high_quality_results": len([r for r in entity_results if r.final_discovery_score >= 0.7]),
                    "avg_score": sum(r.final_discovery_score for r in entity_results) / len(entity_results) if entity_results else 0
                })
            
            return session
            
        except Exception as e:
            session.status = DiscoveryStatus.ERROR
            session.completed_at = datetime.now()
            
            if progress_callback:
                progress_callback(session_id, {
                    "status": "error",
                    "message": f"Entity-based discovery failed: {str(e)}",
                    "error": str(e)
                })
            
            return session
    
    async def get_entity_discovery_preview(
        self,
        profile: OrganizationProfile,
        entity_types: List[str] = None,
        limit: int = 10
    ) -> List[EntityDiscoveryResult]:
        """
        Get a quick preview of entity-based discovery results.
        
        Args:
            profile: Organization profile
            entity_types: Types to preview
            limit: Number of preview results
            
        Returns:
            List of EntityDiscoveryResult objects
        """
        try:
            return await self.entity_discovery_service.discover_combined_opportunities(
                profile=profile,
                max_results=limit,
                include_types=entity_types or ['nonprofits', 'government'],
                filters={'preview_mode': True}
            )
        except Exception as e:
            self.logger.error(f"Error getting entity discovery preview: {e}")
            return []


# Global engine instance
discovery_engine = MultiTrackDiscoveryEngine()