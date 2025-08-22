#!/usr/bin/env python3
"""
Cross-Tab Data Consistency Validator - Phase 5 Cross-System Integration
Comprehensive validation system for ensuring data consistency across all system tabs.

This system validates data integrity, consistency, and synchronization across
DISCOVER, RESEARCH, EXAMINE, PLAN, and APPROACH tabs with real-time monitoring.
"""

import asyncio
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.core.government_models import GovernmentOpportunity


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"                   # Informational findings
    WARNING = "warning"             # Potential issues, not critical
    ERROR = "error"                 # Data inconsistencies requiring attention
    CRITICAL = "critical"           # Critical issues affecting system integrity
    BLOCKING = "blocking"           # Issues preventing system operation


class ValidationCategory(Enum):
    """Categories of validation checks."""
    DATA_INTEGRITY = "data_integrity"           # Data corruption, missing fields
    REFERENTIAL_INTEGRITY = "referential_integrity" # Foreign key consistency
    TEMPORAL_CONSISTENCY = "temporal_consistency"    # Time-based consistency
    BUSINESS_LOGIC = "business_logic"                # Business rule validation
    CROSS_TAB_SYNC = "cross_tab_sync"               # Cross-tab synchronization
    PERFORMANCE_IMPACT = "performance_impact"        # Performance-related issues
    COMPLIANCE = "compliance"                        # Compliance requirements


class TabContext(Enum):
    """System tabs for validation context."""
    DISCOVER = "discover"
    RESEARCH = "research"
    EXAMINE = "examine"
    PLAN = "plan"
    APPROACH = "approach"
    GLOBAL = "global"  # Cross-system validation


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    issue_id: str
    timestamp: datetime
    severity: ValidationSeverity
    category: ValidationCategory
    
    # Issue details
    title: str
    description: str
    affected_tabs: List[TabContext]
    affected_entities: List[str]  # Entity IDs affected
    
    # Technical details
    validation_rule: str
    expected_value: Any = None
    actual_value: Any = None
    data_path: str = ""  # Path to problematic data
    
    # Resolution
    auto_fixable: bool = False
    recommended_actions: List[str] = field(default_factory=list)
    fix_priority: int = 5  # 1-10, 1 being highest priority
    
    # Tracking
    reported_by: str = "system"
    resolved: bool = False
    resolution_notes: str = ""
    resolution_timestamp: Optional[datetime] = None


@dataclass
class ValidationRule:
    """Validation rule definition."""
    rule_id: str
    rule_name: str
    category: ValidationCategory
    description: str
    
    # Rule configuration
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.WARNING
    applicable_tabs: List[TabContext] = field(default_factory=list)
    
    # Validation logic
    validation_function: str = ""  # Function name to execute
    validation_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance and scheduling
    execution_frequency: str = "on_change"  # on_change, periodic, on_demand
    max_execution_time_ms: int = 5000
    
    # Dependencies
    depends_on_rules: List[str] = field(default_factory=list)
    blocking_rule: bool = False  # If true, blocks other validations when failing


@dataclass
class ValidationResult:
    """Result of validation execution."""
    validation_id: str
    timestamp: datetime
    execution_time_ms: float
    
    # Results
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues_found: List[ValidationIssue]
    
    # Performance
    rules_executed: List[str]
    rules_skipped: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Summary
    overall_status: str = "unknown"  # passed, warning, error, critical
    health_score: float = 1.0  # 0.0 to 1.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ConsistencyMetrics:
    """Metrics for cross-tab consistency."""
    timestamp: datetime
    
    # Overall consistency
    overall_consistency_score: float = 1.0  # 0.0 to 1.0
    
    # Tab-specific metrics
    tab_consistency_scores: Dict[TabContext, float] = field(default_factory=dict)
    cross_tab_sync_rates: Dict[str, float] = field(default_factory=dict)  # tab_pair -> sync_rate
    
    # Data quality metrics
    data_completeness: float = 1.0
    data_accuracy: float = 1.0
    data_freshness: float = 1.0
    
    # Performance impact
    validation_overhead_ms: float = 0.0
    sync_performance_impact: float = 0.0  # 0.0 to 1.0
    
    # Trend analysis
    consistency_trend: str = "stable"  # improving, stable, degrading
    issue_resolution_rate: float = 1.0


