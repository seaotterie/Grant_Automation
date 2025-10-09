"""
Foundation Network Intelligence - Demo Script
Demonstrates Phase 1-3 capabilities with example data.

Usage:
    python examples/foundation_network_demo.py
"""

import sys
from pathlib import Path
import asyncio
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.foundation_network_graph import (
    FoundationNetworkGraph,
    NetworkQueryEngine
)
from src.analytics.network_pathfinder import (
    NetworkPathfinder,
    InfluenceAnalyzer
)


def create_demo_bundling_output():
    """
    Create realistic demo data for foundation network analysis.

    Scenario: 5 foundations in education/youth development space
    """
    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class FundingSource:
        foundation_ein: str
        foundation_name: str
        grant_amount: float
        grant_year: int
        grant_purpose: str = ""

    @dataclass
    class BundledGrantee:
        grantee_ein: str
        grantee_name: str
        funder_count: int
        total_funding: float
        average_grant_size: float
        funding_stability: str
        first_grant_year: int
        last_grant_year: int
        funding_sources: List[FundingSource]
        common_purposes: List[str] = field(default_factory=list)

    @dataclass
    class BundlingOutput:
        foundation_eins: List[str]
        bundled_grantees: List[BundledGrantee]
        total_foundations_analyzed: int
        total_unique_grantees: int

    # Define 5 foundations
    foundations = {
        "81-1234567": "Gates Foundation (Education)",
        "82-2345678": "Chan Zuckerberg Initiative",
        "83-3456789": "Walton Family Foundation",
        "84-4567890": "Bloomberg Philanthropies",
        "85-5678901": "Ford Foundation"
    }

    # Create 10 grantees with various co-funding patterns
    grantees = [
        BundledGrantee(
            grantee_ein="91-1111111",
            grantee_name="National Urban League",
            funder_count=4,
            total_funding=2500000,
            average_grant_size=625000,
            funding_stability="stable",
            first_grant_year=2021,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 800000, 2023, "Education equity"),
                FundingSource("82-2345678", foundations["82-2345678"], 600000, 2022, "STEM programs"),
                FundingSource("84-4567890", foundations["84-4567890"], 550000, 2023, "Youth development"),
                FundingSource("85-5678901", foundations["85-5678901"], 550000, 2021, "Social justice education")
            ],
            common_purposes=["education", "youth development", "equity"]
        ),
        BundledGrantee(
            grantee_ein="92-2222222",
            grantee_name="Teach For America",
            funder_count=5,
            total_funding=5200000,
            average_grant_size=1040000,
            funding_stability="growing",
            first_grant_year=2020,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 1500000, 2023, "Teacher recruitment"),
                FundingSource("82-2345678", foundations["82-2345678"], 1200000, 2023, "STEM teacher training"),
                FundingSource("83-3456789", foundations["83-3456789"], 1000000, 2022, "Charter school support"),
                FundingSource("84-4567890", foundations["84-4567890"], 800000, 2021, "Urban education"),
                FundingSource("85-5678901", foundations["85-5678901"], 700000, 2020, "Education reform")
            ],
            common_purposes=["education", "teacher training", "reform"]
        ),
        BundledGrantee(
            grantee_ein="93-3333333",
            grantee_name="Boys & Girls Clubs of America",
            funder_count=3,
            total_funding=1800000,
            average_grant_size=600000,
            funding_stability="stable",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 700000, 2023, "After-school programs"),
                FundingSource("84-4567890", foundations["84-4567890"], 600000, 2023, "Youth services"),
                FundingSource("85-5678901", foundations["85-5678901"], 500000, 2022, "Community programs")
            ],
            common_purposes=["youth development", "after-school", "community"]
        ),
        BundledGrantee(
            grantee_ein="94-4444444",
            grantee_name="Khan Academy",
            funder_count=3,
            total_funding=3500000,
            average_grant_size=1166667,
            funding_stability="growing",
            first_grant_year=2021,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 1500000, 2023, "Online learning platform"),
                FundingSource("82-2345678", foundations["82-2345678"], 1200000, 2022, "Personalized learning"),
                FundingSource("84-4567890", foundations["84-4567890"], 800000, 2021, "Education technology")
            ],
            common_purposes=["education", "technology", "online learning"]
        ),
        BundledGrantee(
            grantee_ein="95-5555555",
            grantee_name="Code.org",
            funder_count=2,
            total_funding=1800000,
            average_grant_size=900000,
            funding_stability="stable",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("82-2345678", foundations["82-2345678"], 1000000, 2023, "CS education"),
                FundingSource("84-4567890", foundations["84-4567890"], 800000, 2022, "STEM diversity")
            ],
            common_purposes=["computer science", "STEM", "diversity"]
        ),
        BundledGrantee(
            grantee_ein="96-6666666",
            grantee_name="College Board",
            funder_count=3,
            total_funding=2200000,
            average_grant_size=733333,
            funding_stability="stable",
            first_grant_year=2021,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 900000, 2023, "AP program expansion"),
                FundingSource("83-3456789", foundations["83-3456789"], 700000, 2022, "College access"),
                FundingSource("84-4567890", foundations["84-4567890"], 600000, 2021, "Student assessment")
            ],
            common_purposes=["college access", "assessment", "AP programs"]
        ),
        BundledGrantee(
            grantee_ein="97-7777777",
            grantee_name="KIPP (Knowledge Is Power Program)",
            funder_count=4,
            total_funding=3200000,
            average_grant_size=800000,
            funding_stability="stable",
            first_grant_year=2020,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("81-1234567", foundations["81-1234567"], 1000000, 2023, "Charter network support"),
                FundingSource("83-3456789", foundations["83-3456789"], 900000, 2022, "School expansion"),
                FundingSource("84-4567890", foundations["84-4567890"], 700000, 2021, "College prep"),
                FundingSource("85-5678901", foundations["85-5678901"], 600000, 2020, "Education equity")
            ],
            common_purposes=["charter schools", "college prep", "equity"]
        ),
        BundledGrantee(
            grantee_ein="98-8888888",
            grantee_name="Success Academy Charter Schools",
            funder_count=2,
            total_funding=1400000,
            average_grant_size=700000,
            funding_stability="stable",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("83-3456789", foundations["83-3456789"], 800000, 2023, "Charter expansion"),
                FundingSource("84-4567890", foundations["84-4567890"], 600000, 2022, "Urban schools")
            ],
            common_purposes=["charter schools", "urban education"]
        ),
        BundledGrantee(
            grantee_ein="99-9999999",
            grantee_name="Girls Who Code",
            funder_count=2,
            total_funding=1200000,
            average_grant_size=600000,
            funding_stability="growing",
            first_grant_year=2022,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("82-2345678", foundations["82-2345678"], 700000, 2023, "CS diversity"),
                FundingSource("85-5678901", foundations["85-5678901"], 500000, 2022, "Gender equity in tech")
            ],
            common_purposes=["computer science", "diversity", "gender equity"]
        ),
        BundledGrantee(
            grantee_ein="90-1010101",
            grantee_name="DonorsChoose",
            funder_count=1,
            total_funding=500000,
            average_grant_size=500000,
            funding_stability="new",
            first_grant_year=2023,
            last_grant_year=2023,
            funding_sources=[
                FundingSource("84-4567890", foundations["84-4567890"], 500000, 2023, "Teacher support platform")
            ],
            common_purposes=["teacher support", "crowdfunding"]
        )
    ]

    return BundlingOutput(
        foundation_eins=list(foundations.keys()),
        bundled_grantees=grantees,
        total_foundations_analyzed=5,
        total_unique_grantees=10
    )


