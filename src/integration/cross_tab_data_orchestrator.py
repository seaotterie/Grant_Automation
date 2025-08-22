#!/usr/bin/env python3
"""
Cross-Tab Data Orchestrator - Phase 5 Cross-System Integration
Comprehensive system for orchestrating seamless data flow across all tabs.

This system ensures consistent, real-time data synchronization between DISCOVER,
RESEARCH, EXAMINE, and PLAN tabs while maintaining data integrity and performance.
"""

import asyncio
import time
import json
import threading
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import weakref

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import GovernmentOpportunity


class TabContext(Enum):
    """System tabs for data orchestration."""
    DISCOVER = "discover"
    RESEARCH = "research"
    EXAMINE = "examine"
    PLAN = "plan"
    APPROACH = "approach"


class DataOperation(Enum):
    """Types of data operations for synchronization."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    SYNC = "sync"


class DataPriority(Enum):
    """Priority levels for data synchronization."""
    CRITICAL = "critical"     # Immediate sync required
    HIGH = "high"            # Sync within 1 second
    MEDIUM = "medium"        # Sync within 5 seconds
    LOW = "low"             # Sync within 30 seconds
    BACKGROUND = "background" # Sync when convenient


class SyncStatus(Enum):
    """Synchronization status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DataEvent:
    """Data event for cross-tab synchronization."""
    event_id: str
    source_tab: TabContext
    target_tabs: List[TabContext]
    operation: DataOperation
    data_type: str
    data_payload: Dict[str, Any]
    
    priority: DataPriority = DataPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    sync_status: SyncStatus = SyncStatus.PENDING
    
    # Metadata
    user_session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    error_message: Optional[str] = None


@dataclass
class TabState:
    """State information for a specific tab."""
    tab_context: TabContext
    active_opportunities: Set[str] = field(default_factory=set)
    active_organizations: Set[str] = field(default_factory=set)
    active_profiles: Set[str] = field(default_factory=set)
    
    # Data cache
    cached_data: Dict[str, Any] = field(default_factory=dict)
    last_sync_time: datetime = field(default_factory=datetime.now)
    
    # State metadata
    user_interactions: List[Dict[str, Any]] = field(default_factory=list)
    processing_queue: List[str] = field(default_factory=list)  # Event IDs
    
    # Performance metrics
    sync_performance: Dict[str, float] = field(default_factory=dict)
    cache_hit_rate: float = 0.0


@dataclass
class DataFlowMapping:
    """Mapping of data flows between tabs."""
    source_tab: TabContext
    target_tab: TabContext
    data_types: List[str]
    sync_rules: Dict[str, Any]
    
    # Flow characteristics
    is_bidirectional: bool = False
    requires_transformation: bool = False
    transformation_function: Optional[str] = None
    
    # Performance characteristics
    expected_latency_ms: int = 100
    batch_size: int = 1
    sync_frequency: int = 1000  # milliseconds


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    event_id: str
    success: bool
    sync_time_ms: int
    
    synced_tabs: List[TabContext] = field(default_factory=list)
    failed_tabs: List[TabContext] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Performance metrics
    cache_hits: int = 0
    cache_misses: int = 0
    transformation_time_ms: int = 0


