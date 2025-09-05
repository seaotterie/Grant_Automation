"""
Centralized Test Configurations for Catalynx Testing Platform

Provides standardized configuration for testing scenarios, budget controls,
and expected performance benchmarks based on the master test plan.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ProcessorTestConfig:
    """Configuration for individual processor testing"""
    name: str
    category: str  # "data_collection", "analysis", "integration"
    expected_cost_range: Tuple[float, float]  # (min, max)
    expected_duration_seconds: int
    gpt_model: str
    description: str


@dataclass
class TierTestConfig:
    """Configuration for intelligence tier testing"""
    name: str
    price_point: float
    max_cost_budget: float
    expected_duration_minutes: int
    expected_features: List[str]
    success_criteria: Dict[str, Any]


# Standard testing budget controls (from master test plan)
COST_CONTROLS = {
    "max_total_test_cost": 25.00,          # Total budget across all testing
    "max_cost_per_tier": 10.00,            # Limit per intelligence tier test
    "max_cost_per_processor": 2.50,        # Limit per individual processor
    "token_limits": {
        "gpt-5": 5000,                     # Conservative token limits
        "gpt-5-mini": 8000,                # Higher volume for screening
        "gpt-5-nano": 15000,               # Highest volume for basic processing
    },
    "timeout_seconds": 180,                # API timeout protection
    "retry_attempts": 2                    # Limited retry on failures
}

# 4-Stage AI Processing Pipeline Configuration
AI_PIPELINE_STAGES = {
    "PLAN": ProcessorTestConfig(
        name="ai_lite_unified_processor",
        category="analysis",
        expected_cost_range=(0.0002, 0.0008),
        expected_duration_seconds=30,
        gpt_model="gpt-5-nano", 
        description="Cost-effective screening and strategic assessment"
    ),
    "ANALYZE": ProcessorTestConfig(
        name="ai_heavy_light_analyzer", 
        category="analysis",
        expected_cost_range=(0.02, 0.04),
        expected_duration_seconds=60,
        gpt_model="gpt-5-mini",
        description="Enhanced context analysis and competitive positioning"
    ),
    "EXAMINE": ProcessorTestConfig(
        name="ai_heavy_deep_researcher",
        category="analysis", 
        expected_cost_range=(0.08, 0.15),
        expected_duration_seconds=120,
        gpt_model="gpt-5",
        description="Comprehensive research and deep risk analysis"
    ),
    "APPROACH": ProcessorTestConfig(
        name="ai_heavy_researcher",
        category="analysis",
        expected_cost_range=(0.12, 0.20),
        expected_duration_seconds=90,
        gpt_model="gpt-5",
        description="Implementation strategy and detailed approach"
    )
}

# Data Collection Processors Configuration
DATA_COLLECTION_PROCESSORS = [
    ProcessorTestConfig(
        name="bmf_filter",
        category="data_collection",
        expected_cost_range=(0.00, 0.01),
        expected_duration_seconds=15,
        gpt_model="none",
        description="IRS Business Master File filtering with entity integration"
    ),
    ProcessorTestConfig(
        name="propublica_fetch", 
        category="data_collection",
        expected_cost_range=(0.00, 0.01),
        expected_duration_seconds=30,
        gpt_model="none",
        description="990 filing data retrieval with shared analytics"
    ),
    ProcessorTestConfig(
        name="grants_gov_fetch",
        category="data_collection", 
        expected_cost_range=(0.00, 0.02),
        expected_duration_seconds=45,
        gpt_model="none",
        description="Federal grant opportunity discovery with entity organization"
    ),
    ProcessorTestConfig(
        name="usaspending_fetch",
        category="data_collection",
        expected_cost_range=(0.00, 0.02),
        expected_duration_seconds=60,
        gpt_model="none",
        description="Historical federal award analysis with entity structure"
    )
]

# Analysis Processors Configuration
ANALYSIS_PROCESSORS = [
    ProcessorTestConfig(
        name="government_opportunity_scorer",
        category="analysis",
        expected_cost_range=(0.00, 0.01),
        expected_duration_seconds=10,
        gpt_model="none", 
        description="Enhanced scoring with data-driven weights"
    ),
    ProcessorTestConfig(
        name="financial_scorer",
        category="analysis", 
        expected_cost_range=(0.00, 0.01),
        expected_duration_seconds=5,
        gpt_model="none",
        description="Financial health assessment"
    ),
    ProcessorTestConfig(
        name="board_network_analyzer",
        category="analysis",
        expected_cost_range=(0.01, 0.05),
        expected_duration_seconds=30,
        gpt_model="gpt-5-nano",
        description="Strategic relationship mapping with shared analytics"
    )
]

# Intelligence Tier System Configuration
INTELLIGENCE_TIERS = {
    "current": TierTestConfig(
        name="CURRENT Intelligence",
        price_point=0.75,
        max_cost_budget=1.00,
        expected_duration_minutes=10,
        expected_features=[
            "4-Stage AI Analysis",
            "Multi-Dimensional Scoring", 
            "Risk Assessment Matrix",
            "Success Probability Modeling",
            "Strategic Recommendations",
            "Implementation Roadmaps"
        ],
        success_criteria={
            "cost_under_budget": True,
            "processing_time_minutes": 10,
            "confidence_score_min": 0.85,
            "recommendation_quality": "proceed_no_go_clear"
        }
    ),
    "standard": TierTestConfig(
        name="STANDARD Intelligence",
        price_point=7.50,
        max_cost_budget=8.00,
        expected_duration_minutes=20,
        expected_features=[
            "All Current Tier Features",
            "Historical Funding Analysis",
            "Award Pattern Intelligence", 
            "Geographic Distribution",
            "Temporal Trend Analysis",
            "Success Factor Identification"
        ],
        success_criteria={
            "cost_under_budget": True,
            "processing_time_minutes": 20,
            "historical_data_included": True,
            "geographic_analysis_present": True
        }
    ),
    "enhanced": TierTestConfig(
        name="ENHANCED Intelligence", 
        price_point=22.00,
        max_cost_budget=25.00,
        expected_duration_minutes=45,
        expected_features=[
            "All Standard Tier Features",
            "Complete RFP/NOFO Analysis",
            "Board Network Intelligence",
            "Decision Maker Profiling",
            "Competitive Deep Analysis", 
            "Partnership Opportunity Intelligence"
        ],
        success_criteria={
            "cost_under_budget": True,
            "processing_time_minutes": 45,
            "document_analysis_complete": True,
            "network_intelligence_present": True,
            "decision_maker_profiles": True
        }
    ),
    "complete": TierTestConfig(
        name="COMPLETE Intelligence",
        price_point=42.00,
        max_cost_budget=45.00,
        expected_duration_minutes=60,
        expected_features=[
            "All Enhanced Tier Features",
            "Advanced Network Mapping",
            "Policy Context Analysis", 
            "Real-Time Monitoring Setup",
            "Premium Documentation Suite",
            "Strategic Consulting Layer"
        ],
        success_criteria={
            "cost_under_budget": True,
            "processing_time_minutes": 60,
            "masters_thesis_quality": True,
            "policy_analysis_complete": True,
            "monitoring_setup_ready": True,
            "premium_documentation": True
        }
    )
}

# Test Scenarios Configuration
TEST_SCENARIOS = {
    "heroes_bridge_primary": {
        "name": "Heroes Bridge + Test Grant",
        "nonprofit_ein": "812827604",
        "opportunity_id": "TEST-GRANTS-2024-001",
        "priority": "primary",
        "description": "Veterans nonprofit with federal opportunity - primary test scenario"
    },
    "fauquier_secondary": {
        "name": "Fauquier Foundation + Test Grant", 
        "nonprofit_ein": "300219424",
        "opportunity_id": "TEST-GRANTS-2024-001",
        "priority": "secondary", 
        "description": "Health foundation with federal opportunity - secondary test scenario"
    }
}

# Performance Benchmarks (from master test plan)
PERFORMANCE_BENCHMARKS = {
    "api_response_time_max_seconds": 30,
    "entity_cache_hit_rate_min": 0.85,
    "concurrent_requests_supported": 10,
    "error_rate_max": 0.01,
    "uptime_target": 0.995,
    "data_consistency_target": 1.00,
    "cost_accuracy_variance_max": 0.05,
    "repeatability_variance_max": 0.10
}

# Success Criteria for Business Value Validation
BUSINESS_VALUE_CRITERIA = {
    "recommendation_accuracy_min": 0.85,
    "risk_factor_identification_min": 0.90,
    "implementation_feasibility_realistic": True,
    "competitive_intelligence_accurate": True,
    "roi_positive": True,
    "budget_efficiency_target": 50.00  # Total testing cost under $50
}


def get_processor_config(processor_name: str) -> ProcessorTestConfig:
    """Get configuration for a specific processor"""
    # Check AI pipeline stages
    for stage_config in AI_PIPELINE_STAGES.values():
        if stage_config.name == processor_name:
            return stage_config
    
    # Check data collection processors
    for config in DATA_COLLECTION_PROCESSORS:
        if config.name == processor_name:
            return config
            
    # Check analysis processors
    for config in ANALYSIS_PROCESSORS:
        if config.name == processor_name:
            return config
    
    # Default configuration for unknown processors
    return ProcessorTestConfig(
        name=processor_name,
        category="unknown",
        expected_cost_range=(0.50, 2.50),
        expected_duration_seconds=60,
        gpt_model="gpt-5-mini",
        description="Unknown processor - using default configuration"
    )


def get_tier_config(tier_name: str) -> TierTestConfig:
    """Get configuration for a specific intelligence tier"""
    if tier_name.lower() in INTELLIGENCE_TIERS:
        return INTELLIGENCE_TIERS[tier_name.lower()]
    else:
        raise ValueError(f"Unknown tier: {tier_name}. Available tiers: {list(INTELLIGENCE_TIERS.keys())}")


def validate_test_budget(total_cost: float) -> bool:
    """Validate if total test cost is within acceptable limits"""
    return total_cost <= COST_CONTROLS["max_total_test_cost"]


def get_scenario_config(scenario_name: str) -> Dict[str, Any]:
    """Get configuration for a specific test scenario"""
    if scenario_name in TEST_SCENARIOS:
        return TEST_SCENARIOS[scenario_name]
    else:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available scenarios: {list(TEST_SCENARIOS.keys())}")


# Export all configurations for easy import
__all__ = [
    'COST_CONTROLS',
    'AI_PIPELINE_STAGES', 
    'DATA_COLLECTION_PROCESSORS',
    'ANALYSIS_PROCESSORS',
    'INTELLIGENCE_TIERS',
    'TEST_SCENARIOS', 
    'PERFORMANCE_BENCHMARKS',
    'BUSINESS_VALUE_CRITERIA',
    'ProcessorTestConfig',
    'TierTestConfig',
    'get_processor_config',
    'get_tier_config', 
    'validate_test_budget',
    'get_scenario_config'
]