def print_section_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_graph_construction():
    """Demonstrate graph construction"""
    print_section_header("PHASE 3 DEMO: Foundation Network Graph Construction")

    # Create demo data
    print("Creating demo data (5 foundations, 10 grantees)...")
    bundling_output = create_demo_bundling_output()

    # Build graph
    print("\nBuilding foundation-grantee bipartite network graph...")
    graph_builder = FoundationNetworkGraph()
    graph = graph_builder.build_from_bundling_results(bundling_output)

    # Get statistics
    stats = graph_builder.get_network_statistics()

    print(f"\n[SUCCESS] Graph constructed successfully!")
    print(f"   - Nodes: {stats['total_nodes']}")
    print(f"   - Edges: {stats['total_edges']}")
    print(f"   - Foundations: {stats['total_foundations']}")
    print(f"   - Grantees: {stats['total_grantees']}")
    print(f"   - Total funding: ${stats['total_grant_amount']:,.0f}")
    print(f"   - Average grant: ${stats['average_grant_size']:,.0f}")
    print(f"   - Network density: {stats['network_density']:.3f}")

    return graph, graph_builder


def demo_co_funder_queries(graph):
    """Demonstrate co-funder queries"""
    print_section_header("CO-FUNDER DETECTION")

    query_engine = NetworkQueryEngine(graph)

    # Query for Teach For America (most connected grantee)
    print("Query: Who funds Teach For America?")
    print("Grantee EIN: 92-2222222\n")

    co_funders = query_engine.find_co_funders("92-2222222")

    print(f"Found {len(co_funders)} co-funders:\n")

    for i, funder in enumerate(co_funders, 1):
        print(f"{i}. {funder['foundation_name']}")
        print(f"   EIN: {funder['foundation_ein']}")
        print(f"   Total funding: ${funder['total_funding']:,.0f}")
        print(f"   Grants: {funder['grant_count']}")
        print(f"   Years: {funder['years']}")
        print(f"   Avg grant: ${funder['average_grant']:,.0f}")
        print()