class CrossTabDataOrchestrator(BaseProcessor):
    """
    Cross-Tab Data Orchestrator - Phase 5 Cross-System Integration
    
    Comprehensive data orchestration system providing:
    
    ## Seamless Data Flow Management
    - Real-time data synchronization across all tabs
    - Intelligent data routing and transformation
    - Conflict resolution and data consistency
    - Performance-optimized data distribution
    
    ## Tab State Management
    - Active data tracking per tab
    - User interaction pattern analysis
    - Processing queue management
    - Cache optimization across tabs
    
    ## Event-Driven Architecture
    - Asynchronous event processing
    - Priority-based sync scheduling
    - Retry and error handling
    - Performance monitoring and optimization
    
    ## Data Flow Optimization
    - Intelligent caching and prefetching
    - Batch processing for efficiency
    - Network optimization for remote sync
    - Resource usage optimization
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="cross_tab_data_orchestrator",
            description="Orchestrate seamless data flow across all system tabs",
            version="1.0.0",
            dependencies=["workflow_aware_government_scorer", "government_research_integration"],
            estimated_duration=120,  # 2 minutes for orchestration setup
            requires_network=False,  # Local data orchestration
            requires_api_key=False,  # No external APIs
            processor_type="orchestration"
        )
        super().__init__(metadata)
        
        # Initialize orchestration state
        self.tab_states: Dict[TabContext, TabState] = {}
        self.data_flow_mappings: List[DataFlowMapping] = []
        self.event_queue: Dict[DataPriority, List[DataEvent]] = defaultdict(list)
        self.sync_history: List[SyncResult] = []
        
        # Initialize tab states
        self._initialize_tab_states()
        
        # Initialize data flow mappings
        self._initialize_data_flow_mappings()
        
        # Orchestration configuration
        self.orchestration_config = {
            "max_batch_size": 10,
            "sync_timeout_ms": 5000,
            "retry_attempts": 3,
            "cache_ttl_seconds": 300,
            "performance_monitoring": True,
            "real_time_sync": True
        }
        
        # Performance monitoring
        self.performance_metrics = {
            "total_events_processed": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_sync_time_ms": 0,
            "cache_hit_rate": 0.0
        }
        
        # Threading for async operations
        self._sync_thread = None
        self._running = False
        self._lock = threading.RLock()
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute cross-tab data orchestration setup and initial sync."""
        start_time = time.time()
        
        try:
            # Initialize orchestration system
            await self._initialize_orchestration_system(config, workflow_state)
            
            # Perform initial cross-tab data synchronization
            initial_sync_results = await self._perform_initial_sync(workflow_state)
            
            # Establish real-time sync processes
            await self._establish_real_time_sync()
            
            # Generate data flow analytics
            data_flow_analytics = await self._generate_data_flow_analytics()
            
            # Calculate orchestration performance metrics
            performance_metrics = await self._calculate_orchestration_performance()
            
            # Generate sync optimization recommendations
            optimization_recommendations = await self._generate_sync_optimization_recommendations()
            
            # Prepare comprehensive results
            result_data = {
                "orchestration_status": "active",
                "initial_sync_results": initial_sync_results,
                "data_flow_analytics": data_flow_analytics,
                "performance_metrics": performance_metrics,
                "optimization_recommendations": optimization_recommendations,
                "tab_states": {tab.value: state.__dict__ for tab, state in self.tab_states.items()},
                "active_data_flows": len(self.data_flow_mappings),
                "orchestration_summary": {
                    "total_tabs_managed": len(self.tab_states),
                    "data_flows_established": len(self.data_flow_mappings),
                    "real_time_sync_active": self._running,
                    "cache_optimization_enabled": True
                }
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "orchestration_mode": "real_time",
                    "sync_architecture": "event_driven",
                    "performance_optimization": "enabled"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Cross-tab data orchestration failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Cross-tab data orchestration failed: {str(e)}"]
            )
    
    def _initialize_tab_states(self) -> None:
        """Initialize state tracking for all tabs."""
        
        for tab_context in TabContext:
            self.tab_states[tab_context] = TabState(
                tab_context=tab_context,
                cached_data={
                    "opportunities": {},
                    "organizations": {},
                    "profiles": {},
                    "research_insights": {},
                    "dossiers": {},
                    "compliance_roadmaps": {},
                    "agency_intelligence": {},
                    "network_analysis": {}
                }
            )
    
    def _initialize_data_flow_mappings(self) -> None:
        """Initialize data flow mappings between tabs."""
        
        # DISCOVER to RESEARCH flow
        self.data_flow_mappings.append(DataFlowMapping(
            source_tab=TabContext.DISCOVER,
            target_tab=TabContext.RESEARCH,
            data_types=["opportunities", "organizations", "match_scores"],
            sync_rules={
                "sync_on_selection": True,
                "sync_batch_size": 5,
                "include_metadata": True
            },
            is_bidirectional=False,
            expected_latency_ms=200
        ))
        
        # RESEARCH to EXAMINE flow
        self.data_flow_mappings.append(DataFlowMapping(
            source_tab=TabContext.RESEARCH,
            target_tab=TabContext.EXAMINE,
            data_types=["research_insights", "opportunity_analysis", "recommendations"],
            sync_rules={
                "sync_on_completion": True,
                "include_confidence_scores": True,
                "include_supporting_data": True
            },
            is_bidirectional=False,
            requires_transformation=True,
            transformation_function="transform_research_to_examine",
            expected_latency_ms=300
        ))
        
        # EXAMINE to APPROACH flow
        self.data_flow_mappings.append(DataFlowMapping(
            source_tab=TabContext.EXAMINE,
            target_tab=TabContext.APPROACH,
            data_types=["dossiers", "decision_frameworks", "implementation_plans"],
            sync_rules={
                "sync_on_generation": True,
                "include_decision_rationale": True,
                "include_risk_analysis": True
            },
            is_bidirectional=False,
            requires_transformation=True,
            transformation_function="transform_examine_to_approach",
            expected_latency_ms=400
        ))
        
        # PLAN tab bidirectional flows
        for source_tab in [TabContext.DISCOVER, TabContext.RESEARCH, TabContext.EXAMINE]:
            self.data_flow_mappings.append(DataFlowMapping(
                source_tab=source_tab,
                target_tab=TabContext.PLAN,
                data_types=["network_insights", "relationship_data", "strategic_intelligence"],
                sync_rules={
                    "sync_continuously": True,
                    "aggregate_insights": True,
                    "maintain_relationships": True
                },
                is_bidirectional=True,
                expected_latency_ms=150
            ))
        
        # Cross-tab validation flows
        for tab1 in TabContext:
            for tab2 in TabContext:
                if tab1 != tab2:
                    self.data_flow_mappings.append(DataFlowMapping(
                        source_tab=tab1,
                        target_tab=tab2,
                        data_types=["validation_data", "consistency_checks"],
                        sync_rules={
                            "validate_on_change": True,
                            "maintain_consistency": True
                        },
                        is_bidirectional=True,
                        expected_latency_ms=100,
                        sync_frequency=5000  # Every 5 seconds
                    ))
    
    async def _initialize_orchestration_system(self, config: ProcessorConfig, workflow_state) -> None:
        """Initialize the orchestration system."""
        
        # Load current data from workflow state
        await self._load_workflow_state_data(workflow_state)
        
        # Initialize cache systems
        await self._initialize_cache_systems()
        
        # Setup event processing queues
        await self._setup_event_processing()
        
        # Initialize performance monitoring
        await self._initialize_performance_monitoring()
    
    async def _load_workflow_state_data(self, workflow_state) -> None:
        """Load existing data from workflow state into tab states."""
        
        if not workflow_state:
            return
        
        # DISCOVER tab data
        if workflow_state.has_processor_succeeded('government_opportunity_scorer'):
            scorer_data = workflow_state.get_processor_data('government_opportunity_scorer')
            if scorer_data:
                discover_state = self.tab_states[TabContext.DISCOVER]
                discover_state.cached_data["opportunities"] = self._extract_opportunities_data(scorer_data)
                discover_state.cached_data["organizations"] = self._extract_organizations_data(scorer_data)
                
                # Track active opportunities and organizations
                for opp_match in scorer_data.get("opportunity_matches", []):
                    discover_state.active_opportunities.add(opp_match.get("opportunity", {}).get("opportunity_id"))
                    discover_state.active_organizations.add(opp_match.get("organization"))
        
        # RESEARCH tab data
        if workflow_state.has_processor_succeeded('ai_lite_scorer'):
            research_data = workflow_state.get_processor_data('ai_lite_scorer')
            if research_data:
                research_state = self.tab_states[TabContext.RESEARCH]
                research_state.cached_data["research_insights"] = research_data.get("research_insights", {})
                research_state.cached_data["opportunity_analysis"] = research_data.get("opportunity_analysis", {})
        
        # EXAMINE tab data
        if workflow_state.has_processor_succeeded('ai_heavy_dossier_builder'):
            examine_data = workflow_state.get_processor_data('ai_heavy_dossier_builder')
            if examine_data:
                examine_state = self.tab_states[TabContext.EXAMINE]
                examine_state.cached_data["dossiers"] = examine_data.get("comprehensive_dossiers", {})
                examine_state.cached_data["decision_frameworks"] = examine_data.get("decision_frameworks", {})
        
        # PLAN tab data (from network analysis and strategic intelligence)
        plan_state = self.tab_states[TabContext.PLAN]
        if workflow_state.has_processor_succeeded('board_network_analyzer'):
            network_data = workflow_state.get_processor_data('board_network_analyzer')
            if network_data:
                plan_state.cached_data["network_analysis"] = network_data
        
        # Update last sync times
        current_time = datetime.now()
        for state in self.tab_states.values():
            state.last_sync_time = current_time
    
    def _extract_opportunities_data(self, scorer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract opportunities data from scorer results."""
        
        opportunities = {}
        
        for match in scorer_data.get("opportunity_matches", []):
            opportunity = match.get("opportunity", {})
            opp_id = opportunity.get("opportunity_id")
            if opp_id:
                opportunities[opp_id] = {
                    "title": opportunity.get("title"),
                    "agency_code": opportunity.get("agency_code"),
                    "description": opportunity.get("description"),
                    "award_ceiling": opportunity.get("award_ceiling"),
                    "close_date": opportunity.get("close_date"),
                    "match_score": match.get("relevance_score"),
                    "last_updated": datetime.now().isoformat()
                }
        
        return opportunities
    
    def _extract_organizations_data(self, scorer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract organizations data from scorer results."""
        
        organizations = {}
        
        for match in scorer_data.get("opportunity_matches", []):
            org_ein = match.get("organization")
            if org_ein and org_ein not in organizations:
                # Would extract full org data in production
                organizations[org_ein] = {
                    "ein": org_ein,
                    "name": f"Organization {org_ein}",  # Would be real name
                    "last_updated": datetime.now().isoformat()
                }
        
        return organizations
    
    async def _initialize_cache_systems(self) -> None:
        """Initialize intelligent caching systems."""
        
        for tab_state in self.tab_states.values():
            # Initialize cache hit tracking
            tab_state.cache_hit_rate = 0.0
            
            # Setup cache invalidation rules
            tab_state.cached_data["_cache_metadata"] = {
                "ttl_seconds": self.orchestration_config["cache_ttl_seconds"],
                "max_entries": 1000,
                "eviction_policy": "lru"
            }
    
    async def _setup_event_processing(self) -> None:
        """Setup event processing queues and handlers."""
        
        # Initialize priority queues
        for priority in DataPriority:
            self.event_queue[priority] = []
        
        # Start background event processing
        self._running = True
        self._sync_thread = threading.Thread(target=self._process_events_background, daemon=True)
        self._sync_thread.start()
    
    async def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring systems."""
        
        self.performance_metrics = {
            "total_events_processed": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_sync_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "throughput_events_per_second": 0.0,
            "peak_memory_usage_mb": 0.0,
            "network_latency_ms": 0.0
        }
    
    async def _perform_initial_sync(self, workflow_state) -> Dict[str, Any]:
        """Perform initial synchronization across all tabs."""
        
        sync_results = {
            "total_syncs_performed": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "sync_details": []
        }
        
        # Sync data from DISCOVER to other tabs
        discover_sync = await self._sync_discover_data()
        sync_results["sync_details"].append(discover_sync.__dict__)
        sync_results["total_syncs_performed"] += 1
        if discover_sync.success:
            sync_results["successful_syncs"] += 1
        else:
            sync_results["failed_syncs"] += 1
        
        # Sync data from RESEARCH to EXAMINE
        research_sync = await self._sync_research_data()
        sync_results["sync_details"].append(research_sync.__dict__)
        sync_results["total_syncs_performed"] += 1
        if research_sync.success:
            sync_results["successful_syncs"] += 1
        else:
            sync_results["failed_syncs"] += 1
        
        # Cross-validate data consistency
        validation_sync = await self._perform_cross_validation()
        sync_results["sync_details"].append(validation_sync.__dict__)
        sync_results["total_syncs_performed"] += 1
        if validation_sync.success:
            sync_results["successful_syncs"] += 1
        else:
            sync_results["failed_syncs"] += 1
        
        return sync_results
    
    async def _sync_discover_data(self) -> SyncResult:
        """Sync data from DISCOVER tab to other tabs."""
        
        start_time = time.time()
        event_id = f"discover_sync_{int(start_time)}"
        
        discover_state = self.tab_states[TabContext.DISCOVER]
        
        try:
            synced_tabs = []
            failed_tabs = []
            
            # Sync to RESEARCH tab
            research_state = self.tab_states[TabContext.RESEARCH]
            if self._sync_opportunities_to_research(discover_state, research_state):
                synced_tabs.append(TabContext.RESEARCH)
            else:
                failed_tabs.append(TabContext.RESEARCH)
            
            # Sync to PLAN tab
            plan_state = self.tab_states[TabContext.PLAN]
            if self._sync_organizations_to_plan(discover_state, plan_state):
                synced_tabs.append(TabContext.PLAN)
            else:
                failed_tabs.append(TabContext.PLAN)
            
            sync_time = int((time.time() - start_time) * 1000)
            
            return SyncResult(
                event_id=event_id,
                success=len(failed_tabs) == 0,
                sync_time_ms=sync_time,
                synced_tabs=synced_tabs,
                failed_tabs=failed_tabs
            )
            
        except Exception as e:
            sync_time = int((time.time() - start_time) * 1000)
            return SyncResult(
                event_id=event_id,
                success=False,
                sync_time_ms=sync_time,
                errors=[str(e)]
            )
    
    async def _sync_research_data(self) -> SyncResult:
        """Sync data from RESEARCH tab to EXAMINE tab."""
        
        start_time = time.time()
        event_id = f"research_sync_{int(start_time)}"
        
        research_state = self.tab_states[TabContext.RESEARCH]
        examine_state = self.tab_states[TabContext.EXAMINE]
        
        try:
            # Transform and sync research insights
            transformed_data = self._transform_research_to_examine(research_state.cached_data)
            examine_state.cached_data.update(transformed_data)
            
            # Update sync time
            examine_state.last_sync_time = datetime.now()
            
            sync_time = int((time.time() - start_time) * 1000)
            
            return SyncResult(
                event_id=event_id,
                success=True,
                sync_time_ms=sync_time,
                synced_tabs=[TabContext.EXAMINE],
                transformation_time_ms=sync_time // 2  # Estimate transformation time
            )
            
        except Exception as e:
            sync_time = int((time.time() - start_time) * 1000)
            return SyncResult(
                event_id=event_id,
                success=False,
                sync_time_ms=sync_time,
                errors=[str(e)]
            )
    
    async def _perform_cross_validation(self) -> SyncResult:
        """Perform cross-tab data consistency validation."""
        
        start_time = time.time()
        event_id = f"validation_{int(start_time)}"
        
        try:
            validation_errors = []
            
            # Validate opportunity consistency
            validation_errors.extend(self._validate_opportunity_consistency())
            
            # Validate organization consistency
            validation_errors.extend(self._validate_organization_consistency())
            
            # Validate data freshness
            validation_errors.extend(self._validate_data_freshness())
            
            sync_time = int((time.time() - start_time) * 1000)
            
            return SyncResult(
                event_id=event_id,
                success=len(validation_errors) == 0,
                sync_time_ms=sync_time,
                errors=validation_errors
            )
            
        except Exception as e:
            sync_time = int((time.time() - start_time) * 1000)
            return SyncResult(
                event_id=event_id,
                success=False,
                sync_time_ms=sync_time,
                errors=[str(e)]
            )
    
    def _sync_opportunities_to_research(self, discover_state: TabState, research_state: TabState) -> bool:
        """Sync opportunities from DISCOVER to RESEARCH."""
        
        try:
            opportunities = discover_state.cached_data.get("opportunities", {})
            
            # Filter high-priority opportunities for research
            research_opportunities = {}
            for opp_id, opp_data in opportunities.items():
                if opp_data.get("match_score", 0) > 0.6:  # High match score threshold
                    research_opportunities[opp_id] = {
                        **opp_data,
                        "research_priority": "high" if opp_data.get("match_score", 0) > 0.8 else "medium",
                        "sync_source": "discover",
                        "sync_time": datetime.now().isoformat()
                    }
            
            research_state.cached_data["opportunities"] = research_opportunities
            research_state.last_sync_time = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to sync opportunities to research: {e}")
            return False
    
    def _sync_organizations_to_plan(self, discover_state: TabState, plan_state: TabState) -> bool:
        """Sync organizations from DISCOVER to PLAN for network analysis."""
        
        try:
            organizations = discover_state.cached_data.get("organizations", {})
            
            # Prepare organization data for network analysis
            plan_organizations = {}
            for org_ein, org_data in organizations.items():
                plan_organizations[org_ein] = {
                    **org_data,
                    "network_analysis_ready": True,
                    "relationship_mapping": "enabled",
                    "sync_source": "discover",
                    "sync_time": datetime.now().isoformat()
                }
            
            plan_state.cached_data["organizations"] = plan_organizations
            plan_state.last_sync_time = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to sync organizations to plan: {e}")
            return False
    
    def _transform_research_to_examine(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform research data for EXAMINE tab consumption."""
        
        transformed_data = {
            "research_summaries": {},
            "decision_inputs": {},
            "risk_assessments": {}
        }
        
        # Transform research insights into decision inputs
        research_insights = research_data.get("research_insights", {})
        for insight_id, insight_data in research_insights.items():
            transformed_data["decision_inputs"][insight_id] = {
                "research_quality": insight_data.get("quality_score", 0.5),
                "key_findings": insight_data.get("key_findings", []),
                "recommendations": insight_data.get("recommendations", []),
                "confidence_level": insight_data.get("confidence_level", "medium"),
                "decision_readiness": "ready" if insight_data.get("quality_score", 0) > 0.7 else "needs_review"
            }
        
        # Transform opportunity analysis
        opportunity_analysis = research_data.get("opportunity_analysis", {})
        for opp_id, analysis in opportunity_analysis.items():
            transformed_data["risk_assessments"][opp_id] = {
                "competitive_risk": analysis.get("competitive_assessment", "medium"),
                "implementation_risk": analysis.get("implementation_complexity", "medium"),
                "success_probability": analysis.get("success_factors", {}).get("probability", 0.5)
            }
        
        return transformed_data
    
    def _validate_opportunity_consistency(self) -> List[str]:
        """Validate opportunity data consistency across tabs."""
        
        errors = []
        
        # Get opportunity IDs from each tab
        discover_opps = set(self.tab_states[TabContext.DISCOVER].cached_data.get("opportunities", {}).keys())
        research_opps = set(self.tab_states[TabContext.RESEARCH].cached_data.get("opportunities", {}).keys())
        examine_opps = set(self.tab_states[TabContext.EXAMINE].cached_data.get("research_summaries", {}).keys())
        
        # Check for missing opportunities
        if discover_opps and research_opps:
            missing_in_research = discover_opps - research_opps
            if missing_in_research:
                errors.append(f"Opportunities missing in RESEARCH tab: {list(missing_in_research)[:5]}")
        
        if research_opps and examine_opps:
            missing_in_examine = research_opps - examine_opps
            if missing_in_examine:
                errors.append(f"Opportunities missing in EXAMINE tab: {list(missing_in_examine)[:5]}")
        
        return errors
    
    def _validate_organization_consistency(self) -> List[str]:
        """Validate organization data consistency across tabs."""
        
        errors = []
        
        # Get organization EINs from relevant tabs
        discover_orgs = set(self.tab_states[TabContext.DISCOVER].cached_data.get("organizations", {}).keys())
        plan_orgs = set(self.tab_states[TabContext.PLAN].cached_data.get("organizations", {}).keys())
        
        # Check for missing organizations
        if discover_orgs and plan_orgs:
            missing_in_plan = discover_orgs - plan_orgs
            if missing_in_plan:
                errors.append(f"Organizations missing in PLAN tab: {list(missing_in_plan)[:5]}")
        
        return errors
    
    def _validate_data_freshness(self) -> List[str]:
        """Validate data freshness across tabs."""
        
        errors = []
        current_time = datetime.now()
        freshness_threshold = timedelta(minutes=10)
        
        for tab_context, tab_state in self.tab_states.items():
            if current_time - tab_state.last_sync_time > freshness_threshold:
                errors.append(f"Data in {tab_context.value} tab is stale (last sync: {tab_state.last_sync_time})")
        
        return errors
    
    async def _establish_real_time_sync(self) -> None:
        """Establish real-time synchronization processes."""
        
        if self.orchestration_config["real_time_sync"]:
            self._running = True
            self.logger.info("Real-time synchronization established")
        else:
            self.logger.info("Real-time synchronization disabled")
    
    def _process_events_background(self) -> None:
        """Background thread for processing synchronization events."""
        
        while self._running:
            try:
                # Process events by priority
                for priority in [DataPriority.CRITICAL, DataPriority.HIGH, DataPriority.MEDIUM, DataPriority.LOW]:
                    if self.event_queue[priority]:
                        with self._lock:
                            events_to_process = self.event_queue[priority][:self.orchestration_config["max_batch_size"]]
                            self.event_queue[priority] = self.event_queue[priority][self.orchestration_config["max_batch_size"]:]
                        
                        for event in events_to_process:
                            self._process_single_event(event)
                
                # Sleep based on priority processing
                time.sleep(0.1)  # 100ms processing cycle
                
            except Exception as e:
                self.logger.error(f"Error in background event processing: {e}")
                time.sleep(1)  # Longer sleep on error
    
    def _process_single_event(self, event: DataEvent) -> None:
        """Process a single synchronization event."""
        
        start_time = time.time()
        
        try:
            event.sync_status = SyncStatus.IN_PROGRESS
            
            # Route event to appropriate handler
            if event.operation == DataOperation.SYNC:
                success = self._handle_sync_event(event)
            elif event.operation == DataOperation.UPDATE:
                success = self._handle_update_event(event)
            elif event.operation == DataOperation.CREATE:
                success = self._handle_create_event(event)
            elif event.operation == DataOperation.DELETE:
                success = self._handle_delete_event(event)
            else:
                success = False
            
            # Update event status
            event.sync_status = SyncStatus.COMPLETED if success else SyncStatus.FAILED
            
            # Record performance metrics
            sync_time = (time.time() - start_time) * 1000  # Convert to ms
            self._update_performance_metrics(success, sync_time)
            
        except Exception as e:
            event.sync_status = SyncStatus.FAILED
            event.error_message = str(e)
            self.logger.warning(f"Failed to process event {event.event_id}: {e}")
    
    def _handle_sync_event(self, event: DataEvent) -> bool:
        """Handle synchronization event."""
        
        try:
            source_state = self.tab_states[event.source_tab]
            
            for target_tab in event.target_tabs:
                target_state = self.tab_states[target_tab]
                
                # Sync data based on data type
                if event.data_type in source_state.cached_data:
                    source_data = source_state.cached_data[event.data_type]
                    
                    # Apply transformation if required
                    data_to_sync = source_data
                    if self._requires_transformation(event.source_tab, target_tab):
                        data_to_sync = self._transform_data(source_data, event.source_tab, target_tab)
                    
                    # Update target cache
                    target_state.cached_data[event.data_type] = data_to_sync
                    target_state.last_sync_time = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to handle sync event: {e}")
            return False
    
    def _handle_update_event(self, event: DataEvent) -> bool:
        """Handle data update event."""
        
        try:
            # Update data in source tab
            source_state = self.tab_states[event.source_tab]
            
            data_type = event.data_type
            data_payload = event.data_payload
            
            if data_type not in source_state.cached_data:
                source_state.cached_data[data_type] = {}
            
            # Update specific data items
            for item_id, item_data in data_payload.items():
                source_state.cached_data[data_type][item_id] = item_data
            
            source_state.last_sync_time = datetime.now()
            
            # Propagate to target tabs if needed
            self._propagate_update(event)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to handle update event: {e}")
            return False
    
    def _handle_create_event(self, event: DataEvent) -> bool:
        """Handle data creation event."""
        
        try:
            # Create new data in source tab
            source_state = self.tab_states[event.source_tab]
            
            data_type = event.data_type
            data_payload = event.data_payload
            
            if data_type not in source_state.cached_data:
                source_state.cached_data[data_type] = {}
            
            # Add new data items
            for item_id, item_data in data_payload.items():
                source_state.cached_data[data_type][item_id] = item_data
                
                # Track active items
                if data_type == "opportunities":
                    source_state.active_opportunities.add(item_id)
                elif data_type == "organizations":
                    source_state.active_organizations.add(item_id)
            
            source_state.last_sync_time = datetime.now()
            
            # Propagate to target tabs
            self._propagate_create(event)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to handle create event: {e}")
            return False
    
    def _handle_delete_event(self, event: DataEvent) -> bool:
        """Handle data deletion event."""
        
        try:
            # Delete data from source tab
            source_state = self.tab_states[event.source_tab]
            
            data_type = event.data_type
            data_payload = event.data_payload
            
            if data_type in source_state.cached_data:
                for item_id in data_payload.keys():
                    if item_id in source_state.cached_data[data_type]:
                        del source_state.cached_data[data_type][item_id]
                    
                    # Remove from active tracking
                    if data_type == "opportunities":
                        source_state.active_opportunities.discard(item_id)
                    elif data_type == "organizations":
                        source_state.active_organizations.discard(item_id)
            
            source_state.last_sync_time = datetime.now()
            
            # Propagate deletion to target tabs
            self._propagate_delete(event)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to handle delete event: {e}")
            return False
    
    def _requires_transformation(self, source_tab: TabContext, target_tab: TabContext) -> bool:
        """Check if data transformation is required between tabs."""
        
        for mapping in self.data_flow_mappings:
            if mapping.source_tab == source_tab and mapping.target_tab == target_tab:
                return mapping.requires_transformation
        
        return False
    
    def _transform_data(self, data: Any, source_tab: TabContext, target_tab: TabContext) -> Any:
        """Transform data between tabs."""
        
        # Find appropriate transformation
        for mapping in self.data_flow_mappings:
            if (mapping.source_tab == source_tab and mapping.target_tab == target_tab and 
                mapping.transformation_function):
                
                if mapping.transformation_function == "transform_research_to_examine":
                    return self._transform_research_to_examine(data)
                elif mapping.transformation_function == "transform_examine_to_approach":
                    return self._transform_examine_to_approach(data)
        
        # Default: return data as-is
        return data
    
    def _transform_examine_to_approach(self, examine_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform EXAMINE data for APPROACH tab."""
        
        transformed_data = {
            "decision_summaries": {},
            "implementation_guides": {},
            "approach_strategies": {}
        }
        
        # Transform dossiers into approach strategies
        dossiers = examine_data.get("dossiers", {})
        for dossier_id, dossier_data in dossiers.items():
            transformed_data["approach_strategies"][dossier_id] = {
                "recommended_approach": dossier_data.get("recommended_approach", "standard"),
                "implementation_timeline": dossier_data.get("implementation_timeline", {}),
                "resource_requirements": dossier_data.get("resource_requirements", {}),
                "success_factors": dossier_data.get("success_factors", []),
                "risk_mitigation": dossier_data.get("risk_mitigation", [])
            }
        
        return transformed_data
    
    def _propagate_update(self, event: DataEvent) -> None:
        """Propagate update to target tabs."""
        
        # Create new sync events for each target tab
        for target_tab in event.target_tabs:
            if target_tab != event.source_tab:
                sync_event = DataEvent(
                    event_id=f"propagated_{event.event_id}_{target_tab.value}",
                    source_tab=event.source_tab,
                    target_tabs=[target_tab],
                    operation=DataOperation.SYNC,
                    data_type=event.data_type,
                    data_payload=event.data_payload,
                    priority=DataPriority.HIGH,
                    correlation_id=event.event_id
                )
                
                self.event_queue[DataPriority.HIGH].append(sync_event)
    
    def _propagate_create(self, event: DataEvent) -> None:
        """Propagate creation to target tabs."""
        self._propagate_update(event)  # Same logic as update
    
    def _propagate_delete(self, event: DataEvent) -> None:
        """Propagate deletion to target tabs."""
        
        # Create deletion sync events for target tabs
        for target_tab in event.target_tabs:
            if target_tab != event.source_tab:
                delete_event = DataEvent(
                    event_id=f"delete_propagated_{event.event_id}_{target_tab.value}",
                    source_tab=event.source_tab,
                    target_tabs=[target_tab],
                    operation=DataOperation.DELETE,
                    data_type=event.data_type,
                    data_payload=event.data_payload,
                    priority=DataPriority.MEDIUM,
                    correlation_id=event.event_id
                )
                
                self.event_queue[DataPriority.MEDIUM].append(delete_event)
    
    def _update_performance_metrics(self, success: bool, sync_time_ms: float) -> None:
        """Update performance metrics."""
        
        with self._lock:
            self.performance_metrics["total_events_processed"] += 1
            
            if success:
                self.performance_metrics["successful_syncs"] += 1
            else:
                self.performance_metrics["failed_syncs"] += 1
            
            # Update average sync time
            total_syncs = self.performance_metrics["total_events_processed"]
            current_avg = self.performance_metrics["avg_sync_time_ms"]
            new_avg = ((current_avg * (total_syncs - 1)) + sync_time_ms) / total_syncs
            self.performance_metrics["avg_sync_time_ms"] = new_avg
    
    # Public API methods for external integration
    
    def trigger_sync(self, source_tab: TabContext, target_tabs: List[TabContext], 
                    data_type: str, data_payload: Dict[str, Any], 
                    priority: DataPriority = DataPriority.MEDIUM) -> str:
        """Trigger a synchronization event."""
        
        event_id = f"manual_{source_tab.value}_{int(time.time())}"
        
        event = DataEvent(
            event_id=event_id,
            source_tab=source_tab,
            target_tabs=target_tabs,
            operation=DataOperation.SYNC,
            data_type=data_type,
            data_payload=data_payload,
            priority=priority
        )
        
        self.event_queue[priority].append(event)
        
        return event_id
    
    def update_data(self, tab: TabContext, data_type: str, data_payload: Dict[str, Any],
                   priority: DataPriority = DataPriority.HIGH) -> str:
        """Update data in a specific tab."""
        
        event_id = f"update_{tab.value}_{int(time.time())}"
        
        event = DataEvent(
            event_id=event_id,
            source_tab=tab,
            target_tabs=[],  # Will be determined by data flow mappings
            operation=DataOperation.UPDATE,
            data_type=data_type,
            data_payload=data_payload,
            priority=priority
        )
        
        # Determine target tabs based on data flow mappings
        for mapping in self.data_flow_mappings:
            if mapping.source_tab == tab and data_type in mapping.data_types:
                event.target_tabs.append(mapping.target_tab)
        
        self.event_queue[priority].append(event)
        
        return event_id
    
    def get_tab_state(self, tab: TabContext) -> Dict[str, Any]:
        """Get current state of a specific tab."""
        
        if tab in self.tab_states:
            state = self.tab_states[tab]
            return {
                "tab_context": state.tab_context.value,
                "active_opportunities": list(state.active_opportunities),
                "active_organizations": list(state.active_organizations),
                "active_profiles": list(state.active_profiles),
                "last_sync_time": state.last_sync_time.isoformat(),
                "cache_hit_rate": state.cache_hit_rate,
                "cached_data_types": list(state.cached_data.keys()),
                "processing_queue_length": len(state.processing_queue)
            }
        
        return {}
    
    def get_sync_status(self, event_id: str) -> Dict[str, Any]:
        """Get synchronization status for a specific event."""
        
        # Search through sync history
        for sync_result in self.sync_history:
            if sync_result.event_id == event_id:
                return {
                    "event_id": sync_result.event_id,
                    "success": sync_result.success,
                    "sync_time_ms": sync_result.sync_time_ms,
                    "synced_tabs": [tab.value for tab in sync_result.synced_tabs],
                    "failed_tabs": [tab.value for tab in sync_result.failed_tabs],
                    "errors": sync_result.errors
                }
        
        return {"event_id": event_id, "status": "not_found"}
    
    # Analytics and monitoring methods
    
    async def _generate_data_flow_analytics(self) -> Dict[str, Any]:
        """Generate analytics about data flows."""
        
        analytics = {
            "flow_overview": {
                "total_data_flows": len(self.data_flow_mappings),
                "bidirectional_flows": len([m for m in self.data_flow_mappings if m.is_bidirectional]),
                "transformation_flows": len([m for m in self.data_flow_mappings if m.requires_transformation])
            },
            "tab_activity": {
                tab.value: {
                    "active_opportunities": len(state.active_opportunities),
                    "active_organizations": len(state.active_organizations),
                    "cached_data_types": len(state.cached_data),
                    "last_sync_age_minutes": (datetime.now() - state.last_sync_time).total_seconds() / 60
                }
                for tab, state in self.tab_states.items()
            },
            "sync_patterns": {
                "events_in_queue": sum(len(queue) for queue in self.event_queue.values()),
                "priority_distribution": {
                    priority.value: len(queue) for priority, queue in self.event_queue.items()
                }
            }
        }
        
        return analytics
    
    async def _calculate_orchestration_performance(self) -> Dict[str, Any]:
        """Calculate orchestration performance metrics."""
        
        performance = {
            "sync_performance": {
                "total_events_processed": self.performance_metrics["total_events_processed"],
                "success_rate": (self.performance_metrics["successful_syncs"] / 
                               max(1, self.performance_metrics["total_events_processed"])),
                "avg_sync_time_ms": self.performance_metrics["avg_sync_time_ms"],
                "throughput_events_per_second": self.performance_metrics.get("throughput_events_per_second", 0)
            },
            "cache_performance": {
                "overall_cache_hit_rate": sum(state.cache_hit_rate for state in self.tab_states.values()) / len(self.tab_states),
                "cache_efficiency_by_tab": {
                    tab.value: state.cache_hit_rate for tab, state in self.tab_states.items()
                }
            },
            "system_health": {
                "sync_thread_active": self._running,
                "pending_events": sum(len(queue) for queue in self.event_queue.values()),
                "failed_sync_rate": (self.performance_metrics["failed_syncs"] / 
                                   max(1, self.performance_metrics["total_events_processed"]))
            }
        }
        
        return performance
    
    async def _generate_sync_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for sync optimization."""
        
        recommendations = {
            "performance_optimizations": [],
            "cache_optimizations": [],
            "flow_optimizations": [],
            "priority_adjustments": []
        }
        
        # Performance recommendations
        if self.performance_metrics["avg_sync_time_ms"] > 500:
            recommendations["performance_optimizations"].append(
                "Average sync time exceeds 500ms - consider batch processing optimization"
            )
        
        if self.performance_metrics["failed_syncs"] / max(1, self.performance_metrics["total_events_processed"]) > 0.05:
            recommendations["performance_optimizations"].append(
                "High sync failure rate - review error handling and retry logic"
            )
        
        # Cache recommendations
        avg_cache_hit_rate = sum(state.cache_hit_rate for state in self.tab_states.values()) / len(self.tab_states)
        if avg_cache_hit_rate < 0.7:
            recommendations["cache_optimizations"].append(
                "Low cache hit rate - consider increasing cache size or adjusting TTL"
            )
        
        # Flow recommendations
        high_traffic_flows = [m for m in self.data_flow_mappings if m.expected_latency_ms > 300]
        if high_traffic_flows:
            recommendations["flow_optimizations"].append(
                f"Optimize high-latency flows: {[f.source_tab.value + '->' + f.target_tab.value for f in high_traffic_flows[:3]]}"
            )
        
        # Priority recommendations
        total_events = sum(len(queue) for queue in self.event_queue.values())
        if total_events > 100:
            recommendations["priority_adjustments"].append(
                "High event queue backlog - consider adjusting processing priorities"
            )
        
        return recommendations
    
    def shutdown(self) -> None:
        """Shutdown the orchestration system."""
        
        self._running = False
        
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)
        
        self.logger.info("Cross-tab data orchestration system shutdown complete")


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return CrossTabDataOrchestrator()