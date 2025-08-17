# Discovery Engine

## Overview
The Discovery Engine orchestrates multi-track opportunity discovery across nonprofit, government, state, and commercial funding sources using entity-based data architecture.

## Core Components

### Entity Discovery Service
- **File**: `entity_discovery_service.py`
- **Purpose**: Advanced discovery leveraging entity-based data and shared analytics
- **Features**: Cross-entity analysis, profile-specific matching, intelligent opportunity scoring

### Discovery Engine
- **File**: `discovery_engine.py` 
- **Purpose**: Multi-track orchestration with priority-based processing
- **Tracks**: Nonprofit, Government, State, Commercial
- **Features**: Smart resource allocation, pipeline coordination

### Track-Specific Discoverers
- **Nonprofit Discoverer**: ProPublica 990 data analysis
- **Government Discoverer**: Grants.gov + USASpending.gov integration
- **State Discoverer**: Virginia state agency grants (10 agencies)
- **Commercial Discoverer**: Foundation Directory + CSR programs

## Entity-Based Architecture

### Data Organization
- **Nonprofit Entities**: `data/source_data/nonprofits/{EIN}/`
- **Government Opportunities**: `data/source_data/government/{OPP_ID}/`
- **Foundation Entities**: `data/source_data/foundations/{FOUNDATION_ID}/`

### Shared Analytics Integration
- Financial health analysis computed once per entity
- Network influence scoring reused across profiles
- Cross-entity relationship identification

## Usage

```python
from src.discovery.entity_discovery_service import EntityDiscoveryService

# Initialize discovery service
discovery_service = EntityDiscoveryService()

# Execute entity-based discovery
results = await discovery_service.discover_opportunities(
    profile_id="profile_123",
    entity_filters={"type": "nonprofit", "state": "VA"},
    discovery_config={"max_results": 50}
)
```

## Configuration

### Discovery Settings
- **Max Results per Track**: 50 opportunities
- **Priority Processing**: High-value matches first
- **Entity Cache TTL**: 24 hours
- **Async Concurrency**: 5 concurrent processors

### Performance Optimization
- Entity-based caching reduces redundant API calls
- Shared analytics minimize computational overhead
- Priority-based processing optimizes resource allocation