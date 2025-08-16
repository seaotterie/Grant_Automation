"""
Data Migration Framework for Entity-Based Architecture Refactoring

This package provides tools for migrating from the current hash-based cache
system to an entity-based data organization structure.
"""

from .migration_framework import (
    DataMigrationFramework,
    MigrationStep,
    MigrationRecord,
    MigrationStatus,
    create_entity_directories
)

from .entity_extractor import (
    EntityExtractor,
    EntityType,
    EntityIdentification
)

from .setup_structure import (
    setup_directory_structure,
    setup_metadata_files
)

__version__ = "1.0.0"
__all__ = [
    "DataMigrationFramework",
    "MigrationStep", 
    "MigrationRecord",
    "MigrationStatus",
    "EntityExtractor",
    "EntityType",
    "EntityIdentification",
    "setup_directory_structure",
    "setup_metadata_files",
    "create_entity_directories"
]