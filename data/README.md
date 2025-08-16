# Entity-Based Data Architecture

This directory contains the refactored data structure for the Catalynx grant research platform.

## Structure Overview

### source_data/
Raw entity data organized by type and identifier:
- `nonprofits/{EIN}/` - Nonprofit organizations by EIN
- `foundations/{foundation_id}/` - Foundation data by foundation ID  
- `corporations/{corp_id}/` - Corporate entity data
- `government/` - Government funding opportunities

### cache/
Shared computed data and indices:
- `networks/` - Raw network relationship data
- `indices/` - Search and similarity indices
- `market_data/` - Market-wide analysis

### profiles/
Profile-specific data and analysis:
- `profiles/` - Profile definitions
- `leads/` - Opportunity leads per profile
- `sessions/` - Discovery sessions per profile
- `analysis/{profile_id}/` - Profile-specific analysis results

## Benefits

- **Data Reusability**: Source data shared across profiles
- **Performance**: Entity-based organization enables faster lookups
- **Scalability**: Clear separation of concerns
- **Maintainability**: Predictable data organization