def demo_shared_grantees(graph):
    """Demonstrate shared grantee analysis"""
    print_section_header("SHARED GRANTEE ANALYSIS")

    query_engine = NetworkQueryEngine(graph)

    # Compare Gates Foundation and Chan Zuckerberg Initiative
    foundation1 = "81-1234567"
    foundation2 = "82-2345678"

    print(f"Query: Which organizations do these two foundations both fund?")
    print(f"Foundation 1: Gates Foundation (Education) - {foundation1}")
    print(f"Foundation 2: Chan Zuckerberg Initiative - {foundation2}\n")

    shared = query_engine.find_shared_grantees(foundation1, foundation2)

    print(f"Found {len(shared)} shared grantees:\n")

    for i, grantee in enumerate(shared, 1):
        print(f"{i}. {grantee['grantee_name']}")
        print(f"   EIN: {grantee['grantee_ein']}")
        print(f"   Gates funding: ${grantee['foundation_1_funding']:,.0f}")
        print(f"   CZI funding: ${grantee['foundation_2_funding']:,.0f}")
        print(f"   Total co-funding: ${grantee['total_co_funding']:,.0f}")
        print()


def demo_pathfinding(graph):
    """Demonstrate strategic pathfinding"""
    print_section_header("STRATEGIC PATHFINDING")

    pathfinder = NetworkPathfinder(graph)

    # Find path from National Urban League to Walton Family Foundation
    source = "91-1111111"  # National Urban League
    target = "83-3456789"  # Walton Family Foundation

    print("Query: How can National Urban League connect to Walton Family Foundation?")
    print(f"Source: National Urban League ({source})")
    print(f"Target: Walton Family Foundation ({target})\n")

    paths = pathfinder.find_board_pathways(source, target)

    if paths:
        print(f"Found {len(paths)} pathway(s):\n")

        for i, path in enumerate(paths, 1):
            print(f"Pathway {i}:")
            print(f"  Length: {path.path_length} hops")
            print(f"  Strength: ${path.path_strength:,.0f}")
            print(f"  Route: {' -> '.join([graph.nodes[n].get('name', n)[:30] for n in path.path_nodes])}")
            print(f"\n  Description:")
            print(f"  {path.path_description}\n")
            print(f"  Cultivation Strategy:")
            print(f"  {path.cultivation_strategy}\n")
    else:
        print("No pathways found.")


def demo_influence_analysis(graph):
    """Demonstrate influence scoring"""
    print_section_header("NETWORK INFLUENCE ANALYSIS")

    analyzer = InfluenceAnalyzer(graph)

    # Get top influencers
    print("Query: Who are the most influential nodes in this network?\n")

    top_influencers = analyzer.score_top_influencers(limit=5)

    print(f"Top {len(top_influencers)} Influencers:\n")

    for i, influencer in enumerate(top_influencers, 1):
        print(f"{i}. {influencer.node_name}")
        print(f"   Type: {influencer.node_type}")
        print(f"   Degree centrality: {influencer.degree_centrality:.3f}")
        print(f"   PageRank score: {influencer.pagerank_score:.4f}")
        print(f"   Influence tier: {influencer.influence_tier.upper()}")
        print(f"   Assessment: {influencer.influence_interpretation}")
        print()

    # Get influence distribution
    print("\nInfluence Distribution:")
    distribution = analyzer.get_influence_distribution()

    print(f"  High influence: {distribution['high_influence_count']} nodes ({distribution['high_influence_percentage']:.1f}%)")
    print(f"  Medium influence: {distribution['medium_influence_count']} nodes")
    print(f"  Low influence: {distribution['low_influence_count']} nodes")


