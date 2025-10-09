"""
Foundation Network Intelligence API Endpoints
Multi-foundation grant bundling, co-funding analysis, and network graph queries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

# Import tool models and functions
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.foundation_grantee_bundling_tool.app import (
    GranteeBundlingInput,
    GranteeBundlingOutput,
    analyze_foundation_bundling
)
from tools.foundation_grantee_bundling_tool.app.database_service import (
    FoundationGrantsDatabaseService
)
from src.analytics.foundation_network_graph import (
    FoundationNetworkGraph,
    NetworkQueryEngine,
    NetworkGraphOutput
)
from src.analytics.network_pathfinder import (
    NetworkPathfinder,
    InfluenceAnalyzer,
    find_strategic_pathways,
    analyze_network_influence
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/network", tags=["Foundation Network Intelligence"])


# ============================================================================
# PHASE 1: MULTI-FOUNDATION BUNDLING
# ============================================================================

@router.post("/bundling/analyze", response_model=dict)
async def analyze_multi_foundation_bundling(request: dict):
    """
    Analyze grant bundling across multiple foundations.

    Input:
    {
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024],
        "min_foundations": 2,
        "include_grant_purposes": true,
        "geographic_filter": ["VA", "MD", "DC"]
    }

    Returns:
    {
        "bundled_grantees": [...],
        "foundation_overlap_matrix": [...],
        "thematic_clusters": [...],
        "processing_time_seconds": 1.23,
        ...
    }
    """
    try:
        logger.info(f"Bundling analysis request: {len(request.get('foundation_eins', []))} foundations")

        # Validate input
        if not request.get('foundation_eins'):
            raise HTTPException(status_code=400, detail="foundation_eins required")

        if len(request.get('foundation_eins', [])) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 foundation EINs required for bundling analysis"
            )

        # Create input object
        bundling_input = GranteeBundlingInput(
            foundation_eins=request['foundation_eins'],
            tax_years=request.get('tax_years', [2022, 2023, 2024]),
            min_foundations=request.get('min_foundations', 2),
            include_grant_purposes=request.get('include_grant_purposes', True),
            geographic_filter=request.get('geographic_filter'),
            min_grant_amount=request.get('min_grant_amount', 0)
        )

        # Execute bundling
        result = await analyze_foundation_bundling(
            foundation_eins=bundling_input.foundation_eins,
            tax_years=bundling_input.tax_years,
            min_foundations=bundling_input.min_foundations,
            include_grant_purposes=bundling_input.include_grant_purposes,
            geographic_filter=bundling_input.geographic_filter
        )

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Bundling analysis failed: {result.error}"
            )

        # Convert to dict for JSON response
        output = result.data

        response = {
            "success": True,
            "data": {
                "total_foundations_analyzed": output.total_foundations_analyzed,
                "foundation_eins": output.foundation_eins,
                "tax_years_analyzed": output.tax_years_analyzed,
                "total_unique_grantees": output.total_unique_grantees,
                "bundled_grantees_count": len(output.bundled_grantees),
                "bundled_grantees": [
                    {
                        "grantee_ein": bg.grantee_ein,
                        "grantee_name": bg.grantee_name,
                        "funder_count": bg.funder_count,
                        "total_funding": bg.total_funding,
                        "average_grant_size": bg.average_grant_size,
                        "funding_sources": [
                            {
                                "foundation_ein": fs.foundation_ein,
                                "foundation_name": fs.foundation_name,
                                "grant_amount": fs.grant_amount,
                                "grant_year": fs.grant_year
                            }
                            for fs in bg.funding_sources
                        ],
                        "first_grant_year": bg.first_grant_year,
                        "last_grant_year": bg.last_grant_year,
                        "funding_stability": bg.funding_stability,
                        "common_purposes": bg.common_purposes
                    }
                    for bg in output.bundled_grantees[:100]  # Limit to top 100
                ],
                "foundation_overlap_matrix": [
                    {
                        "foundation_1": fo.foundation_name_1,
                        "foundation_2": fo.foundation_name_2,
                        "shared_grantees_count": fo.shared_grantees_count,
                        "jaccard_similarity": fo.jaccard_similarity
                    }
                    for fo in output.foundation_overlap_matrix
                ],
                "thematic_clusters": [
                    {
                        "cluster_name": tc.cluster_name,
                        "grantee_count": tc.grantee_count,
                        "total_funding": tc.total_funding,
                        "common_keywords": tc.common_keywords
                    }
                    for tc in output.thematic_clusters
                ],
                "statistics": {
                    "total_grants_analyzed": output.total_grants_analyzed,
                    "total_funding_amount": output.total_funding_amount,
                    "average_grants_per_foundation": output.average_grants_per_foundation,
                    "data_completeness_score": output.data_completeness_score,
                    "recipient_matching_confidence": output.recipient_matching_confidence
                },
                "processing_time_seconds": output.processing_time_seconds,
                "analysis_date": output.analysis_date
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bundling analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bundling/top-co-funded")
async def get_top_co_funded_organizations(
    limit: int = Query(20, ge=1, le=100),
    min_funders: int = Query(2, ge=2)
):
    """
    Get top co-funded organizations across all foundations in database.

    Query params:
    - limit: Max results (default 20, max 100)
    - min_funders: Minimum number of funders (default 2)
    """
    try:
        db_service = FoundationGrantsDatabaseService()

        # This would require a more complex query - simplified version
        # In production, this would query aggregated results

        return {
            "success": True,
            "message": "Query top co-funded organizations",
            "note": "Feature requires grant data to be loaded. Use /bundling/analyze with specific EINs."
        }

    except Exception as e:
        logger.error(f"Error querying top co-funded orgs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 2: CO-FUNDING ANALYSIS
# ============================================================================

@router.post("/cofunding/analyze", response_model=dict)
async def analyze_cofunding_patterns(request: dict):
    """
    Analyze co-funding patterns and funder similarity.

    Input:
    {
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024],
        "similarity_threshold": 0.3,
        "max_peer_funders": 10,
        "include_network_graph": true
    }

    Returns:
    {
        "funder_similarity_pairs": [...],
        "peer_funder_groups": [...],
        "recommendations": [...],
        "network_statistics": {...}
    }
    """
    try:
        from tools.foundation_grantee_bundling_tool.app.cofunding_analyzer import analyze_cofunding

        logger.info("Co-funding analysis request received")

        # First, run bundling analysis
        bundling_result = await analyze_multi_foundation_bundling(request)

        if not bundling_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Bundling analysis failed"
            )

        # Extract bundling output
        bundling_data = bundling_result['data']

        # Reconstruct bundling output object for co-funding analyzer
        # (In production, this would be cached or passed directly)
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingOutput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        # Create a mock bundling output from the API response
        # This is simplified - in production, reuse the actual object
        tool = FoundationGranteeBundlingTool()
        bundling_input_data = {
            'foundation_eins': request.get('foundation_eins', []),
            'tax_years': request.get('tax_years', [2022, 2023, 2024])
        }

        # Re-run bundling to get proper object
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        bundling_input_obj = GranteeBundlingInput(**bundling_input_data)
        bundling_result_obj = await tool.execute(bundling_input=bundling_input_obj)

        if not bundling_result_obj.success:
            raise HTTPException(
                status_code=500,
                detail=f"Bundling failed: {bundling_result_obj.error}"
            )

        # Run co-funding analysis
        cofunding_output = await analyze_cofunding(
            bundling_results=bundling_result_obj.data,
            similarity_threshold=request.get('similarity_threshold', 0.3),
            max_peer_funders=request.get('max_peer_funders', 10),
            include_network_graph=request.get('include_network_graph', True)
        )

        # Format response
        response = {
            "success": True,
            "data": {
                "similarity_pairs_count": len(cofunding_output.funder_similarity_pairs),
                "highly_similar_pairs": [
                    {
                        "foundation_1": fs.foundation_name_1,
                        "foundation_2": fs.foundation_name_2,
                        "similarity_score": fs.similarity_score,
                        "jaccard_similarity": fs.jaccard_similarity,
                        "shared_grantees_count": fs.shared_grantees_count,
                        "total_co_funding": fs.total_co_funding_amount,
                        "common_themes": fs.common_thematic_focus
                    }
                    for fs in cofunding_output.highly_similar_pairs[:20]
                ],
                "peer_funder_groups": [
                    {
                        "cluster_id": pg.cluster_id,
                        "cluster_name": pg.cluster_name,
                        "member_count": pg.member_count,
                        "member_foundations": pg.member_foundations,
                        "cluster_density": pg.cluster_density,
                        "total_funding": pg.total_cluster_funding
                    }
                    for pg in cofunding_output.peer_funder_groups
                ],
                "recommendations": [
                    {
                        "foundation_name": rec.recommended_foundation_name,
                        "foundation_ein": rec.recommended_foundation_ein,
                        "recommendation_type": rec.recommendation_type,
                        "confidence_score": rec.confidence_score,
                        "rationale": rec.rationale,
                        "priority": rec.priority,
                        "supporting_evidence": rec.supporting_evidence,
                        "suggested_approach": rec.suggested_approach
                    }
                    for rec in cofunding_output.recommendations[:10]
                ],
                "network_statistics": cofunding_output.network_statistics,
                "network_graph": cofunding_output.foundation_network_graph,
                "processing_time_seconds": cofunding_output.processing_time_seconds
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Co-funding analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cofunding/peer-groups")
async def get_peer_funder_groups(
    min_members: int = Query(2, ge=2),
    min_density: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Get identified peer funder groups.

    Query params:
    - min_members: Minimum members per group (default 2)
    - min_density: Minimum cluster density (default 0.0)
    """
    try:
        return {
            "success": True,
            "message": "Query peer funder groups",
            "note": "Feature requires running co-funding analysis first. Use /cofunding/analyze."
        }

    except Exception as e:
        logger.error(f"Error querying peer groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GRANT DATABASE MANAGEMENT
# ============================================================================

@router.get("/grants/statistics")
async def get_grant_database_statistics():
    """Get overall statistics about foundation grants database."""
    try:
        db_service = FoundationGrantsDatabaseService()
        stats = db_service.get_grant_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting grant statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grants/search")
async def search_grantees(
    search_term: str = Query(..., min_length=3),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search for grantees by name.

    Query params:
    - search_term: Search string (min 3 characters)
    - limit: Max results (default 50, max 200)
    """
    try:
        db_service = FoundationGrantsDatabaseService()
        results = db_service.search_grantees(search_term, limit)

        return {
            "success": True,
            "search_term": search_term,
            "result_count": len(results),
            "data": results
        }

    except Exception as e:
        logger.error(f"Error searching grantees: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grants/import")
async def import_grants_from_schedule_i(request: dict):
    """
    Import grants from Schedule I data.

    Input:
    {
        "foundation_ein": "12-3456789",
        "foundation_name": "Example Foundation",
        "grants": [
            {
                "recipient_name": "Grantee Name",
                "recipient_ein": "98-7654321",
                "amount": 50000,
                "purpose": "Program support",
                "year": 2023
            },
            ...
        ]
    }
    """
    try:
        db_service = FoundationGrantsDatabaseService()

        foundation_ein = request.get('foundation_ein')
        foundation_name = request.get('foundation_name')
        grants_data = request.get('grants', [])

        if not foundation_ein or not grants_data:
            raise HTTPException(
                status_code=400,
                detail="foundation_ein and grants required"
            )

        # Prepare grants for bulk insert
        grants_to_insert = []
        for grant in grants_data:
            grants_to_insert.append({
                'foundation_ein': foundation_ein,
                'foundation_name': foundation_name,
                'grantee_ein': grant.get('recipient_ein'),
                'grantee_name': grant.get('recipient_name'),
                'normalized_grantee_name': grant.get('recipient_name', '').lower().strip(),
                'grant_amount': grant.get('amount', 0),
                'grant_year': grant.get('year'),
                'grant_purpose': grant.get('purpose'),
                'grant_tier': None,  # Will be computed
                'grantee_city': grant.get('city'),
                'grantee_state': grant.get('state'),
                'source_form': '990-PF',
                'data_quality_score': 0.8
            })

        # Bulk insert
        inserted_count = db_service.bulk_insert_grants(grants_to_insert)

        return {
            "success": True,
            "foundation_ein": foundation_ein,
            "grants_provided": len(grants_data),
            "grants_inserted": inserted_count,
            "message": f"Imported {inserted_count} grants from Schedule I"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing grants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: NETWORK GRAPH CONSTRUCTION & QUERIES
# ============================================================================

@router.post("/graph/build")
async def build_network_graph(request: dict):
    """
    Build foundation-grantee bipartite network graph from bundling results.

    Input:
    {
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024],
        "min_foundations": 2
    }

    Returns:
    {
        "graph_built": true,
        "statistics": {...},
        "nodes_count": 150,
        "edges_count": 320
    }
    """
    try:
        logger.info("Building network graph from bundling results")

        # First, run bundling analysis to get data
        bundling_result = await analyze_multi_foundation_bundling(request)

        if not bundling_result.get('success'):
            raise HTTPException(
                status_code=500,
                detail="Bundling analysis failed - cannot build graph"
            )

        # Reconstruct bundling output object
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=request.get('foundation_eins', []),
            tax_years=request.get('tax_years', [2022, 2023, 2024]),
            min_foundations=request.get('min_foundations', 2)
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        if not bundling_output.success:
            raise HTTPException(
                status_code=500,
                detail=f"Bundling failed: {bundling_output.error}"
            )

        # Build graph
        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Get statistics
        stats = graph_builder.get_network_statistics()

        return {
            "success": True,
            "graph_built": True,
            "statistics": stats,
            "nodes_count": graph.number_of_nodes(),
            "edges_count": graph.number_of_edges(),
            "message": f"Network graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building network graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/co-funders")
async def query_co_funders(request: dict):
    """
    Find all foundations funding a specific grantee.

    Input:
    {
        "grantee_ein": "12-3456789",
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024]
    }

    Returns:
    {
        "grantee_ein": "12-3456789",
        "grantee_name": "Example Nonprofit",
        "co_funders": [...]
    }
    """
    try:
        grantee_ein = request.get('grantee_ein')
        if not grantee_ein:
            raise HTTPException(status_code=400, detail="grantee_ein required")

        # Build graph first
        graph_result = await build_network_graph(request)

        if not graph_result.get('success'):
            raise HTTPException(status_code=500, detail="Failed to build graph")

        # Query graph (need to rebuild - in production, cache this)
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=request.get('foundation_eins', []),
            tax_years=request.get('tax_years', [2022, 2023, 2024]),
            min_foundations=1  # Include all grantees
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Query for co-funders
        query_engine = NetworkQueryEngine(graph)
        co_funders = query_engine.find_co_funders(grantee_ein)

        return {
            "success": True,
            "grantee_ein": grantee_ein,
            "grantee_name": graph.nodes[grantee_ein].get('name', grantee_ein) if grantee_ein in graph else None,
            "co_funders_count": len(co_funders),
            "co_funders": co_funders
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying co-funders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/paths")
async def find_connection_paths(request: dict):
    """
    Find strategic pathways between source and target organizations.

    Input:
    {
        "source_ein": "98-7654321",
        "target_ein": "11-1111111",
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024],
        "max_hops": 3
    }

    Returns:
    {
        "source_ein": "98-7654321",
        "target_ein": "11-1111111",
        "paths_found": 3,
        "pathways": [...]
    }
    """
    try:
        source_ein = request.get('source_ein')
        target_ein = request.get('target_ein')

        if not source_ein or not target_ein:
            raise HTTPException(
                status_code=400,
                detail="source_ein and target_ein required"
            )

        # Build graph
        graph_result = await build_network_graph(request)

        if not graph_result.get('success'):
            raise HTTPException(status_code=500, detail="Failed to build graph")

        # Rebuild graph for pathfinding
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=request.get('foundation_eins', []),
            tax_years=request.get('tax_years', [2022, 2023, 2024]),
            min_foundations=1
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Find pathways
        pathway_result = find_strategic_pathways(graph, source_ein, target_ein)

        return {
            "success": True,
            **pathway_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding connection paths: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_network_statistics(
    foundation_eins: List[str] = Query(..., description="Foundation EINs to analyze"),
    tax_years: List[int] = Query([2022, 2023, 2024], description="Tax years")
):
    """
    Get comprehensive network graph statistics.

    Query params:
    - foundation_eins: List of foundation EINs (required)
    - tax_years: List of tax years (default: 2022-2024)

    Returns comprehensive network metrics and statistics.
    """
    try:
        request = {
            'foundation_eins': foundation_eins,
            'tax_years': tax_years,
            'min_foundations': 1
        }

        graph_result = await build_network_graph(request)

        return {
            "success": True,
            "statistics": graph_result.get('statistics', {}),
            "nodes_count": graph_result.get('nodes_count', 0),
            "edges_count": graph_result.get('edges_count', 0)
        }

    except Exception as e:
        logger.error(f"Error getting network statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/graphml")
async def export_graphml(
    foundation_eins: List[str] = Query(..., description="Foundation EINs"),
    tax_years: List[int] = Query([2022, 2023, 2024], description="Tax years")
):
    """
    Export network graph to GraphML format (for Gephi/Cytoscape).

    Query params:
    - foundation_eins: List of foundation EINs (required)
    - tax_years: List of tax years (default: 2022-2024)

    Returns GraphML XML string.
    """
    try:
        from fastapi.responses import Response

        # Build graph
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=foundation_eins,
            tax_years=tax_years,
            min_foundations=1
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        if not bundling_output.success:
            raise HTTPException(status_code=500, detail="Failed to build graph")

        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Export to GraphML
        graphml_string = graph_builder.export_to_graphml()

        return Response(
            content=graphml_string,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=foundation_network_{datetime.now().strftime('%Y%m%d')}.graphml"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting GraphML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_json(
    foundation_eins: List[str] = Query(..., description="Foundation EINs"),
    tax_years: List[int] = Query([2022, 2023, 2024], description="Tax years")
):
    """
    Export network graph to JSON format (for D3.js/vis.js).

    Query params:
    - foundation_eins: List of foundation EINs (required)
    - tax_years: List of tax years (default: 2022-2024)

    Returns JSON with nodes and edges arrays.
    """
    try:
        # Build graph
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=foundation_eins,
            tax_years=tax_years,
            min_foundations=1
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        if not bundling_output.success:
            raise HTTPException(status_code=500, detail="Failed to build graph")

        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Export to JSON
        json_graph = graph_builder.export_to_json()

        return {
            "success": True,
            "graph": json_graph
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/influence/analyze")
async def analyze_influence(request: dict):
    """
    Analyze network influence for nodes or entire network.

    Input:
    {
        "foundation_eins": ["11-1111111", "22-2222222", ...],
        "tax_years": [2022, 2023, 2024],
        "node_id": "12-3456789",  // Optional - analyze specific node
        "top_influencers": 10  // Optional - return top N influencers
    }

    Returns influence analysis with PageRank, centrality metrics.
    """
    try:
        # Build graph
        from tools.foundation_grantee_bundling_tool.app import GranteeBundlingInput
        from tools.foundation_grantee_bundling_tool.app.bundling_tool import FoundationGranteeBundlingTool

        tool = FoundationGranteeBundlingTool()
        bundling_input = GranteeBundlingInput(
            foundation_eins=request.get('foundation_eins', []),
            tax_years=request.get('tax_years', [2022, 2023, 2024]),
            min_foundations=1
        )

        bundling_output = await tool.execute(bundling_input=bundling_input)

        if not bundling_output.success:
            raise HTTPException(status_code=500, detail="Failed to build graph")

        graph_builder = FoundationNetworkGraph()
        graph = graph_builder.build_from_bundling_results(bundling_output.data)

        # Analyze influence
        node_id = request.get('node_id')
        influence_result = analyze_network_influence(graph, node_id)

        # Get top influencers if requested
        if request.get('top_influencers'):
            analyzer = InfluenceAnalyzer(graph)
            top_influencers = analyzer.score_top_influencers(
                limit=request.get('top_influencers', 10)
            )
            influence_result['top_influencers'] = [inf.__dict__ for inf in top_influencers]

        return {
            "success": True,
            **influence_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing influence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def network_health_check():
    """Health check for foundation network endpoints."""
    try:
        db_service = FoundationGrantsDatabaseService()
        stats = db_service.get_grant_statistics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "grants_loaded": stats.get('total_grants', 0),
                "foundations_count": stats.get('unique_foundations', 0),
                "grantees_count": stats.get('unique_grantees', 0)
            }
        }

    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
