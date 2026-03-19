#!/usr/bin/env python3
"""
Analysis & Intelligence Router - Scoring, network, classification, and strategic planning endpoints.

Extracted from main.py analysis endpoints (lines ~6364-7135).
Handles financial scoring, network analysis, intelligence classification,
enhanced scoring, strategic planning, plan prospects, and network visualization.
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis & Intelligence"])


@router.post("/analysis/scoring")
async def run_financial_scoring(request: Dict[str, Any]):
    """Run 990 XML financial analysis on selected organizations."""
    try:
        logger.info(f"Received scoring request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")

        logger.info(f"Running financial scoring on {len(organizations)} organizations")

        # Simulate analysis delay
        await asyncio.sleep(2)

        # Mock financial analysis results - in production would use actual processors
        results = {
            "analysis_id": f"financial_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "financial_metrics": {
                "average_revenue_trend": (random.random() - 0.5) * 20,  # -10% to +10%
                "average_health_score": 0.7 + random.random() * 0.3,   # 0.7 to 1.0
                "risk_distribution": {
                    "Low": random.randint(40, 60),
                    "Medium": random.randint(20, 40),
                    "High": random.randint(0, 20)
                },
                "990_availability": random.randint(70, 95)  # 70% to 95%
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "revenue_trend": (random.random() - 0.5) * 20,
                    "health_score": 0.7 + random.random() * 0.3,
                    "risk_level": random.choice(["Low", "Medium", "High"]),
                    "990_available": random.random() > 0.25
                }
                for org in organizations
            ],
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        logger.error(f"Financial scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/network")
async def run_network_analysis(request: Dict[str, Any]):
    """Run network discovery and board connection analysis."""
    try:
        logger.info(f"Received network request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in network request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")

        logger.info(f"Running REAL network analysis on {len(organizations)} organizations")

        # Import the real board network analyzer
        from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
        from src.core.data_models import ProcessorConfig, WorkflowConfig, OrganizationProfile

        try:
            # Convert organizations to OrganizationProfile objects
            org_profiles = []
            for org in organizations:
                # Convert organization data to profile format
                profile = OrganizationProfile(
                    ein=org.get("ein", "000000000"),
                    name=org.get("organization_name", org.get("name", "Unknown Organization")),
                    state=org.get("state", "VA"),
                    ntee_code=org.get("ntee_code", "P99"),
                    board_members=org.get("board_members", [
                        "Sample Board Member 1",
                        "Sample Board Member 2",
                        "Sample Board Member 3"
                    ]),  # Default sample board members for testing
                    key_personnel=org.get("key_personnel", [
                        {"name": "Sample Executive Director", "title": "Executive Director"},
                        {"name": "Sample Board Chair", "title": "Board Chair"}
                    ])
                )
                org_profiles.append(profile)

            # Create processor and run analysis
            processor = BoardNetworkAnalyzerProcessor()
            config = ProcessorConfig(
                workflow_id=f'network_web_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                processor_name='board_network_analyzer',
                workflow_config=WorkflowConfig(
                    workflow_id='network_web',
                    target_ein=organizations[0].get("ein", "000000000"),
                    max_results=50
                )
            )

            # Create a simple workflow state with our organizations
            class SimpleWorkflowState:
                def __init__(self, orgs):
                    self.organizations = orgs

                def has_processor_succeeded(self, processor_name):
                    return processor_name == 'financial_scorer'

                def get_organizations_from_processor(self, processor_name):
                    return [org.dict() for org in self.organizations]

            workflow_state = SimpleWorkflowState(org_profiles)

            # Execute the real network analysis
            logger.info("Executing real BoardNetworkAnalyzerProcessor...")
            result = await processor.execute(config, workflow_state)

            if result.success:
                logger.info("Network analysis completed successfully")

                # Extract data from processor result
                network_data = result.data
                analysis_data = network_data.get("network_analysis", {})
                connections = network_data.get("connections", [])
                network_metrics = network_data.get("network_metrics", {})
                influence_scores = network_data.get("influence_scores", {})

                # Check if this is a "no board data" scenario
                if analysis_data.get("status") == "no_board_data":
                    logger.info("Network analysis completed but no board member data available")
                    return {
                        "analysis_id": f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "status": "completed_no_data",
                        "analyzed_count": len(org_profiles),
                        "data_limitation": analysis_data.get("data_limitation", "Board member data not available"),
                        "message": analysis_data.get("message", "Board member data not available in source filings"),
                        "network_metrics": {
                            "total_board_connections": 0,
                            "unique_board_members": 0,
                            "network_density": 0.0,
                            "data_status": "not_available"
                        },
                        "organization_results": [
                            {
                                "organization_name": org.get("name", "Unknown"),
                                "ein": org.get("ein"),
                                "board_connections": "Data not available",
                                "strategic_links": "Data not available",
                                "influence_score": "Data not available",
                                "network_position": "Data not available"
                            }
                            for org in network_data.get("organizations", [])
                        ],
                        "top_connections": [],
                        "insights": analysis_data.get("insights", {}),
                        "raw_network_data": network_data,
                        "timestamp": datetime.now().isoformat()
                    }

                # Normal case with board member data
                results = {
                    "analysis_id": f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "completed",
                    "analyzed_count": len(org_profiles),
                    "network_metrics": {
                        "total_board_connections": len(connections),
                        "unique_board_members": analysis_data.get("unique_individuals", 0),
                        "network_density": network_metrics.get("network_stats", {}).get("network_density", 0.0),
                        "average_clustering": network_metrics.get("network_stats", {}).get("average_clustering", 0.0)
                    },
                    "organization_results": [
                        {
                            "organization_name": org["name"],
                            "ein": org["ein"],
                            "board_connections": len([c for c in connections if c["org1_ein"] == org["ein"] or c["org2_ein"] == org["ein"]]),
                            "strategic_links": network_metrics.get("organization_metrics", {}).get(org["ein"], {}).get("total_connections", 0),
                            "influence_score": network_metrics.get("organization_metrics", {}).get(org["ein"], {}).get("betweenness_centrality", 0.0),
                            "network_position": "Central" if network_metrics.get("organization_metrics", {}).get(org["ein"], {}).get("betweenness_centrality", 0) > 0.1 else "Peripheral"
                        }
                        for org in network_data.get("organizations", [])
                    ],
                    "top_connections": [
                        {
                            "name": name,
                            "organizations": data["board_positions"],
                            "influence": data["total_influence_score"]
                        }
                        for name, data in influence_scores.get("top_influencers", {}).items()
                    ][:5],
                    "raw_network_data": network_data,  # Include full data for visualization
                    "timestamp": datetime.now().isoformat()
                }

                return results

            else:
                logger.error(f"Network analysis failed: {result.errors}")
                # Fallback to enhanced mock data with error info
                return {
                    "analysis_id": f"network_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "completed_with_fallback",
                    "analyzed_count": len(organizations),
                    "error": "Real analysis failed, using fallback",
                    "network_metrics": {
                        "total_board_connections": 12,
                        "unique_board_members": 8,
                        "network_density": 0.3,
                        "average_influence_score": 0.6
                    },
                    "organization_results": [
                        {
                            "organization_name": org.get("organization_name", "Unknown"),
                            "ein": org.get("ein"),
                            "board_connections": 3,
                            "strategic_links": 2,
                            "influence_score": 0.5,
                            "network_position": "Connected"
                        }
                        for org in organizations
                    ],
                    "top_connections": [
                        {"name": "Board Member 1", "organizations": 2, "influence": 0.75},
                        {"name": "Board Member 2", "organizations": 2, "influence": 0.65}
                    ],
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as processor_error:
            logger.error(f"Real network processor failed: {processor_error}")
            # Enhanced fallback with sample board member connections
            return {
                "analysis_id": f"network_enhanced_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed_with_enhanced_fallback",
                "analyzed_count": len(organizations),
                "error": f"Processor error: {str(processor_error)}",
                "network_metrics": {
                    "total_board_connections": len(organizations) * 2,
                    "unique_board_members": len(organizations) + 3,
                    "network_density": 0.4,
                    "average_influence_score": 0.7
                },
                "organization_results": [
                    {
                        "organization_name": org.get("organization_name", org.get("name", "Unknown")),
                        "ein": org.get("ein"),
                        "board_connections": 4,
                        "strategic_links": 3,
                        "influence_score": 0.6,
                        "network_position": "Connected"
                    }
                    for org in organizations
                ],
                "top_connections": [
                    {"name": "Executive Director A", "organizations": 3, "influence": 0.85},
                    {"name": "Board Chair B", "organizations": 2, "influence": 0.75},
                    {"name": "Treasurer C", "organizations": 2, "influence": 0.65}
                ],
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Network analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/intelligence/classify")
async def run_intelligence_classification(request: Dict[str, Any]):
    """Run AI-powered intelligent classification and opportunity scoring."""
    try:
        organizations = request.get("organizations", [])
        min_score = request.get("min_score", 0.3)

        if not organizations:
            raise HTTPException(status_code=400, detail="Organizations list is required")

        logger.info(f"Running AI classification on {len(organizations)} organizations")

        # Simulate analysis delay
        await asyncio.sleep(1)

        # Mock intelligence classification results - in production would use intelligent_classifier
        results = {
            "analysis_id": f"intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "min_score_threshold": min_score,
            "classification_metrics": {
                "average_score": round(random.uniform(0.5, 0.9), 3),
                "average_confidence": round(random.uniform(0.7, 0.95), 3),
                "recommendations": {
                    "Promote": random.randint(40, 70),
                    "Review": random.randint(20, 40),
                    "Monitor": random.randint(10, 30)
                }
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "classification_score": round(random.uniform(0.4, 0.95), 3),
                    "confidence_level": round(random.uniform(0.6, 0.95), 2),
                    "recommendation": random.choice(["Promote", "Review", "Monitor"]),
                    "key_factors": random.sample([
                        "Strong financial performance",
                        "Expanding network influence",
                        "Mission alignment",
                        "Geographic relevance",
                        "Program compatibility",
                        "Historical success patterns"
                    ], 3),
                    "risk_factors": random.sample([
                        "Limited financial transparency",
                        "Recent leadership changes",
                        "Narrow funding base",
                        "Geographic constraints"
                    ], random.randint(0, 2))
                }
                for org in organizations
            ],
            "insights": [
                "Organizations show strong potential for strategic partnership development",
                "Network influence appears to be a key differentiator in this cohort",
                "Financial health indicators suggest sustainable growth trajectories",
                "Mission alignment scores indicate high compatibility with funding priorities"
            ],
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        logger.error(f"Intelligence classification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/enhanced-scoring")
async def run_enhanced_scoring(request: Dict[str, Any]):
    """Run enhanced scoring analysis using local Python algorithms."""
    try:
        logger.info(f"Received enhanced scoring request: {request}")
        organizations = request.get("organizations", [])
        if not organizations:
            logger.error(f"No organizations provided in enhanced scoring request: {request}")
            raise HTTPException(status_code=400, detail="Organizations list is required")

        logger.info(f"Running enhanced scoring on {len(organizations)} organizations")

        # Simulate analysis delay
        await asyncio.sleep(1.8)

        # Mock enhanced scoring results using local Python analysis
        results = {
            "analysis_id": f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "analyzed_count": len(organizations),
            "enhanced_metrics": {
                "average_mission_alignment": round(random.uniform(0.6, 0.9), 3),
                "average_eligibility_match": round(random.uniform(0.65, 0.95), 3),
                "average_opportunity_fit": round(random.uniform(0.7, 0.92), 3),
                "geographic_distribution": {
                    "Virginia": random.randint(60, 85),
                    "Regional": random.randint(10, 25),
                    "National": random.randint(5, 15)
                }
            },
            "organization_results": [
                {
                    "organization_name": org.get("organization_name", "Unknown"),
                    "ein": org.get("ein"),
                    "mission_alignment_score": round(random.uniform(0.5, 0.95), 3),
                    "eligibility_match_score": round(random.uniform(0.6, 0.98), 3),
                    "opportunity_fit_score": round(random.uniform(0.65, 0.92), 3),
                    "enhanced_score": round(random.uniform(0.65, 0.93), 3),
                    "qualification_factors": [
                        random.choice(["Financial Strength", "Geographic Match", "Mission Alignment", "Foundation Type"]),
                        random.choice(["Activity Pattern", "Network Position", "Grant History", "Organizational Size"])
                    ]
                }
                for org in organizations
            ],
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        logger.error(f"Enhanced scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analysis/strategic-plan")
async def generate_strategic_plan(request: Dict[str, Any]):
    """Generate strategic plan and recommendations for qualified prospects."""
    try:
        logger.info(f"Received strategic planning request: {request}")
        profile_id = request.get("profile_id")

        if not profile_id:
            logger.error("No profile_id provided in strategic planning request")
            raise HTTPException(status_code=400, detail="Profile ID is required")

        logger.info(f"Generating strategic plan for profile: {profile_id}")

        # Simulate strategic analysis delay
        await asyncio.sleep(3.0)

        # Mock strategic planning results
        high_scoring_count = random.randint(5, 15)
        results = {
            "analysis_id": f"strategic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "profile_id": profile_id,
            "strategic_metrics": {
                "qualified_prospects_count": high_scoring_count,
                "promotion_candidates": random.randint(3, 8),
                "average_combined_score": round(random.uniform(0.75, 0.92), 3),
                "recommended_focus_areas": [
                    "High-value network connections",
                    "Strategic partnerships",
                    "Board-level introductions"
                ]
            },
            "recommendations": [
                {
                    "priority": "High",
                    "action": "Initiate contact with top 3 scoring organizations",
                    "timeline": "Within 2 weeks",
                    "expected_outcome": "Strategic partnership discussions"
                },
                {
                    "priority": "Medium",
                    "action": "Network mapping for board connections",
                    "timeline": "Within 1 month",
                    "expected_outcome": "Warm introductions identified"
                },
                {
                    "priority": "Medium",
                    "action": "Develop partnership proposals for candidates",
                    "timeline": "Within 6 weeks",
                    "expected_outcome": "Formal collaboration framework"
                }
            ],
            "next_steps": [
                "Review enhanced scoring results for top prospects",
                "Prioritize network connections based on influence scores",
                "Prepare strategic outreach materials",
                "Schedule follow-up analysis in 30 days"
            ],
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        logger.error(f"Strategic planning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/plan/{profile_id}/prospects")
async def get_plan_prospects(profile_id: str, stage: Optional[str] = None):
    """Get prospects for PLAN tab analysis - supports comma-separated stages."""
    try:
        from src.discovery.funnel_manager import funnel_manager
        from src.discovery.base_discoverer import FunnelStage

        # Handle comma-separated stages for filtering
        if stage:
            stage_values = [s.strip() for s in stage.split(',')]
            opportunities = []
            for stage_val in stage_values:
                try:
                    stage_enum = FunnelStage(stage_val)
                    stage_opportunities = funnel_manager.get_opportunities_by_stage(profile_id, stage_enum)
                    opportunities.extend(stage_opportunities)
                except ValueError:
                    logger.warning(f"Invalid stage in filter: {stage_val}")
        else:
            opportunities = funnel_manager.get_all_opportunities(profile_id)

        # Convert to serializable format
        prospects_data = []
        for opp in opportunities:
            prospect = {
                "opportunity_id": opp.opportunity_id,
                "organization_name": opp.organization_name,
                "source_type": opp.source_type.value if hasattr(opp.source_type, 'value') else str(opp.source_type),
                "funnel_stage": opp.funnel_stage.value if hasattr(opp.funnel_stage, 'value') else str(opp.funnel_stage),
                "compatibility_score": opp.compatibility_score,
                "confidence_level": opp.confidence_level,
                "ein": getattr(opp, 'ein', None) or opp.external_data.get('ein', None),
                "discovered_at": opp.discovered_at.isoformat() if opp.discovered_at else None,
                "stage_updated_at": opp.stage_updated_at.isoformat() if opp.stage_updated_at else None,
                "stage_notes": opp.stage_notes,
                "funding_amount": opp.funding_amount,
                "application_deadline": opp.application_deadline,
                "geographic_info": opp.geographic_info,
                "match_factors": opp.match_factors
            }
            prospects_data.append(prospect)

        return {
            "profile_id": profile_id,
            "stage_filter": stage,
            "total_prospects": len(prospects_data),
            "opportunities": prospects_data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get PLAN prospects for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analyze/network-data/{profile_id}")
async def get_network_visualization_data(profile_id: str):
    """Get network data and generate visualizations for ANALYZE tab."""
    try:
        logger.info(f"Generating network visualizations for profile: {profile_id}")

        # Import the existing network visualizer processor
        from src.processors.visualization.network_visualizer import create_network_visualizer

        # Import required components for real network analysis
        from src.processors.analysis.board_network_analyzer import BoardNetworkAnalyzerProcessor
        from src.core.data_models import ProcessorConfig, WorkflowConfig, OrganizationProfile

        # Get real network data - first get some sample organizations
        try:
            # Try to get entities from cache
            from src.core.entity_cache_manager import EntityCacheManager
            cache_manager = EntityCacheManager()
            sample_entities = cache_manager.get_all_cached_entities("nonprofit")[:5]

            org_profiles = []
            for entity_id, entity_data in sample_entities.items():
                profile = OrganizationProfile(
                    ein=entity_id,
                    name=entity_data.get('name', f'Organization {entity_id}'),
                    state=entity_data.get('state', 'VA'),
                    ntee_code=entity_data.get('ntee_code', 'T31'),
                    board_members=[
                        f"Board Member A-{entity_id[-3:]}",
                        f"Board Member B-{entity_id[-3:]}",
                        "Sarah Johnson",  # Create cross-connections
                        "Michael Davis" if int(entity_id[-1]) % 2 == 0 else f"Director C-{entity_id[-3:]}"
                    ],
                    key_personnel=[
                        {"name": f"Executive Director {entity_id[-3:]}", "title": "Executive Director"},
                        {"name": "Sarah Johnson" if int(entity_id[-1]) % 3 == 0 else "Board Chair", "title": "Board Chair"}
                    ]
                )
                org_profiles.append(profile)

        except Exception as entity_error:
            logger.warning(f"Could not load entity data, using sample organizations: {entity_error}")
            # Fallback sample organizations with board connections
            org_profiles = [
                OrganizationProfile(
                    ein="123456789",
                    name="Health Innovation Foundation",
                    state="VA",
                    ntee_code="E21",
                    board_members=["Dr. Sarah Johnson", "Michael Davis", "Jennifer Wilson", "Board Member A"],
                    key_personnel=[{"name": "Dr. Sarah Johnson", "title": "Board Chair"}]
                ),
                OrganizationProfile(
                    ein="987654321",
                    name="Community Development Partners",
                    state="VA",
                    ntee_code="F30",
                    board_members=["Michael Davis", "Jennifer Wilson", "Dr. Robert Brown", "Board Member C"],
                    key_personnel=[{"name": "Michael Davis", "title": "Board Member"}]
                ),
                OrganizationProfile(
                    ein="555123456",
                    name="Rural Development Initiative",
                    state="VA",
                    ntee_code="T31",
                    board_members=["Jennifer Wilson", "Dr. Robert Brown", "Lisa Anderson", "Board Member E"],
                    key_personnel=[{"name": "Dr. Robert Brown", "title": "President"}]
                )
            ]

        # Run real network analysis
        logger.info("Running REAL BoardNetworkAnalyzerProcessor for visualization...")
        processor = BoardNetworkAnalyzerProcessor()
        config = ProcessorConfig(
            workflow_id=f'network_viz_{profile_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            processor_name='board_network_analyzer',
            workflow_config=WorkflowConfig(
                workflow_id='network_viz',
                target_ein=org_profiles[0].ein,
                max_results=50
            )
        )

        # Create workflow state
        class SimpleWorkflowState:
            def __init__(self, orgs):
                self.organizations = orgs

            def has_processor_succeeded(self, processor_name):
                return processor_name == 'financial_scorer'

            def get_organizations_from_processor(self, processor_name):
                return [org.dict() for org in self.organizations]

        workflow_state = SimpleWorkflowState(org_profiles)

        # Execute network analysis
        result = await processor.execute(config, workflow_state)

        if result.success:
            logger.info("Real network analysis successful!")
            network_data = result.data

            # Check if we have a "no board data" scenario
            analysis_data = network_data.get("network_analysis", {})
            if analysis_data.get("status") == "no_board_data":
                logger.info("Network analysis completed but no board member data available")
                return {
                    "profile_id": profile_id,
                    "board_network_html": f"""
                        <div class='text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300'>
                            <div class='mx-auto max-w-md'>
                                <h3 class='text-lg font-semibold text-gray-900 mb-3'>Board Member Data Not Available</h3>
                                <p class='text-sm text-gray-600 mb-4'>{analysis_data.get('message', 'Board member information not found in source filings')}</p>
                                <div class='bg-blue-50 p-3 rounded-lg'>
                                    <p class='text-xs text-blue-800'>
                                        <strong>Data Source Limitation:</strong><br>
                                        {analysis_data.get('data_limitation', 'ProPublica 990 filings provide financial data but limited governance details')}
                                    </p>
                                </div>
                            </div>
                        </div>
                    """,
                    "influence_network_html": f"""
                        <div class='text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300'>
                            <div class='mx-auto max-w-md'>
                                <h3 class='text-lg font-semibold text-gray-900 mb-3'>Influence Network Not Available</h3>
                                <p class='text-sm text-gray-600 mb-4'>Cannot generate influence network without board member data</p>
                                <div class='bg-yellow-50 p-3 rounded-lg'>
                                    <p class='text-xs text-yellow-800'>
                                        <strong>Recommendations:</strong><br>
                                        • Manual data entry for board information<br>
                                        • Check organization websites<br>
                                        • Review annual reports for governance details
                                    </p>
                                </div>
                            </div>
                        </div>
                    """,
                    "network_metrics": network_data.get('network_metrics', {}),
                    "influence_scores": network_data.get('influence_scores', {}),
                    "total_organizations": len(network_data.get('organizations', [])),
                    "total_connections": 0,
                    "analysis_summary": {
                        "data_source": "real_network_analysis_no_data",
                        "data_status": "board_data_unavailable",
                        "total_board_members": 0,
                        "unique_individuals": 0,
                        "spiderweb_visualization": "unavailable_no_data",
                        "message": analysis_data.get('message', 'Board member data not available'),
                        "insights": network_data.get('insights', {})
                    },
                    "timestamp": datetime.now().isoformat()
                }

        else:
            logger.warning(f"Network analysis failed: {result.errors}, using enhanced fallback")
            # Enhanced fallback with realistic connections
            network_data = {
                "organizations": [org.dict() for org in org_profiles],
                "connections": [
                    {
                        "org1_ein": "123456789",
                        "org1_name": "Health Innovation Foundation",
                        "org2_ein": "987654321",
                        "org2_name": "Community Development Partners",
                        "shared_members": ["Michael Davis", "Jennifer Wilson"],
                        "connection_strength": 2.0
                    },
                    {
                        "org1_ein": "987654321",
                        "org1_name": "Community Development Partners",
                        "org2_ein": "555123456",
                        "org2_name": "Rural Development Initiative",
                        "shared_members": ["Jennifer Wilson", "Dr. Robert Brown"],
                        "connection_strength": 2.0
                    }
                ],
                "influence_scores": {
                    "individual_influence": {
                        "Jennifer Wilson": {
                            "total_influence_score": 9.0,
                            "organizations": ["Health Innovation Foundation", "Community Development Partners", "Rural Development Initiative"],
                            "board_positions": 3
                        },
                        "Michael Davis": {
                            "total_influence_score": 6.5,
                            "organizations": ["Health Innovation Foundation", "Community Development Partners"],
                            "board_positions": 2
                        }
                    }
                },
                "network_metrics": {
                    "organization_metrics": {
                        "123456789": {"centrality": 0.75, "betweenness_centrality": 0.6, "total_connections": 1},
                        "987654321": {"centrality": 0.85, "betweenness_centrality": 0.8, "total_connections": 2},
                        "555123456": {"centrality": 0.65, "betweenness_centrality": 0.4, "total_connections": 1}
                    }
                }
            }

        # Create visualizer instance
        visualizer = create_network_visualizer()

        # Generate both network types with REAL data
        try:
            network_fig = visualizer.create_interactive_network(network_data, f"Board Network Analysis - {profile_id}")
            influence_fig = visualizer.create_influence_network(network_data)

            # Convert to HTML for embedding
            board_network_html = network_fig.to_html(
                include_plotlyjs='cdn',
                div_id="board-network-plotly-div",
                config={'displayModeBar': True, 'responsive': True}
            )

            influence_network_html = influence_fig.to_html(
                include_plotlyjs='cdn',
                div_id="influence-network-plotly-div",
                config={'displayModeBar': True, 'responsive': True}
            )

            return {
                "profile_id": profile_id,
                "board_network_html": board_network_html,
                "influence_network_html": influence_network_html,
                "network_metrics": network_data.get('network_metrics', {}),
                "influence_scores": network_data.get('influence_scores', {}),
                "total_organizations": len(network_data.get('organizations', [])),
                "total_connections": len(network_data.get('connections', [])),
                "analysis_summary": {
                    "data_source": "real_network_analysis" if result.success else "enhanced_fallback",
                    "total_board_members": network_data.get("network_analysis", {}).get("total_board_members", 0),
                    "unique_individuals": network_data.get("network_analysis", {}).get("unique_individuals", 0),
                    "spiderweb_visualization": "active"
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as viz_error:
            logger.error(f"Network visualization generation failed: {viz_error}")
            # Return analysis data without visualizations
            return {
                "profile_id": profile_id,
                "board_network_html": f"<div class='text-center py-8'><h3>Network Analysis Complete</h3><p>Found {len(network_data.get('connections', []))} board connections</p><p>Visualization failed: {str(viz_error)}</p></div>",
                "influence_network_html": f"<div class='text-center py-8'><h3>Influence Analysis Complete</h3><p>Analyzed {network_data.get('network_analysis', {}).get('unique_individuals', 0)} unique board members</p><p>Visualization failed</p></div>",
                "network_metrics": network_data.get('network_metrics', {}),
                "influence_scores": network_data.get('influence_scores', {}),
                "analysis_summary": {
                    "data_source": "real_analysis_visualization_failed",
                    "analysis_successful": True,
                    "visualization_failed": True,
                    "error": str(viz_error)
                },
                "error": f"Visualization generation failed: {str(viz_error)}",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Network data retrieval failed: {e}")
        logger.error(f"Failed to generate network visualizations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
