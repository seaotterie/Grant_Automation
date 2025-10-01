#!/usr/bin/env python3
"""
Catalynx Data Transformation Pipeline
Comprehensive data transformation system for grant research platform

Main Components:
- DataTransformationService: Core transformation logic
- NormalizedDatabaseManager: Database integration
- DataTransformationIntegrator: Main orchestration service
- Pydantic Models: Complete type system

Usage:
    from src.data_transformation import CatalynxDataTransformer
    from src.database.database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    transformer = CatalynxDataTransformer(db_manager)
    
    # Transform profile data
    result = transformer.transform_profile_data(
        profile_id="profile_123",
        web_scraping_results=scraping_data,
        board_members_json=board_data
    )
"""

from .models import (
    # Input models
    WebScrapingResults, DatabaseJSONFields, BoardMemberData,
    ScrapedLeadership, ScrapedProgram, ScrapedContact, ScrapedExtractedInfo,
    
    # Output models
    Person, ParsedName, OrganizationRole, Program, Contact, BoardConnection,
    
    # Result models
    TransformationResult, TransformationStats, ValidationError, DuplicationMatch,
    
    # Configuration
    TransformationConfig, NameParsingConfig, DeduplicationConfig, ValidationConfig,
    
    # Enums
    DataSource, ContactType, ProgramType, ValidationStatus
)

from .transformation_service import (
    DataTransformationService, NameParser, DataDeduplicator
)

from .database_integration import (
    NormalizedDatabaseManager, DataTransformationIntegrator
)

from .main_service import CatalynxDataTransformer

__all__ = [
    # Main service
    'CatalynxDataTransformer',
    
    # Core services
    'DataTransformationService',
    'NormalizedDatabaseManager', 
    'DataTransformationIntegrator',
    'NameParser',
    'DataDeduplicator',
    
    # Input models
    'WebScrapingResults',
    'DatabaseJSONFields',
    'BoardMemberData',
    'ScrapedLeadership',
    'ScrapedProgram',
    'ScrapedContact',
    'ScrapedExtractedInfo',
    
    # Output models
    'Person',
    'ParsedName',
    'OrganizationRole',
    'Program',
    'Contact',
    'BoardConnection',
    
    # Result models
    'TransformationResult',
    'TransformationStats',
    'ValidationError',
    'DuplicationMatch',
    
    # Configuration
    'TransformationConfig',
    'NameParsingConfig',
    'DeduplicationConfig',
    'ValidationConfig',
    
    # Enums
    'DataSource',
    'ContactType',
    'ProgramType',
    'ValidationStatus'
]

__version__ = "1.0.0"
__author__ = "Catalynx Team"
__description__ = "Data transformation pipeline for Catalynx grant research platform"