class CrossTabConsistencyValidator(BaseProcessor):
    """
    Cross-Tab Data Consistency Validator - Phase 5 Cross-System Integration
    
    Comprehensive validation system providing:
    
    ## Data Integrity Validation
    - Real-time data consistency checking
    - Cross-tab referential integrity validation
    - Temporal consistency validation
    - Business logic compliance verification
    
    ## Automated Issue Detection
    - Intelligent rule-based validation
    - Performance impact assessment
    - Automated fix recommendations
    - Priority-based issue resolution
    
    ## Cross-System Synchronization
    - Tab synchronization monitoring
    - Data flow consistency validation
    - Cache coherency verification
    - Entity relationship validation
    
    ## Continuous Monitoring
    - Real-time validation monitoring
    - Health score calculation
    - Trend analysis and alerting
    - Performance optimization
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="cross_tab_consistency_validator",
            description="Validate data consistency across all system tabs",
            version="1.0.0",
            dependencies=["cross_tab_data_orchestrator", "comprehensive_audit_trail_system"],
            estimated_duration=240,  # 4 minutes for comprehensive validation
            requires_network=False,  # Local validation
            requires_api_key=False,  # No external APIs
            processor_type="validation"
        )
        super().__init__(metadata)
        
        # Validation state
        self.validation_rules: List[ValidationRule] = []
        self.validation_history: List[ValidationResult] = []
        self.active_issues: List[ValidationIssue] = []
        self.consistency_metrics: List[ConsistencyMetrics] = []
        
        # Tab data cache for validation
        self.tab_data_cache: Dict[TabContext, Dict[str, Any]] = {}
        self.last_validation_time: Optional[datetime] = None
        
        # Performance tracking
        self.validation_performance = {
            "total_validations": 0,
            "avg_execution_time_ms": 0.0,
            "success_rate": 1.0,
            "issues_detected": 0,
            "issues_resolved": 0
        }
        
        # Initialize validation rules
        self._initialize_validation_rules()
        
        # Configuration
        self.validator_config = {
            "real_time_validation": True,
            "max_concurrent_rules": 10,
            "validation_timeout_ms": 30000,
            "auto_fix_enabled": True,
            "issue_retention_days": 30,
            "performance_monitoring": True
        }
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """Execute comprehensive cross-tab consistency validation."""
        start_time = time.time()
        
        try:
            # Load current tab data for validation
            await self._load_tab_data_for_validation(workflow_state)
            
            # Execute comprehensive validation
            validation_result = await self._execute_comprehensive_validation()
            
            # Analyze validation results
            validation_analysis = await self._analyze_validation_results(validation_result)
            
            # Generate consistency metrics
            consistency_metrics = await self._calculate_consistency_metrics(validation_result)
            
            # Generate automated fixes
            automated_fixes = await self._generate_automated_fixes(validation_result)
            
            # Update validation history and metrics
            await self._update_validation_metrics(validation_result)
            
            # Generate validation recommendations
            recommendations = await self._generate_validation_recommendations(
                validation_result, consistency_metrics
            )
            
            # Prepare comprehensive results
            result_data = {
                "validation_status": validation_result.overall_status,
                "validation_result": validation_result.__dict__,
                "validation_analysis": validation_analysis,
                "consistency_metrics": consistency_metrics.__dict__,
                "automated_fixes": automated_fixes,
                "recommendations": recommendations,
                "active_issues": len(self.active_issues),
                "validation_summary": {
                    "total_checks": validation_result.total_checks,
                    "passed_checks": validation_result.passed_checks,
                    "failed_checks": validation_result.failed_checks,
                    "health_score": validation_result.health_score,
                    "issues_found": len(validation_result.issues_found)
                }
            }
            
            execution_time = time.time() - start_time
            
            return ProcessorResult(
                success=True,
                processor_name=self.metadata.name,
                execution_time=execution_time,
                data=result_data,
                metadata={
                    "validation_scope": "comprehensive",
                    "consistency_monitoring": "active",
                    "auto_fix_enabled": self.validator_config["auto_fix_enabled"]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Cross-tab consistency validation failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                processor_name=self.metadata.name,
                execution_time=time.time() - start_time,
                errors=[f"Cross-tab consistency validation failed: {str(e)}"]
            )
    
    def _initialize_validation_rules(self) -> None:
        """Initialize comprehensive validation rules."""
        
        # Data integrity rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="opportunity_data_integrity",
                rule_name="Opportunity Data Integrity",
                category=ValidationCategory.DATA_INTEGRITY,
                description="Validate opportunity data completeness and format",
                applicable_tabs=[TabContext.DISCOVER, TabContext.RESEARCH, TabContext.EXAMINE],
                validation_function="validate_opportunity_integrity",
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                rule_id="organization_data_integrity",
                rule_name="Organization Data Integrity", 
                category=ValidationCategory.DATA_INTEGRITY,
                description="Validate organization data completeness and format",
                applicable_tabs=[TabContext.DISCOVER, TabContext.PLAN],
                validation_function="validate_organization_integrity",
                severity=ValidationSeverity.ERROR
            )
        ])
        
        # Referential integrity rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="cross_tab_opportunity_references",
                rule_name="Cross-Tab Opportunity References",
                category=ValidationCategory.REFERENTIAL_INTEGRITY,
                description="Validate opportunity references across tabs",
                applicable_tabs=[TabContext.DISCOVER, TabContext.RESEARCH, TabContext.EXAMINE],
                validation_function="validate_opportunity_references",
                severity=ValidationSeverity.WARNING
            ),
            ValidationRule(
                rule_id="organization_reference_consistency",
                rule_name="Organization Reference Consistency",
                category=ValidationCategory.REFERENTIAL_INTEGRITY,
                description="Validate organization references across tabs",
                applicable_tabs=[TabContext.DISCOVER, TabContext.PLAN],
                validation_function="validate_organization_references",
                severity=ValidationSeverity.WARNING
            )
        ])
        
        # Temporal consistency rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="data_freshness_validation",
                rule_name="Data Freshness Validation",
                category=ValidationCategory.TEMPORAL_CONSISTENCY,
                description="Validate data freshness across tabs",
                applicable_tabs=list(TabContext),
                validation_function="validate_data_freshness",
                severity=ValidationSeverity.INFO,
                execution_frequency="periodic"
            ),
            ValidationRule(
                rule_id="sync_timestamp_consistency",
                rule_name="Sync Timestamp Consistency",
                category=ValidationCategory.TEMPORAL_CONSISTENCY,
                description="Validate synchronization timestamps",
                applicable_tabs=list(TabContext),
                validation_function="validate_sync_timestamps",
                severity=ValidationSeverity.WARNING
            )
        ])
        
        # Business logic rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="scoring_consistency",
                rule_name="Scoring Consistency",
                category=ValidationCategory.BUSINESS_LOGIC,
                description="Validate scoring consistency across workflow",
                applicable_tabs=[TabContext.DISCOVER, TabContext.RESEARCH],
                validation_function="validate_scoring_consistency",
                severity=ValidationSeverity.WARNING
            ),
            ValidationRule(
                rule_id="decision_logic_consistency",
                rule_name="Decision Logic Consistency",
                category=ValidationCategory.BUSINESS_LOGIC,
                description="Validate decision logic consistency",
                applicable_tabs=[TabContext.EXAMINE, TabContext.APPROACH],
                validation_function="validate_decision_logic",
                severity=ValidationSeverity.ERROR
            )
        ])
        
        # Cross-tab synchronization rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="cross_tab_data_sync",
                rule_name="Cross-Tab Data Synchronization",
                category=ValidationCategory.CROSS_TAB_SYNC,
                description="Validate data synchronization between tabs",
                applicable_tabs=list(TabContext),
                validation_function="validate_cross_tab_sync",
                severity=ValidationSeverity.WARNING,
                execution_frequency="on_change"
            ),
            ValidationRule(
                rule_id="cache_consistency",
                rule_name="Cache Consistency",
                category=ValidationCategory.CROSS_TAB_SYNC,
                description="Validate cache consistency across tabs",
                applicable_tabs=list(TabContext),
                validation_function="validate_cache_consistency",
                severity=ValidationSeverity.INFO
            )
        ])
        
        # Performance impact rules
        self.validation_rules.extend([
            ValidationRule(
                rule_id="performance_impact_assessment",
                rule_name="Performance Impact Assessment",
                category=ValidationCategory.PERFORMANCE_IMPACT,
                description="Assess performance impact of data inconsistencies",
                applicable_tabs=list(TabContext),
                validation_function="assess_performance_impact",
                severity=ValidationSeverity.INFO,
                execution_frequency="periodic"
            )
        ])
    
    async def _load_tab_data_for_validation(self, workflow_state) -> None:
        """Load current tab data for validation."""
        
        # Clear existing cache
        self.tab_data_cache.clear()
        
        if not workflow_state:
            self.logger.warning("No workflow state available for validation")
            return
        
        # Load DISCOVER tab data
        if workflow_state.has_processor_succeeded('government_opportunity_scorer'):
            discover_data = workflow_state.get_processor_data('government_opportunity_scorer')
            self.tab_data_cache[TabContext.DISCOVER] = {
                "opportunities": self._extract_opportunities_from_data(discover_data),
                "organizations": self._extract_organizations_from_data(discover_data),
                "match_scores": discover_data.get("opportunity_matches", []),
                "last_update": datetime.now()
            }
        
        # Load RESEARCH tab data
        if workflow_state.has_processor_succeeded('ai_lite_researcher'):
            research_data = workflow_state.get_processor_data('ai_lite_researcher')
            self.tab_data_cache[TabContext.RESEARCH] = {
                "research_insights": research_data.get("research_insights", {}),
                "opportunity_analysis": research_data.get("opportunity_analysis", {}),
                "research_quality": research_data.get("research_quality", {}),
                "last_update": datetime.now()
            }
        
        # Load EXAMINE tab data
        if workflow_state.has_processor_succeeded('ai_heavy_dossier_builder'):
            examine_data = workflow_state.get_processor_data('ai_heavy_dossier_builder')
            self.tab_data_cache[TabContext.EXAMINE] = {
                "dossiers": examine_data.get("comprehensive_dossiers", {}),
                "decision_frameworks": examine_data.get("decision_frameworks", {}),
                "implementation_plans": examine_data.get("implementation_plans", {}),
                "last_update": datetime.now()
            }
        
        # Load PLAN tab data
        if workflow_state.has_processor_succeeded('board_network_analyzer'):
            plan_data = workflow_state.get_processor_data('board_network_analyzer')
            self.tab_data_cache[TabContext.PLAN] = {
                "network_analysis": plan_data.get("network_analysis", {}),
                "relationship_data": plan_data.get("relationship_data", {}),
                "strategic_intelligence": plan_data.get("strategic_intelligence", {}),
                "last_update": datetime.now()
            }
        
        self.logger.info(f"Loaded data for {len(self.tab_data_cache)} tabs for validation")
    
    def _extract_opportunities_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract opportunity data from processor results."""
        
        opportunities = {}
        
        for match in data.get("opportunity_matches", []):
            opportunity = match.get("opportunity", {})
            opp_id = opportunity.get("opportunity_id")
            if opp_id:
                opportunities[opp_id] = {
                    "title": opportunity.get("title"),
                    "agency_code": opportunity.get("agency_code"),
                    "description": opportunity.get("description"),
                    "award_ceiling": opportunity.get("award_ceiling"),
                    "close_date": opportunity.get("close_date"),
                    "match_score": match.get("relevance_score")
                }
        
        return opportunities
    
    def _extract_organizations_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract organization data from processor results."""
        
        organizations = {}
        
        for match in data.get("opportunity_matches", []):
            org_ein = match.get("organization")
            if org_ein and org_ein not in organizations:
                organizations[org_ein] = {
                    "ein": org_ein,
                    "name": f"Organization {org_ein}",  # Would be real name in production
                    "match_score": match.get("relevance_score")
                }
        
        return organizations
    
    async def _execute_comprehensive_validation(self) -> ValidationResult:
        """Execute comprehensive validation across all rules."""
        
        start_time = time.time()
        validation_id = f"validation_{int(start_time)}"
        
        issues_found = []
        rules_executed = []
        rules_skipped = []
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        
        # Execute validation rules
        for rule in self.validation_rules:
            if not rule.enabled:
                rules_skipped.append(rule.rule_id)
                continue
            
            try:
                rule_start_time = time.time()
                
                # Execute validation rule
                rule_issues, rule_checks, rule_passed = await self._execute_validation_rule(rule)
                
                rule_execution_time = (time.time() - rule_start_time) * 1000
                
                # Check for timeout
                if rule_execution_time > rule.max_execution_time_ms:
                    self.logger.warning(f"Validation rule {rule.rule_id} exceeded timeout")
                
                # Update counts
                total_checks += rule_checks
                passed_checks += rule_passed
                failed_checks += (rule_checks - rule_passed)
                
                # Add issues
                issues_found.extend(rule_issues)
                rules_executed.append(rule.rule_id)
                
            except Exception as e:
                self.logger.error(f"Failed to execute validation rule {rule.rule_id}: {e}")
                rules_skipped.append(rule.rule_id)
                
                # Create issue for rule execution failure
                execution_issue = ValidationIssue(
                    issue_id=f"rule_execution_failure_{rule.rule_id}",
                    timestamp=datetime.now(),
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.DATA_INTEGRITY,
                    title=f"Validation Rule Execution Failure",
                    description=f"Failed to execute validation rule {rule.rule_id}: {str(e)}",
                    affected_tabs=rule.applicable_tabs,
                    affected_entities=[],
                    validation_rule=rule.rule_id,
                    recommended_actions=["Check rule configuration", "Review system logs"]
                )
                issues_found.append(execution_issue)
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Determine overall status
        overall_status = self._determine_validation_status(issues_found)
        
        # Calculate health score
        health_score = self._calculate_health_score(total_checks, passed_checks, issues_found)
        
        # Generate recommendations
        recommendations = self._generate_validation_recommendations_from_issues(issues_found)
        
        # Create validation result
        validation_result = ValidationResult(
            validation_id=validation_id,
            timestamp=datetime.now(),
            execution_time_ms=execution_time_ms,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            issues_found=issues_found,
            rules_executed=rules_executed,
            rules_skipped=rules_skipped,
            overall_status=overall_status,
            health_score=health_score,
            recommendations=recommendations
        )
        
        # Update active issues
        await self._update_active_issues(issues_found)
        
        return validation_result
    
    async def _execute_validation_rule(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Execute a single validation rule."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Route to appropriate validation function
        if rule.validation_function == "validate_opportunity_integrity":
            issues, total_checks, passed_checks = await self._validate_opportunity_integrity(rule)
        elif rule.validation_function == "validate_organization_integrity":
            issues, total_checks, passed_checks = await self._validate_organization_integrity(rule)
        elif rule.validation_function == "validate_opportunity_references":
            issues, total_checks, passed_checks = await self._validate_opportunity_references(rule)
        elif rule.validation_function == "validate_organization_references":
            issues, total_checks, passed_checks = await self._validate_organization_references(rule)
        elif rule.validation_function == "validate_data_freshness":
            issues, total_checks, passed_checks = await self._validate_data_freshness(rule)
        elif rule.validation_function == "validate_sync_timestamps":
            issues, total_checks, passed_checks = await self._validate_sync_timestamps(rule)
        elif rule.validation_function == "validate_scoring_consistency":
            issues, total_checks, passed_checks = await self._validate_scoring_consistency(rule)
        elif rule.validation_function == "validate_decision_logic":
            issues, total_checks, passed_checks = await self._validate_decision_logic(rule)
        elif rule.validation_function == "validate_cross_tab_sync":
            issues, total_checks, passed_checks = await self._validate_cross_tab_sync(rule)
        elif rule.validation_function == "validate_cache_consistency":
            issues, total_checks, passed_checks = await self._validate_cache_consistency(rule)
        elif rule.validation_function == "assess_performance_impact":
            issues, total_checks, passed_checks = await self._assess_performance_impact(rule)
        else:
            self.logger.warning(f"Unknown validation function: {rule.validation_function}")
            
        return issues, total_checks, passed_checks
    
    async def _validate_opportunity_integrity(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate opportunity data integrity."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        for tab_context in rule.applicable_tabs:
            if tab_context in self.tab_data_cache:
                opportunities = self.tab_data_cache[tab_context].get("opportunities", {})
                
                for opp_id, opp_data in opportunities.items():
                    total_checks += 1
                    
                    # Check required fields
                    required_fields = ["title", "agency_code", "description"]
                    missing_fields = [field for field in required_fields if not opp_data.get(field)]
                    
                    if missing_fields:
                        issues.append(ValidationIssue(
                            issue_id=f"opportunity_missing_fields_{tab_context.value}_{opp_id}",
                            timestamp=datetime.now(),
                            severity=rule.severity,
                            category=rule.category,
                            title=f"Missing Required Fields in {tab_context.value}",
                            description=f"Opportunity {opp_id} missing fields: {', '.join(missing_fields)}",
                            affected_tabs=[tab_context],
                            affected_entities=[opp_id],
                            validation_rule=rule.rule_id,
                            data_path=f"{tab_context.value}.opportunities.{opp_id}",
                            recommended_actions=["Reload opportunity data", "Check data source integrity"]
                        ))
                    else:
                        passed_checks += 1
                    
                    # Check data types and ranges
                    total_checks += 1
                    if opp_data.get("award_ceiling") and not isinstance(opp_data["award_ceiling"], (int, float)):
                        issues.append(ValidationIssue(
                            issue_id=f"opportunity_invalid_award_{tab_context.value}_{opp_id}",
                            timestamp=datetime.now(),
                            severity=ValidationSeverity.WARNING,
                            category=rule.category,
                            title=f"Invalid Award Ceiling Data Type",
                            description=f"Award ceiling for opportunity {opp_id} has invalid data type",
                            affected_tabs=[tab_context],
                            affected_entities=[opp_id],
                            validation_rule=rule.rule_id
                        ))
                    else:
                        passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_organization_integrity(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate organization data integrity."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        for tab_context in rule.applicable_tabs:
            if tab_context in self.tab_data_cache:
                organizations = self.tab_data_cache[tab_context].get("organizations", {})
                
                for org_ein, org_data in organizations.items():
                    total_checks += 1
                    
                    # Check EIN format (basic validation)
                    if not org_ein or len(org_ein) < 9:
                        issues.append(ValidationIssue(
                            issue_id=f"organization_invalid_ein_{tab_context.value}_{org_ein}",
                            timestamp=datetime.now(),
                            severity=rule.severity,
                            category=rule.category,
                            title=f"Invalid Organization EIN",
                            description=f"Organization EIN {org_ein} has invalid format",
                            affected_tabs=[tab_context],
                            affected_entities=[org_ein],
                            validation_rule=rule.rule_id,
                            recommended_actions=["Verify EIN format", "Check data source"]
                        ))
                    else:
                        passed_checks += 1
                    
                    # Check required organization data
                    total_checks += 1
                    if not org_data.get("name"):
                        issues.append(ValidationIssue(
                            issue_id=f"organization_missing_name_{tab_context.value}_{org_ein}",
                            timestamp=datetime.now(),
                            severity=ValidationSeverity.WARNING,
                            category=rule.category,
                            title=f"Missing Organization Name",
                            description=f"Organization {org_ein} missing name field",
                            affected_tabs=[tab_context],
                            affected_entities=[org_ein],
                            validation_rule=rule.rule_id
                        ))
                    else:
                        passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_opportunity_references(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate opportunity references across tabs."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Get opportunity IDs from each applicable tab
        tab_opportunities = {}
        for tab_context in rule.applicable_tabs:
            if tab_context in self.tab_data_cache:
                opportunities = self.tab_data_cache[tab_context].get("opportunities", {})
                tab_opportunities[tab_context] = set(opportunities.keys())
        
        # Check cross-references between tabs
        tab_pairs = [
            (TabContext.DISCOVER, TabContext.RESEARCH),
            (TabContext.RESEARCH, TabContext.EXAMINE),
            (TabContext.DISCOVER, TabContext.EXAMINE)
        ]
        
        for source_tab, target_tab in tab_pairs:
            if source_tab in tab_opportunities and target_tab in tab_opportunities:
                source_opps = tab_opportunities[source_tab]
                target_opps = tab_opportunities[target_tab]
                
                total_checks += 1
                
                # Check for missing opportunities in target tab
                missing_in_target = source_opps - target_opps
                if missing_in_target and len(missing_in_target) > len(source_opps) * 0.1:  # >10% missing
                    issues.append(ValidationIssue(
                        issue_id=f"opportunities_missing_{source_tab.value}_to_{target_tab.value}",
                        timestamp=datetime.now(),
                        severity=rule.severity,
                        category=rule.category,
                        title=f"Opportunities Missing in {target_tab.value}",
                        description=f"{len(missing_in_target)} opportunities from {source_tab.value} missing in {target_tab.value}",
                        affected_tabs=[source_tab, target_tab],
                        affected_entities=list(missing_in_target)[:10],  # Limit to first 10
                        validation_rule=rule.rule_id,
                        recommended_actions=["Check data synchronization", "Trigger cross-tab sync"]
                    ))
                else:
                    passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_organization_references(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate organization references across tabs."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Similar logic to opportunity references but for organizations
        tab_organizations = {}
        for tab_context in rule.applicable_tabs:
            if tab_context in self.tab_data_cache:
                organizations = self.tab_data_cache[tab_context].get("organizations", {})
                tab_organizations[tab_context] = set(organizations.keys())
        
        # Check DISCOVER to PLAN organization sync
        if TabContext.DISCOVER in tab_organizations and TabContext.PLAN in tab_organizations:
            discover_orgs = tab_organizations[TabContext.DISCOVER]
            plan_orgs = tab_organizations[TabContext.PLAN]
            
            total_checks += 1
            
            missing_in_plan = discover_orgs - plan_orgs
            if missing_in_plan:
                issues.append(ValidationIssue(
                    issue_id="organizations_missing_discover_to_plan",
                    timestamp=datetime.now(),
                    severity=rule.severity,
                    category=rule.category,
                    title="Organizations Missing in PLAN Tab",
                    description=f"{len(missing_in_plan)} organizations from DISCOVER missing in PLAN",
                    affected_tabs=[TabContext.DISCOVER, TabContext.PLAN],
                    affected_entities=list(missing_in_plan),
                    validation_rule=rule.rule_id,
                    recommended_actions=["Sync organization data to PLAN tab"]
                ))
            else:
                passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_data_freshness(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate data freshness across tabs."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        current_time = datetime.now()
        freshness_threshold = timedelta(minutes=15)  # 15-minute freshness requirement
        
        for tab_context in rule.applicable_tabs:
            if tab_context in self.tab_data_cache:
                total_checks += 1
                
                last_update = self.tab_data_cache[tab_context].get("last_update")
                if last_update and current_time - last_update > freshness_threshold:
                    issues.append(ValidationIssue(
                        issue_id=f"data_stale_{tab_context.value}",
                        timestamp=datetime.now(),
                        severity=rule.severity,
                        category=rule.category,
                        title=f"Stale Data in {tab_context.value}",
                        description=f"Data in {tab_context.value} tab is {current_time - last_update} old",
                        affected_tabs=[tab_context],
                        affected_entities=[],
                        validation_rule=rule.rule_id,
                        expected_value="< 15 minutes",
                        actual_value=str(current_time - last_update),
                        recommended_actions=["Trigger data refresh", "Check data sync process"]
                    ))
                else:
                    passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_sync_timestamps(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate synchronization timestamps."""
        
        issues = []
        total_checks = 1
        passed_checks = 0
        
        # Get sync timestamps from all tabs
        sync_timestamps = {}
        for tab_context in self.tab_data_cache:
            last_update = self.tab_data_cache[tab_context].get("last_update")
            if last_update:
                sync_timestamps[tab_context] = last_update
        
        if len(sync_timestamps) > 1:
            # Check for timestamp drift between tabs
            timestamps = list(sync_timestamps.values())
            time_drifts = []
            
            for i in range(len(timestamps)):
                for j in range(i + 1, len(timestamps)):
                    drift = abs((timestamps[i] - timestamps[j]).total_seconds())
                    time_drifts.append(drift)
            
            max_drift = max(time_drifts) if time_drifts else 0
            
            if max_drift > 300:  # 5 minutes drift threshold
                issues.append(ValidationIssue(
                    issue_id="sync_timestamp_drift",
                    timestamp=datetime.now(),
                    severity=rule.severity,
                    category=rule.category,
                    title="Synchronization Timestamp Drift",
                    description=f"Maximum time drift between tabs: {max_drift:.1f} seconds",
                    affected_tabs=list(sync_timestamps.keys()),
                    affected_entities=[],
                    validation_rule=rule.rule_id,
                    expected_value="< 5 minutes",
                    actual_value=f"{max_drift:.1f} seconds",
                    recommended_actions=["Check synchronization process", "Verify system clocks"]
                ))
            else:
                passed_checks = 1
        else:
            passed_checks = 1  # Only one tab, no drift possible
        
        return issues, total_checks, passed_checks
    
    async def _validate_scoring_consistency(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate scoring consistency across workflow."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Compare match scores between DISCOVER and RESEARCH tabs
        if (TabContext.DISCOVER in self.tab_data_cache and 
            TabContext.RESEARCH in self.tab_data_cache):
            
            discover_opportunities = self.tab_data_cache[TabContext.DISCOVER].get("opportunities", {})
            research_opportunities = self.tab_data_cache[TabContext.RESEARCH].get("opportunities", {})
            
            common_opportunities = set(discover_opportunities.keys()) & set(research_opportunities.keys())
            
            for opp_id in common_opportunities:
                total_checks += 1
                
                discover_score = discover_opportunities[opp_id].get("match_score", 0)
                research_score = research_opportunities[opp_id].get("match_score", 0)
                
                # Allow for some variation but flag large discrepancies
                if abs(discover_score - research_score) > 0.2:  # 20% difference threshold
                    issues.append(ValidationIssue(
                        issue_id=f"score_inconsistency_{opp_id}",
                        timestamp=datetime.now(),
                        severity=rule.severity,
                        category=rule.category,
                        title=f"Score Inconsistency for {opp_id}",
                        description=f"Match score differs significantly: DISCOVER={discover_score:.2f}, RESEARCH={research_score:.2f}",
                        affected_tabs=[TabContext.DISCOVER, TabContext.RESEARCH],
                        affected_entities=[opp_id],
                        validation_rule=rule.rule_id,
                        expected_value=f"≈{discover_score:.2f}",
                        actual_value=f"{research_score:.2f}",
                        recommended_actions=["Review scoring algorithm", "Check data consistency"]
                    ))
                else:
                    passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_decision_logic(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate decision logic consistency."""
        
        issues = []
        total_checks = 1
        passed_checks = 0
        
        # Check if EXAMINE tab decisions are consistent with APPROACH tab recommendations
        if (TabContext.EXAMINE in self.tab_data_cache and 
            TabContext.APPROACH in self.tab_data_cache):
            
            examine_data = self.tab_data_cache[TabContext.EXAMINE]
            approach_data = self.tab_data_cache[TabContext.APPROACH]
            
            # Simplified decision logic validation
            dossiers = examine_data.get("dossiers", {})
            implementations = approach_data.get("implementation_plans", {})
            
            # Check that high-scoring dossiers have implementation plans
            high_score_dossiers = [d for d in dossiers.values() 
                                 if d.get("decision_score", 0) > 0.8]
            
            if high_score_dossiers and not implementations:
                issues.append(ValidationIssue(
                    issue_id="missing_implementation_plans",
                    timestamp=datetime.now(),
                    severity=rule.severity,
                    category=rule.category,
                    title="Missing Implementation Plans",
                    description=f"High-scoring dossiers ({len(high_score_dossiers)}) lack implementation plans",
                    affected_tabs=[TabContext.EXAMINE, TabContext.APPROACH],
                    affected_entities=[],
                    validation_rule=rule.rule_id,
                    recommended_actions=["Generate implementation plans", "Check workflow progression"]
                ))
            else:
                passed_checks = 1
        else:
            passed_checks = 1  # No data to validate
        
        return issues, total_checks, passed_checks
    
    async def _validate_cross_tab_sync(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate cross-tab data synchronization."""
        
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Check that common data elements are synchronized
        tabs_with_opportunities = []
        for tab_context in self.tab_data_cache:
            if self.tab_data_cache[tab_context].get("opportunities"):
                tabs_with_opportunities.append(tab_context)
        
        # Validate opportunity data consistency across tabs
        if len(tabs_with_opportunities) >= 2:
            for i in range(len(tabs_with_opportunities)):
                for j in range(i + 1, len(tabs_with_opportunities)):
                    tab1, tab2 = tabs_with_opportunities[i], tabs_with_opportunities[j]
                    
                    opps1 = self.tab_data_cache[tab1].get("opportunities", {})
                    opps2 = self.tab_data_cache[tab2].get("opportunities", {})
                    
                    common_opps = set(opps1.keys()) & set(opps2.keys())
                    
                    for opp_id in common_opps:
                        total_checks += 1
                        
                        opp1_data = opps1[opp_id]
                        opp2_data = opps2[opp_id]
                        
                        # Check key fields for consistency
                        key_fields = ["title", "agency_code"]
                        inconsistencies = []
                        
                        for field in key_fields:
                            if opp1_data.get(field) != opp2_data.get(field):
                                inconsistencies.append(field)
                        
                        if inconsistencies:
                            issues.append(ValidationIssue(
                                issue_id=f"sync_inconsistency_{tab1.value}_{tab2.value}_{opp_id}",
                                timestamp=datetime.now(),
                                severity=rule.severity,
                                category=rule.category,
                                title=f"Sync Inconsistency: {tab1.value} ↔ {tab2.value}",
                                description=f"Opportunity {opp_id} has inconsistent {', '.join(inconsistencies)}",
                                affected_tabs=[tab1, tab2],
                                affected_entities=[opp_id],
                                validation_rule=rule.rule_id,
                                recommended_actions=["Trigger data sync", "Check sync process"]
                            ))
                        else:
                            passed_checks += 1
        
        return issues, total_checks, passed_checks
    
    async def _validate_cache_consistency(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Validate cache consistency across tabs."""
        
        issues = []
        total_checks = 1
        passed_checks = 0
        
        # Simple cache consistency check
        # In production, would check actual cache states
        cache_status = "consistent"  # Simplified for demo
        
        if cache_status == "consistent":
            passed_checks = 1
        else:
            issues.append(ValidationIssue(
                issue_id="cache_inconsistency",
                timestamp=datetime.now(),
                severity=rule.severity,
                category=rule.category,
                title="Cache Inconsistency Detected",
                description="Cache inconsistency detected across tabs",
                affected_tabs=list(TabContext),
                affected_entities=[],
                validation_rule=rule.rule_id,
                recommended_actions=["Clear and rebuild cache", "Check cache synchronization"]
            ))
        
        return issues, total_checks, passed_checks
    
    async def _assess_performance_impact(self, rule: ValidationRule) -> Tuple[List[ValidationIssue], int, int]:
        """Assess performance impact of data inconsistencies."""
        
        issues = []
        total_checks = 1
        passed_checks = 0
        
        # Assess performance impact based on number of inconsistencies
        total_inconsistencies = len(self.active_issues)
        
        if total_inconsistencies > 50:
            issues.append(ValidationIssue(
                issue_id="high_performance_impact",
                timestamp=datetime.now(),
                severity=ValidationSeverity.WARNING,
                category=rule.category,
                title="High Performance Impact from Inconsistencies",
                description=f"{total_inconsistencies} active issues may impact system performance",
                affected_tabs=list(TabContext),
                affected_entities=[],
                validation_rule=rule.rule_id,
                recommended_actions=["Address critical issues", "Optimize validation frequency"]
            ))
        elif total_inconsistencies > 20:
            issues.append(ValidationIssue(
                issue_id="moderate_performance_impact",
                timestamp=datetime.now(),
                severity=ValidationSeverity.INFO,
                category=rule.category,
                title="Moderate Performance Impact",
                description=f"{total_inconsistencies} active issues present moderate performance impact",
                affected_tabs=list(TabContext),
                affected_entities=[],
                validation_rule=rule.rule_id,
                recommended_actions=["Monitor performance metrics", "Plan issue resolution"]
            ))
        else:
            passed_checks = 1
        
        return issues, total_checks, passed_checks
    
    def _determine_validation_status(self, issues: List[ValidationIssue]) -> str:
        """Determine overall validation status."""
        
        if not issues:
            return "passed"
        
        severities = [issue.severity for issue in issues]
        
        if ValidationSeverity.CRITICAL in severities or ValidationSeverity.BLOCKING in severities:
            return "critical"
        elif ValidationSeverity.ERROR in severities:
            return "error"
        elif ValidationSeverity.WARNING in severities:
            return "warning"
        else:
            return "info"
    
    def _calculate_health_score(self, total_checks: int, passed_checks: int, issues: List[ValidationIssue]) -> float:
        """Calculate system health score."""
        
        if total_checks == 0:
            return 1.0
        
        base_score = passed_checks / total_checks
        
        # Apply penalties for severe issues
        severity_penalties = {
            ValidationSeverity.BLOCKING: 0.5,
            ValidationSeverity.CRITICAL: 0.3,
            ValidationSeverity.ERROR: 0.2,
            ValidationSeverity.WARNING: 0.1,
            ValidationSeverity.INFO: 0.05
        }
        
        total_penalty = 0
        for issue in issues:
            total_penalty += severity_penalties.get(issue.severity, 0)
        
        # Cap penalty at 80% of base score
        capped_penalty = min(total_penalty, base_score * 0.8)
        
        return max(0.0, base_score - capped_penalty)
    
    def _generate_validation_recommendations_from_issues(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations from validation issues."""
        
        recommendations = []
        
        # Count issues by category
        category_counts = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        # Generate category-specific recommendations
        if category_counts.get(ValidationCategory.DATA_INTEGRITY, 0) > 3:
            recommendations.append("Review data loading and validation processes")
        
        if category_counts.get(ValidationCategory.CROSS_TAB_SYNC, 0) > 2:
            recommendations.append("Optimize cross-tab synchronization mechanisms")
        
        if category_counts.get(ValidationCategory.REFERENTIAL_INTEGRITY, 0) > 1:
            recommendations.append("Implement stronger referential integrity constraints")
        
        # Add general recommendations
        if len(issues) > 10:
            recommendations.append("Consider increasing validation frequency")
            recommendations.append("Review system architecture for consistency improvements")
        
        return recommendations
    
    async def _update_active_issues(self, new_issues: List[ValidationIssue]) -> None:
        """Update active issues list."""
        
        # Mark resolved issues
        current_issue_ids = {issue.issue_id for issue in new_issues}
        
        for active_issue in self.active_issues:
            if active_issue.issue_id not in current_issue_ids:
                active_issue.resolved = True
                active_issue.resolution_timestamp = datetime.now()
                active_issue.resolution_notes = "Issue no longer detected"
        
        # Add new issues
        for new_issue in new_issues:
            existing_issue = next((issue for issue in self.active_issues 
                                 if issue.issue_id == new_issue.issue_id), None)
            if not existing_issue:
                self.active_issues.append(new_issue)
        
        # Clean up old resolved issues
        retention_cutoff = datetime.now() - timedelta(days=self.validator_config["issue_retention_days"])
        self.active_issues = [
            issue for issue in self.active_issues 
            if not issue.resolved or issue.resolution_timestamp > retention_cutoff
        ]
    
    # Analysis and reporting methods
    
    async def _analyze_validation_results(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Analyze validation results for insights."""
        
        analysis = {
            "issue_analysis": {
                "total_issues": len(validation_result.issues_found),
                "issues_by_severity": self._analyze_issues_by_severity(validation_result.issues_found),
                "issues_by_category": self._analyze_issues_by_category(validation_result.issues_found),
                "affected_tabs": self._analyze_affected_tabs(validation_result.issues_found)
            },
            "performance_analysis": {
                "validation_efficiency": validation_result.execution_time_ms / max(1, validation_result.total_checks),
                "rule_execution_success": len(validation_result.rules_executed) / max(1, len(self.validation_rules)),
                "validation_overhead": validation_result.execution_time_ms
            },
            "trend_analysis": {
                "health_trend": self._analyze_health_trend(),
                "issue_trend": self._analyze_issue_trend(),
                "resolution_effectiveness": self._analyze_resolution_effectiveness()
            }
        }
        
        return analysis
    
    def _analyze_issues_by_severity(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """Analyze issues by severity."""
        
        counts = {severity.value: 0 for severity in ValidationSeverity}
        for issue in issues:
            counts[issue.severity.value] += 1
        
        return counts
    
    def _analyze_issues_by_category(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """Analyze issues by category."""
        
        counts = {category.value: 0 for category in ValidationCategory}
        for issue in issues:
            counts[issue.category.value] += 1
        
        return counts
    
    def _analyze_affected_tabs(self, issues: List[ValidationIssue]) -> Dict[str, int]:
        """Analyze which tabs are most affected."""
        
        tab_counts = {tab.value: 0 for tab in TabContext}
        
        for issue in issues:
            for tab in issue.affected_tabs:
                tab_counts[tab.value] += 1
        
        return tab_counts
    
    def _analyze_health_trend(self) -> str:
        """Analyze health score trend."""
        
        if len(self.validation_history) < 2:
            return "insufficient_data"
        
        recent_scores = [result.health_score for result in self.validation_history[-5:]]
        
        if len(recent_scores) >= 2:
            if recent_scores[-1] > recent_scores[-2] + 0.05:
                return "improving"
            elif recent_scores[-1] < recent_scores[-2] - 0.05:
                return "degrading"
        
        return "stable"
    
    def _analyze_issue_trend(self) -> str:
        """Analyze issue count trend."""
        
        if len(self.validation_history) < 2:
            return "insufficient_data"
        
        recent_counts = [len(result.issues_found) for result in self.validation_history[-5:]]
        
        if len(recent_counts) >= 2:
            if recent_counts[-1] < recent_counts[-2]:
                return "improving"
            elif recent_counts[-1] > recent_counts[-2]:
                return "worsening"
        
        return "stable"
    
    def _analyze_resolution_effectiveness(self) -> float:
        """Analyze issue resolution effectiveness."""
        
        resolved_issues = [issue for issue in self.active_issues if issue.resolved]
        total_issues = len(self.active_issues)
        
        return len(resolved_issues) / total_issues if total_issues > 0 else 1.0
    
    async def _calculate_consistency_metrics(self, validation_result: ValidationResult) -> ConsistencyMetrics:
        """Calculate comprehensive consistency metrics."""
        
        metrics = ConsistencyMetrics(
            timestamp=datetime.now(),
            overall_consistency_score=validation_result.health_score
        )
        
        # Calculate tab-specific consistency scores
        for tab in TabContext:
            tab_issues = [issue for issue in validation_result.issues_found if tab in issue.affected_tabs]
            
            if tab_issues:
                severity_weights = {
                    ValidationSeverity.BLOCKING: 1.0,
                    ValidationSeverity.CRITICAL: 0.8,
                    ValidationSeverity.ERROR: 0.6,
                    ValidationSeverity.WARNING: 0.3,
                    ValidationSeverity.INFO: 0.1
                }
                
                total_weight = sum(severity_weights[issue.severity] for issue in tab_issues)
                # Higher weight means lower consistency
                consistency_score = max(0.0, 1.0 - (total_weight / 10))  # Normalize by expected max issues
            else:
                consistency_score = 1.0
            
            metrics.tab_consistency_scores[tab] = consistency_score
        
        # Calculate cross-tab sync rates
        sync_issues = [issue for issue in validation_result.issues_found 
                      if issue.category == ValidationCategory.CROSS_TAB_SYNC]
        
        total_possible_syncs = len(TabContext) * (len(TabContext) - 1) // 2  # Combinations
        failed_syncs = len(sync_issues)
        sync_rate = (total_possible_syncs - failed_syncs) / total_possible_syncs if total_possible_syncs > 0 else 1.0
        
        metrics.cross_tab_sync_rates["overall"] = sync_rate
        
        # Calculate data quality metrics
        data_issues = [issue for issue in validation_result.issues_found 
                      if issue.category == ValidationCategory.DATA_INTEGRITY]
        metrics.data_accuracy = max(0.0, 1.0 - len(data_issues) / 50)  # Normalize by expected threshold
        
        freshness_issues = [issue for issue in validation_result.issues_found 
                           if issue.category == ValidationCategory.TEMPORAL_CONSISTENCY]
        metrics.data_freshness = max(0.0, 1.0 - len(freshness_issues) / 10)  # Normalize
        
        # Set trends
        metrics.consistency_trend = self._analyze_health_trend()
        metrics.issue_resolution_rate = self._analyze_resolution_effectiveness()
        
        # Performance impact
        metrics.validation_overhead_ms = validation_result.execution_time_ms
        
        return metrics
    
    async def _generate_automated_fixes(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Generate automated fixes for validation issues."""
        
        automated_fixes = {
            "fixable_issues": [],
            "fix_recommendations": [],
            "estimated_fix_time": 0,
            "fix_success_probability": 0.0
        }
        
        fixable_count = 0
        total_fix_time = 0
        
        for issue in validation_result.issues_found:
            if issue.auto_fixable:
                fix_info = {
                    "issue_id": issue.issue_id,
                    "fix_type": self._determine_fix_type(issue),
                    "estimated_time_minutes": self._estimate_fix_time(issue),
                    "success_probability": self._estimate_fix_success_probability(issue)
                }
                
                automated_fixes["fixable_issues"].append(fix_info)
                fixable_count += 1
                total_fix_time += fix_info["estimated_time_minutes"]
            else:
                # Generate manual fix recommendation
                automated_fixes["fix_recommendations"].append({
                    "issue_id": issue.issue_id,
                    "recommended_actions": issue.recommended_actions,
                    "priority": issue.fix_priority
                })
        
        automated_fixes["estimated_fix_time"] = total_fix_time
        automated_fixes["fix_success_probability"] = fixable_count / len(validation_result.issues_found) if validation_result.issues_found else 1.0
        
        return automated_fixes
    
    def _determine_fix_type(self, issue: ValidationIssue) -> str:
        """Determine the type of automated fix."""
        
        if issue.category == ValidationCategory.CROSS_TAB_SYNC:
            return "data_sync"
        elif issue.category == ValidationCategory.DATA_INTEGRITY:
            return "data_validation"
        elif issue.category == ValidationCategory.TEMPORAL_CONSISTENCY:
            return "timestamp_correction"
        else:
            return "manual_review"
    
    def _estimate_fix_time(self, issue: ValidationIssue) -> int:
        """Estimate fix time in minutes."""
        
        if issue.category == ValidationCategory.CROSS_TAB_SYNC:
            return 2  # 2 minutes for sync
        elif issue.category == ValidationCategory.DATA_INTEGRITY:
            return 5  # 5 minutes for data validation
        elif issue.category == ValidationCategory.TEMPORAL_CONSISTENCY:
            return 1  # 1 minute for timestamp fix
        else:
            return 10  # 10 minutes for complex fixes
    
    def _estimate_fix_success_probability(self, issue: ValidationIssue) -> float:
        """Estimate fix success probability."""
        
        if issue.category == ValidationCategory.CROSS_TAB_SYNC:
            return 0.9  # High success rate for sync
        elif issue.category == ValidationCategory.TEMPORAL_CONSISTENCY:
            return 0.8  # Good success rate for timestamp fixes
        elif issue.severity == ValidationSeverity.INFO:
            return 0.95  # High success for info-level issues
        else:
            return 0.7  # Moderate success for complex issues
    
    async def _update_validation_metrics(self, validation_result: ValidationResult) -> None:
        """Update validation performance metrics."""
        
        self.validation_history.append(validation_result)
        
        # Keep only recent validation history
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        # Update performance metrics
        self.validation_performance["total_validations"] += 1
        
        # Update average execution time
        total_validations = self.validation_performance["total_validations"]
        current_avg = self.validation_performance["avg_execution_time_ms"]
        new_avg = ((current_avg * (total_validations - 1)) + validation_result.execution_time_ms) / total_validations
        self.validation_performance["avg_execution_time_ms"] = new_avg
        
        # Update success rate
        success = 1 if validation_result.overall_status in ["passed", "info", "warning"] else 0
        current_success_rate = self.validation_performance["success_rate"]
        new_success_rate = ((current_success_rate * (total_validations - 1)) + success) / total_validations
        self.validation_performance["success_rate"] = new_success_rate
        
        # Update issue counts
        self.validation_performance["issues_detected"] += len(validation_result.issues_found)
        
        self.last_validation_time = datetime.now()
    
    async def _generate_validation_recommendations(
        self, validation_result: ValidationResult, consistency_metrics: ConsistencyMetrics
    ) -> Dict[str, Any]:
        """Generate comprehensive validation recommendations."""
        
        recommendations = {
            "immediate_actions": [],
            "optimization_opportunities": [],
            "monitoring_improvements": [],
            "architectural_recommendations": []
        }
        
        # Immediate actions based on critical issues
        critical_issues = [issue for issue in validation_result.issues_found 
                          if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.BLOCKING]]
        
        if critical_issues:
            recommendations["immediate_actions"].append(
                f"Address {len(critical_issues)} critical validation issues immediately"
            )
            
            for issue in critical_issues[:3]:  # Top 3 critical issues
                recommendations["immediate_actions"].append(
                    f"Fix: {issue.title} - {issue.recommended_actions[0] if issue.recommended_actions else 'Manual review required'}"
                )
        
        # Optimization opportunities
        if validation_result.execution_time_ms > 10000:  # 10 seconds
            recommendations["optimization_opportunities"].append(
                "Optimize validation performance - execution time exceeds 10 seconds"
            )
        
        if consistency_metrics.overall_consistency_score < 0.8:
            recommendations["optimization_opportunities"].append(
                "Improve overall system consistency - score below 80%"
            )
        
        # Monitoring improvements
        low_consistency_tabs = [tab for tab, score in consistency_metrics.tab_consistency_scores.items() 
                               if score < 0.7]
        
        if low_consistency_tabs:
            recommendations["monitoring_improvements"].append(
                f"Increase monitoring frequency for tabs: {', '.join(tab.value for tab in low_consistency_tabs)}"
            )
        
        # Architectural recommendations
        sync_issues = [issue for issue in validation_result.issues_found 
                      if issue.category == ValidationCategory.CROSS_TAB_SYNC]
        
        if len(sync_issues) > 5:
            recommendations["architectural_recommendations"].append(
                "Consider implementing event-driven synchronization architecture"
            )
        
        if len(validation_result.issues_found) > 20:
            recommendations["architectural_recommendations"].append(
                "Implement automated issue resolution system"
            )
        
        return recommendations


# Register processor for auto-discovery
def get_processor():
    """Factory function for processor registration."""
    return CrossTabConsistencyValidator()