def demo_export_functionality(graph_builder):
    """Demonstrate export capabilities"""
    print_section_header("EXPORT & VISUALIZATION")

    # JSON export
    print("Exporting to JSON format (for D3.js/vis.js)...")
    json_graph = graph_builder.export_to_json()

    print(f"\n[SUCCESS] JSON Export:")
    print(f"   Nodes: {len(json_graph['nodes'])}")
    print(f"   Edges: {len(json_graph['edges'])}")
    print(f"   Format: Ready for web visualization\n")

    # Show sample node
    sample_node = json_graph['nodes'][0]
    print("Sample node structure:")
    print(json.dumps({k: v for k, v in list(sample_node.items())[:5]}, indent=2))

    # GraphML export
    print("\nExporting to GraphML format (for Gephi/Cytoscape)...")
    graphml_string = graph_builder.export_to_graphml()

    print(f"\n[SUCCESS] GraphML Export:")
    print(f"   Size: {len(graphml_string)} characters")
    print(f"   Format: Ready for Gephi/Cytoscape import")
    print(f"   Sample: {graphml_string[:100]}...")


def demo_portfolio_analysis(graph):
    """Demonstrate foundation portfolio analysis"""
    print_section_header("FOUNDATION PORTFOLIO ANALYSIS")

    query_engine = NetworkQueryEngine(graph)

    # Analyze Gates Foundation portfolio
    foundation = "81-1234567"

    print(f"Query: What is the complete grantee portfolio for Gates Foundation?")
    print(f"Foundation EIN: {foundation}\n")

    portfolio = query_engine.get_grantee_portfolio(foundation)

    print(f"Portfolio Overview:")
    print(f"  Total grantees: {portfolio['total_grantees']}")
    print(f"  Total funding: ${portfolio['total_funding']:,.0f}")
    print(f"  Total grants: {portfolio['total_grants']}")
    print(f"  Average grant size: ${portfolio['average_grant_size']:,.0f}\n")

    print(f"Grantees (sorted by funding):\n")

    for i, grantee in enumerate(portfolio['grantees'][:5], 1):  # Top 5
        print(f"{i}. {grantee['grantee_name']}")
        print(f"   Total funding: ${grantee['total_funding']:,.0f}")
        print(f"   Grants: {grantee['grant_count']}")
        print(f"   Years: {grantee['years']}")
        print()


def main():
    """Run complete demo"""
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + " " * 78 + "|")
    print("|" + "  Foundation Network Intelligence - Phase 3 Demonstration".center(78) + "|")
    print("|" + " " * 78 + "|")
    print("+" + "=" * 78 + "+")

    # Build graph
    graph, graph_builder = demo_graph_construction()

    # Run demos
    demo_co_funder_queries(graph)
    demo_shared_grantees(graph)
    demo_portfolio_analysis(graph)
    demo_pathfinding(graph)
    demo_influence_analysis(graph)
    demo_export_functionality(graph_builder)

    # Summary
    print_section_header("DEMO COMPLETE")
    print("[SUCCESS] All Phase 3 capabilities demonstrated successfully!\n")
    print("Key Features:")
    print("  - Bipartite graph construction (foundations <-> grantees)")
    print("  - Co-funder detection")
    print("  - Shared grantee analysis")
    print("  - Strategic pathfinding with cultivation strategies")
    print("  - Network influence scoring (PageRank, centrality)")
    print("  - Export to GraphML (Gephi) and JSON (D3.js)")
    print("  - Foundation portfolio analysis\n")

    print("Next Steps:")
    print("  1. Run with real foundation data from 990-PF filings")
    print("  2. Visualize networks in Gephi or D3.js")
    print("  3. Integrate with BMF data for enrichment")
    print("  4. Deploy REST API for web access\n")


if __name__ == '__main__':
    main()
