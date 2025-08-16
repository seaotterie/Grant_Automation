#!/usr/bin/env python3
"""
Directory Structure Setup for Entity-Based Architecture

Creates the new directory structure and initializes metadata files.
"""

import json
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import logging

from .migration_framework import create_entity_directories


def setup_directory_structure(base_path: Path, create_metadata: bool = True) -> Dict[str, Any]:
    """
    Create the complete entity-based directory structure
    """
    logger = logging.getLogger(__name__)
    
    # Create main directories
    created_dirs = create_entity_directories(base_path)
    
    # Additional specialized directories
    additional_dirs = [
        "source_data/nonprofits/indices",
        "source_data/foundations/indices", 
        "source_data/corporations/indices",
        "source_data/government/indices",
        "cache/networks/board_connections",
        "cache/networks/foundation_relationships",
        "cache/networks/government_networks",
        "cache/indices/similarity",
        "cache/indices/keywords",
        "cache/indices/geographic",
        "cache/market_data/trends",
        "cache/market_data/sectors",
        "cache/market_data/geographic",
        "profiles/analysis/templates"
    ]
    
    for directory in additional_dirs:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True, parents=True)
        created_dirs.append(dir_path)
    
    logger.info(f"Created {len(created_dirs)} directories for entity-based structure")
    
    if create_metadata:
        setup_metadata_files(base_path)
    
    return {
        'created_directories': [str(d) for d in created_dirs],
        'total_count': len(created_dirs),
        'base_path': str(base_path),
        'created_at': datetime.now().isoformat()
    }


def setup_metadata_files(base_path: Path):
    """
    Create metadata and index files for the new structure
    """
    
    # Directory structure documentation
    structure_doc = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "description": "Entity-based data architecture for Catalynx grant research platform",
        "structure": {
            "source_data": {
                "description": "Raw entity data organized by type and ID",
                "nonprofits": {
                    "organization": "EIN-based directories",
                    "contains": ["bmf.json", "filings/", "schedules/", "propublica.json", "board_members.json"]
                },
                "foundations": {
                    "organization": "Foundation ID-based directories", 
                    "contains": ["profile.json", "grants_history.json", "board_members.json", "csr_programs.json"]
                },
                "corporations": {
                    "organization": "Corporate ID-based directories",
                    "contains": ["profile.json", "csr_programs.json", "foundation_arms.json", "giving_history.json"]
                },
                "government": {
                    "organization": "Opportunity/Award ID-based directories",
                    "contains": ["federal/grants_gov/", "federal/usaspending/", "state/virginia/"]
                }
            },
            "cache": {
                "description": "Shared computed data and indices",
                "networks": "Raw network relationship data",
                "indices": "Search and similarity indices", 
                "market_data": "Market-wide analysis data"
            },
            "profiles": {
                "description": "Profile-specific data and analysis",
                "profiles": "Profile definitions",
                "leads": "Opportunity leads per profile",
                "sessions": "Discovery sessions per profile",
                "analysis": "Profile-specific analysis results"
            }
        }
    }
    
    structure_file = base_path / "data_structure.json"
    with open(structure_file, 'w') as f:
        json.dump(structure_doc, f, indent=2)
    
    # Create index template files
    create_index_templates(base_path)
    
    # Create README files for major directories
    create_readme_files(base_path)


def create_index_templates(base_path: Path):
    """
    Create template index files for entity organization
    """
    
    # Nonprofit EIN index template
    nonprofit_index = {
        "version": "1.0.0",
        "description": "Index of nonprofit organizations by EIN",
        "last_updated": datetime.now().isoformat(),
        "total_organizations": 0,
        "organizations": {
            # "123456789": {
            #     "name": "Example Nonprofit",
            #     "ntee_code": "A01",
            #     "data_files": ["bmf.json", "990_2023.json"],
            #     "last_updated": "2024-01-01T00:00:00"
            # }
        }
    }
    
    nonprofit_index_file = base_path / "source_data" / "nonprofits" / "index.json"
    with open(nonprofit_index_file, 'w') as f:
        json.dump(nonprofit_index, f, indent=2)
    
    # Foundation index template
    foundation_index = {
        "version": "1.0.0",
        "description": "Index of foundations by foundation ID",
        "last_updated": datetime.now().isoformat(),
        "total_foundations": 0,
        "foundations": {}
    }
    
    foundation_index_file = base_path / "source_data" / "foundations" / "index.json"
    with open(foundation_index_file, 'w') as f:
        json.dump(foundation_index, f, indent=2)
    
    # Government opportunities index template
    government_index = {
        "version": "1.0.0",
        "description": "Index of government funding opportunities",
        "last_updated": datetime.now().isoformat(),
        "federal": {
            "grants_gov": {"total_opportunities": 0, "opportunities": {}},
            "usaspending": {"total_awards": 0, "awards": {}}
        },
        "state": {
            "virginia": {"total_opportunities": 0, "opportunities": {}}
        }
    }
    
    government_index_file = base_path / "source_data" / "government" / "index.json"
    with open(government_index_file, 'w') as f:
        json.dump(government_index, f, indent=2)


def create_readme_files(base_path: Path):
    """
    Create README files documenting the new structure
    """
    
    # Main README
    main_readme = """# Entity-Based Data Architecture

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
"""
    
    readme_file = base_path / "README.md"
    with open(readme_file, 'w') as f:
        f.write(main_readme)
    
    # Source data README
    source_readme = """# Source Data Directory

Contains raw entity data organized by type and identifier.

## Nonprofits
- Directory structure: `nonprofits/{EIN}/`
- Contains: IRS data, 990 filings, schedules, ProPublica data, board members

## Foundations  
- Directory structure: `foundations/{foundation_id}/`
- Contains: Foundation profiles, grants history, board members, CSR programs

## Corporations
- Directory structure: `corporations/{corp_id}/`
- Contains: Corporate profiles, CSR programs, foundation arms, giving history

## Government
- Directory structure: `government/{source}/{type}/`
- Contains: Federal and state funding opportunities and historical awards
"""
    
    source_readme_file = base_path / "source_data" / "README.md"
    with open(source_readme_file, 'w') as f:
        f.write(source_readme)


if __name__ == "__main__":
    # Setup directory structure
    base_path = Path("data")
    result = setup_directory_structure(base_path)
    
    print(f"Directory setup complete:")
    print(f"- Created {result['total_count']} directories")
    print(f"- Base path: {result['base_path']}")
    print(f"- Created at: {result['created_at']}")