# Network Intelligence Tool

**12-Factor Compliant Board Network Analysis Tool**

## Purpose

Board network analysis and relationship mapping for strategic cultivation opportunities.

## Features

- **Board Member Profiling**: Centrality, influence, connections
- **Centrality Metrics**: Degree, betweenness, closeness, eigenvector
- **Cluster Identification**: Network community detection
- **Relationship Pathways**: Direct and indirect connection mapping
- **Strategic Connections**: High-value cultivation opportunities
- **Funder Analysis**: Target funder connection assessment

## Usage

```python
from tools.network_intelligence_tool.app import analyze_network_intelligence

board_members = [
    {"name": "John Smith", "title": "Board Chair", "affiliations": "XYZ Foundation, ABC Corp"},
    {"name": "Jane Doe", "title": "Board Member", "affiliations": "Community Foundation"}
]

result = await analyze_network_intelligence(
    organization_ein="12-3456789",
    organization_name="Example Nonprofit",
    board_members=board_members,
    target_funder_name="Smith Foundation",
    target_funder_board=["John Smith", "Mary Johnson"]
)

if result.is_success():
    network = result.data
    print(f"Network Size: {network.network_analysis.network_size}")
    print(f"Network Density: {network.network_analysis.network_density:.2f}")

    if network.funder_connection_analysis:
        print(f"\nFunder Connections: {network.funder_connection_analysis.direct_connection_count} direct")
        print(f"Connection Strength: {network.funder_connection_analysis.overall_connection_strength.value}")
```

## Cost

**$0.04 per analysis**

## Replaced Processors

- ✅ `board_network_analyzer.py`
- ✅ `enhanced_network_analyzer.py`
- ✅ Root-level `optimized_network_analyzer.py`
