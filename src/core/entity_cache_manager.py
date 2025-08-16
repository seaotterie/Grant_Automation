#!/usr/bin/env python3
"""
Entity-Based Cache Manager for New Data Architecture
Handles caching directly to entity-based directory structure instead of hash-based cache.
"""

import asyncio
import aiofiles
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of entities for caching"""
    NONPROFIT = "nonprofit"
    FOUNDATION = "foundation"
    CORPORATION = "corporation"
    GOVERNMENT_OPPORTUNITY = "government_opportunity"
    STATE_OPPORTUNITY = "state_opportunity"


class DataSourceType(str, Enum):
    """Types of data sources"""
    PROPUBLICA = "propublica"
    IRS_BMF = "irs_bmf"
    FORM_990 = "form_990"
    FORM_990_PF = "form_990_pf"
    GRANTS_GOV = "grants_gov"
    USASPENDING = "usaspending"
    FOUNDATION_DIRECTORY = "foundation_directory"
    VA_STATE_GRANTS = "va_state_grants"


@dataclass
class EntityCacheEntry:
    """Entity cache entry metadata"""
    entity_id: str
    entity_type: EntityType
    data_source: DataSourceType
    file_path: Path
    created_at: datetime
    last_updated: datetime
    content_hash: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'data_source': self.data_source.value,
            'file_path': str(self.file_path),
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'content_hash': self.content_hash,
            'metadata': self.metadata
        }


class EntityCacheManager:
    """
    Entity-based cache manager that writes directly to entity directory structure.
    
    Directory Structure:
    - data/source_data/nonprofits/{ein}/
        - propublica.json
        - bmf.json  
        - form_990.json
        - metadata.json
    - data/source_data/government/federal/grants_gov/{opportunity_id}/
        - opportunity.json
        - metadata.json
    - data/source_data/government/federal/usaspending/{award_id}/
        - award.json
        - metadata.json
    """
    
    def __init__(self, base_data_path: Path = None):
        self.base_data_path = base_data_path or Path("data")
        self.source_data_dir = self.base_data_path / "source_data"
        
        # Ensure base directories exist
        self.source_data_dir.mkdir(parents=True, exist_ok=True)
        self._create_entity_directories()
        
        # Track cache entries for reporting
        self.cache_entries: Dict[str, EntityCacheEntry] = {}
    
    def _create_entity_directories(self):
        """Create entity-based directory structure"""
        directories = [
            "nonprofits",
            "foundations", 
            "corporations",
            "government/federal/grants_gov",
            "government/federal/usaspending",
            "government/state/virginia/agencies",
            "government/state/virginia/historical_awards",
        ]
        
        for directory in directories:
            dir_path = self.source_data_dir / directory
            dir_path.mkdir(exist_ok=True, parents=True)
    
    def _extract_entity_id(self, data: Dict[str, Any], entity_type: EntityType, 
                          data_source: DataSourceType) -> Optional[str]:
        """Extract entity ID from data based on type and source"""
        
        if entity_type == EntityType.NONPROFIT:
            # Look for EIN in various formats
            ein_fields = ['ein', 'EIN', 'employer_id_number', 'organization_ein']
            for field in ein_fields:
                if field in data and data[field]:
                    ein = str(data[field]).strip()
                    # Clean EIN format (remove dashes, ensure 9 digits)
                    ein = re.sub(r'[^0-9]', '', ein)
                    if len(ein) == 9:
                        return ein
            
            # Try to extract from nested organization data
            if 'organization' in data:
                org_data = data['organization']
                for field in ein_fields:
                    if field in org_data and org_data[field]:
                        ein = str(org_data[field]).strip()
                        ein = re.sub(r'[^0-9]', '', ein)
                        if len(ein) == 9:
                            return ein
        
        elif entity_type == EntityType.GOVERNMENT_OPPORTUNITY:
            # Look for opportunity/grant IDs
            id_fields = ['opportunity_id', 'OpportunityID', 'funding_opportunity_number', 
                        'award_id', 'id', 'grant_id']
            for field in id_fields:
                if field in data and data[field]:
                    return str(data[field]).strip()
        
        elif entity_type == EntityType.FOUNDATION:
            # Look for foundation IDs (could be EIN or foundation directory ID)
            id_fields = ['foundation_id', 'id', 'ein', 'EIN']
            for field in id_fields:
                if field in data and data[field]:
                    return str(data[field]).strip()
        
        return None
    
    def _get_entity_directory(self, entity_id: str, entity_type: EntityType) -> Path:
        """Get directory path for entity"""
        if entity_type == EntityType.NONPROFIT:
            return self.source_data_dir / "nonprofits" / entity_id
        elif entity_type == EntityType.FOUNDATION:
            return self.source_data_dir / "foundations" / entity_id
        elif entity_type == EntityType.CORPORATION:
            return self.source_data_dir / "corporations" / entity_id
        elif entity_type == EntityType.GOVERNMENT_OPPORTUNITY:
            return self.source_data_dir / "government" / "federal" / "grants_gov" / entity_id
        elif entity_type == EntityType.STATE_OPPORTUNITY:
            return self.source_data_dir / "government" / "state" / "virginia" / "agencies" / entity_id
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    def _get_filename_for_source(self, data_source: DataSourceType) -> str:
        """Get filename for data source"""
        filename_mapping = {
            DataSourceType.PROPUBLICA: "propublica.json",
            DataSourceType.IRS_BMF: "bmf.json",
            DataSourceType.FORM_990: "form_990.json",
            DataSourceType.FORM_990_PF: "form_990_pf.json",
            DataSourceType.GRANTS_GOV: "opportunity.json",
            DataSourceType.USASPENDING: "award.json",
            DataSourceType.FOUNDATION_DIRECTORY: "foundation.json",
            DataSourceType.VA_STATE_GRANTS: "state_grant.json"
        }
        return filename_mapping.get(data_source, f"{data_source.value}.json")
    
    async def cache_entity_data(self, 
                               data: Dict[str, Any],
                               entity_type: EntityType,
                               data_source: DataSourceType,
                               entity_id: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Cache data for an entity in the appropriate directory structure.
        
        Args:
            data: The data to cache
            entity_type: Type of entity
            data_source: Source of the data
            entity_id: Optional explicit entity ID (auto-extracted if None)
            metadata: Optional additional metadata
            
        Returns:
            Entity ID if successful, None if failed
        """
        try:
            # Extract entity ID if not provided
            if not entity_id:
                entity_id = self._extract_entity_id(data, entity_type, data_source)
                if not entity_id:
                    logger.warning(f"Could not extract entity ID from {data_source.value} data")
                    return None
            
            # Get entity directory and ensure it exists
            entity_dir = self._get_entity_directory(entity_id, entity_type)
            entity_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories if needed for nonprofits
            if entity_type == EntityType.NONPROFIT:
                (entity_dir / "filings").mkdir(exist_ok=True)
                (entity_dir / "schedules").mkdir(exist_ok=True)
            
            # Get filename for this data source
            filename = self._get_filename_for_source(data_source)
            file_path = entity_dir / filename
            
            # Prepare data with metadata
            cache_data = {
                'data': data,
                'cached_at': datetime.now().isoformat(),
                'data_source': data_source.value,
                'entity_id': entity_id,
                'entity_type': entity_type.value
            }
            
            if metadata:
                cache_data['metadata'] = metadata
            
            # Write data to file
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, indent=2))
            
            # Calculate content hash
            content_str = json.dumps(data, sort_keys=True)
            import hashlib
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()
            
            # Create cache entry
            entry = EntityCacheEntry(
                entity_id=entity_id,
                entity_type=entity_type,
                data_source=data_source,
                file_path=file_path,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                content_hash=content_hash,
                metadata=metadata or {}
            )
            
            # Update entity metadata file
            await self._update_entity_metadata(entity_dir, entity_id, entity_type, entry)
            
            # Track in memory
            cache_key = f"{entity_type.value}:{entity_id}:{data_source.value}"
            self.cache_entries[cache_key] = entry
            
            logger.info(f"Cached {data_source.value} data for {entity_type.value} {entity_id}")
            return entity_id
            
        except Exception as e:
            logger.error(f"Failed to cache entity data: {e}")
            return None
    
    async def get_entity_data(self, 
                             entity_id: str,
                             entity_type: EntityType,
                             data_source: DataSourceType) -> Optional[Dict[str, Any]]:
        """
        Get cached data for an entity from specific source.
        
        Args:
            entity_id: The entity identifier
            entity_type: Type of entity
            data_source: Source of the data
            
        Returns:
            Cached data or None if not found
        """
        try:
            entity_dir = self._get_entity_directory(entity_id, entity_type)
            filename = self._get_filename_for_source(data_source)
            file_path = entity_dir / filename
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                cache_data = json.loads(content)
                
                # Return the actual data, not the cache wrapper
                return cache_data.get('data', cache_data)
                
        except Exception as e:
            logger.error(f"Failed to get entity data for {entity_id}: {e}")
            return None
    
    async def _update_entity_metadata(self, 
                                     entity_dir: Path, 
                                     entity_id: str,
                                     entity_type: EntityType,
                                     new_entry: EntityCacheEntry):
        """Update entity metadata file with new data source info"""
        metadata_file = entity_dir / "metadata.json"
        
        try:
            # Load existing metadata
            if metadata_file.exists():
                async with aiofiles.open(metadata_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    entity_metadata = json.loads(content)
            else:
                entity_metadata = {
                    'entity_id': entity_id,
                    'entity_type': entity_type.value,
                    'created_at': datetime.now().isoformat(),
                    'data_sources': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            # Update data sources
            entity_metadata['data_sources'][new_entry.data_source.value] = {
                'file_path': str(new_entry.file_path.name),  # Just filename, not full path
                'last_updated': new_entry.last_updated.isoformat(),
                'content_hash': new_entry.content_hash
            }
            entity_metadata['last_updated'] = datetime.now().isoformat()
            
            # Write updated metadata
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(entity_metadata, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to update entity metadata: {e}")
    
    async def get_entity_metadata(self, entity_id: str, entity_type: EntityType) -> Optional[Dict[str, Any]]:
        """Get metadata for an entity"""
        try:
            entity_dir = self._get_entity_directory(entity_id, entity_type)
            metadata_file = entity_dir / "metadata.json"
            
            if not metadata_file.exists():
                return None
            
            async with aiofiles.open(metadata_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"Failed to get entity metadata for {entity_id}: {e}")
            return None
    
    async def list_entities(self, entity_type: EntityType) -> List[str]:
        """List all entity IDs of a specific type"""
        try:
            if entity_type == EntityType.NONPROFIT:
                base_dir = self.source_data_dir / "nonprofits"
            elif entity_type == EntityType.FOUNDATION:
                base_dir = self.source_data_dir / "foundations"
            elif entity_type == EntityType.CORPORATION:
                base_dir = self.source_data_dir / "corporations"
            elif entity_type == EntityType.GOVERNMENT_OPPORTUNITY:
                base_dir = self.source_data_dir / "government" / "federal" / "grants_gov"
            elif entity_type == EntityType.STATE_OPPORTUNITY:
                base_dir = self.source_data_dir / "government" / "state" / "virginia" / "agencies"
            else:
                return []
            
            if not base_dir.exists():
                return []
            
            # Return directory names (entity IDs)
            return [d.name for d in base_dir.iterdir() if d.is_dir()]
            
        except Exception as e:
            logger.error(f"Failed to list entities of type {entity_type}: {e}")
            return []
    
    async def cache_nonprofit_propublica_data(self, propublica_data: Dict[str, Any], ein: str = None) -> Optional[str]:
        """Convenience method for caching ProPublica nonprofit data"""
        return await self.cache_entity_data(
            data=propublica_data,
            entity_type=EntityType.NONPROFIT,
            data_source=DataSourceType.PROPUBLICA,
            entity_id=ein
        )
    
    async def cache_grants_gov_opportunity(self, opportunity_data: Dict[str, Any], opportunity_id: str = None) -> Optional[str]:
        """Convenience method for caching Grants.gov opportunity data"""
        return await self.cache_entity_data(
            data=opportunity_data,
            entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
            data_source=DataSourceType.GRANTS_GOV,
            entity_id=opportunity_id
        )
    
    async def cache_usaspending_award(self, award_data: Dict[str, Any], award_id: str = None) -> Optional[str]:
        """Convenience method for caching USASpending award data"""
        return await self.cache_entity_data(
            data=award_data,
            entity_type=EntityType.GOVERNMENT_OPPORTUNITY,
            data_source=DataSourceType.USASPENDING,
            entity_id=award_id
        )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'entity_counts': {},
            'total_entities': 0,
            'data_source_counts': {}
        }
        
        for entity_type in EntityType:
            entities = await self.list_entities(entity_type)
            count = len(entities)
            stats['entity_counts'][entity_type.value] = count
            stats['total_entities'] += count
        
        return stats


# Global entity cache manager instance
_entity_cache_manager: Optional[EntityCacheManager] = None


def get_entity_cache_manager() -> EntityCacheManager:
    """Get or create global entity cache manager instance"""
    global _entity_cache_manager
    if _entity_cache_manager is None:
        _entity_cache_manager = EntityCacheManager()
    return _entity_cache_manager