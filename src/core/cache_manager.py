#!/usr/bin/env python3
"""
Centralized Cache Manager System
Handles intelligent caching of downloads and expensive operations to prevent redundant work across profiles
"""

import asyncio
import aiofiles
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Types of cached data"""
    XML_DOWNLOAD = "xml_download"
    JSON_DOWNLOAD = "json_download" 
    API_RESPONSE = "api_response"
    PROCESSED_DATA = "processed_data"
    AI_ANALYSIS = "ai_analysis"
    NETWORK_ANALYSIS = "network_analysis"


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    cache_key: str
    cache_type: CacheType
    content_hash: str
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime]
    file_path: Optional[Path]
    metadata: Dict[str, Any]
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        # Convert Path to string
        if self.file_path:
            data['file_path'] = str(self.file_path)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        data = data.copy()
        # Convert ISO format back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        else:
            data['expires_at'] = None
        # Convert string back to Path
        if data.get('file_path'):
            data['file_path'] = Path(data['file_path'])
        else:
            data['file_path'] = None
        return cls(**data)


class CacheManager:
    """Centralized cache management system"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache")
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.cache_entries: Dict[str, CacheEntry] = {}
        
        # Cache configuration
        self.default_ttl = timedelta(hours=24)  # 24 hour default TTL
        self.max_cache_size = 1024 * 1024 * 1024  # 1GB max cache size
        self.cleanup_interval = timedelta(hours=6)  # Cleanup every 6 hours
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache metadata
        self._load_cache_metadata()
    
    def _load_cache_metadata(self) -> None:
        """Load cache metadata from disk"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.cache_entries = {
                        key: CacheEntry.from_dict(data) 
                        for key, data in metadata.items()
                    }
                logger.info(f"Loaded {len(self.cache_entries)} cache entries")
            else:
                self.cache_entries = {}
        except Exception as e:
            logger.error(f"Failed to load cache metadata: {e}")
            self.cache_entries = {}
    
    def _save_cache_metadata(self) -> None:
        """Save cache metadata to disk"""
        try:
            metadata = {
                key: entry.to_dict() 
                for key, entry in self.cache_entries.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _generate_cache_key(self, 
                          identifier: str, 
                          cache_type: CacheType,
                          profile_independent: bool = True) -> str:
        """Generate a cache key for the given parameters"""
        key_components = [cache_type.value, identifier]
        if not profile_independent:
            # Include some profile-specific component if needed
            pass
        return hashlib.sha256("|".join(key_components).encode()).hexdigest()
    
    def _generate_content_hash(self, content: Union[str, bytes]) -> str:
        """Generate content hash for deduplication"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str, cache_type: CacheType) -> Path:
        """Get file path for cached content"""
        type_dir = self.cache_dir / cache_type.value
        type_dir.mkdir(exist_ok=True)
        return type_dir / f"{cache_key}.cache"
    
    async def get(self, 
                  identifier: str, 
                  cache_type: CacheType,
                  profile_independent: bool = True) -> Optional[Any]:
        """Get cached content if available and not expired"""
        cache_key = self._generate_cache_key(identifier, cache_type, profile_independent)
        
        if cache_key not in self.cache_entries:
            return None
        
        entry = self.cache_entries[cache_key]
        
        # Check if expired
        if entry.is_expired():
            await self._remove_cache_entry(cache_key)
            return None
        
        # Update access information
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        self._save_cache_metadata()
        
        # Load and return content
        try:
            if entry.file_path and entry.file_path.exists():
                async with aiofiles.open(entry.file_path, 'rb') as f:
                    content = await f.read()
                    
                # Return appropriate format based on cache type
                if cache_type in [CacheType.JSON_DOWNLOAD, CacheType.API_RESPONSE, CacheType.PROCESSED_DATA]:
                    return json.loads(content.decode('utf-8'))
                elif cache_type == CacheType.XML_DOWNLOAD:
                    return content.decode('utf-8')
                else:
                    return content
            else:
                logger.warning(f"Cache file missing for key {cache_key}")
                await self._remove_cache_entry(cache_key)
                return None
                
        except Exception as e:
            logger.error(f"Failed to load cached content for key {cache_key}: {e}")
            await self._remove_cache_entry(cache_key)
            return None
    
    async def set(self, 
                  identifier: str, 
                  cache_type: CacheType,
                  content: Any,
                  ttl: Optional[timedelta] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  profile_independent: bool = True) -> str:
        """Cache content with optional TTL"""
        cache_key = self._generate_cache_key(identifier, cache_type, profile_independent)
        
        # Serialize content
        if isinstance(content, (dict, list)):
            serialized_content = json.dumps(content, indent=2).encode('utf-8')
        elif isinstance(content, str):
            serialized_content = content.encode('utf-8')
        elif isinstance(content, bytes):
            serialized_content = content
        else:
            serialized_content = str(content).encode('utf-8')
        
        # Generate content hash for deduplication
        content_hash = self._generate_content_hash(serialized_content)
        
        # Check if content already exists with same hash
        existing_entry = self._find_by_content_hash(content_hash, cache_type)
        if existing_entry:
            logger.info(f"Content already cached with hash {content_hash}, reusing")
            # Update access info for existing entry
            existing_entry.last_accessed = datetime.now()
            existing_entry.access_count += 1
            # Create alias entry pointing to same file
            self.cache_entries[cache_key] = existing_entry
            self._save_cache_metadata()
            return cache_key
        
        # Save new content
        file_path = self._get_cache_file_path(cache_key, cache_type)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(serialized_content)
            
            # Create cache entry
            now = datetime.now()
            expires_at = now + (ttl or self.default_ttl)
            
            entry = CacheEntry(
                cache_key=cache_key,
                cache_type=cache_type,
                content_hash=content_hash,
                created_at=now,
                last_accessed=now,
                expires_at=expires_at,
                file_path=file_path,
                metadata=metadata or {},
                access_count=1
            )
            
            self.cache_entries[cache_key] = entry
            self._save_cache_metadata()
            
            logger.info(f"Cached content with key {cache_key} and hash {content_hash}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to cache content: {e}")
            # Clean up partial file
            if file_path.exists():
                file_path.unlink()
            raise
    
    def _find_by_content_hash(self, content_hash: str, cache_type: CacheType) -> Optional[CacheEntry]:
        """Find existing cache entry by content hash"""
        for entry in self.cache_entries.values():
            if entry.content_hash == content_hash and entry.cache_type == cache_type:
                if not entry.is_expired():
                    return entry
        return None
    
    async def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove cache entry and associated file"""
        if cache_key not in self.cache_entries:
            return
        
        entry = self.cache_entries[cache_key]
        
        # Remove file if it exists and no other entries reference it
        if entry.file_path and entry.file_path.exists():
            # Check if any other entries reference the same file
            other_refs = [
                e for k, e in self.cache_entries.items() 
                if k != cache_key and e.file_path == entry.file_path
            ]
            if not other_refs:
                try:
                    entry.file_path.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove cache file {entry.file_path}: {e}")
        
        # Remove from entries
        del self.cache_entries[cache_key]
        self._save_cache_metadata()
    
    async def cleanup_expired(self) -> int:
        """Remove expired cache entries"""
        expired_keys = [
            key for key, entry in self.cache_entries.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            await self._remove_cache_entry(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache_entries)
        total_size = 0
        type_counts = {}
        
        for entry in self.cache_entries.values():
            cache_type = entry.cache_type.value
            type_counts[cache_type] = type_counts.get(cache_type, 0) + 1
            
            if entry.file_path and entry.file_path.exists():
                total_size += entry.file_path.stat().st_size
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'type_distribution': type_counts,
            'cache_directory': str(self.cache_dir)
        }
    
    async def clear_cache(self, cache_type: Optional[CacheType] = None) -> int:
        """Clear cache entries of specified type or all if None"""
        if cache_type:
            keys_to_remove = [
                key for key, entry in self.cache_entries.items()
                if entry.cache_type == cache_type
            ]
        else:
            keys_to_remove = list(self.cache_entries.keys())
        
        for key in keys_to_remove:
            await self._remove_cache_entry(key)
        
        logger.info(f"Cleared {len(keys_to_remove)} cache entries")
        return len(keys_to_remove)


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Convenience functions for common cache operations
async def cache_xml_download(url: str, content: str, ttl: Optional[timedelta] = None) -> str:
    """Cache XML download content"""
    cache_manager = get_cache_manager()
    return await cache_manager.set(
        identifier=url,
        cache_type=CacheType.XML_DOWNLOAD,
        content=content,
        ttl=ttl,
        metadata={'url': url, 'downloaded_at': datetime.now().isoformat()}
    )


async def get_cached_xml(url: str) -> Optional[str]:
    """Get cached XML content"""
    cache_manager = get_cache_manager()
    return await cache_manager.get(
        identifier=url,
        cache_type=CacheType.XML_DOWNLOAD
    )


async def cache_api_response(endpoint: str, params: Dict[str, Any], response: Any, ttl: Optional[timedelta] = None) -> str:
    """Cache API response"""
    cache_manager = get_cache_manager()
    identifier = f"{endpoint}|{json.dumps(params, sort_keys=True)}"
    return await cache_manager.set(
        identifier=identifier,
        cache_type=CacheType.API_RESPONSE,
        content=response,
        ttl=ttl,
        metadata={'endpoint': endpoint, 'params': params}
    )


async def get_cached_api_response(endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
    """Get cached API response"""
    cache_manager = get_cache_manager()
    identifier = f"{endpoint}|{json.dumps(params, sort_keys=True)}"
    return await cache_manager.get(
        identifier=identifier,
        cache_type=CacheType.API_RESPONSE
    )


async def cache_ai_analysis(opportunity_id: str, analysis: Dict[str, Any], ttl: Optional[timedelta] = None) -> str:
    """Cache AI analysis result"""
    cache_manager = get_cache_manager()
    return await cache_manager.set(
        identifier=opportunity_id,
        cache_type=CacheType.AI_ANALYSIS,
        content=analysis,
        ttl=ttl or timedelta(days=7),  # AI analyses last longer
        metadata={'opportunity_id': opportunity_id, 'analyzed_at': datetime.now().isoformat()}
    )


async def get_cached_ai_analysis(opportunity_id: str) -> Optional[Dict[str, Any]]:
    """Get cached AI analysis"""
    cache_manager = get_cache_manager()
    return await cache_manager.get(
        identifier=opportunity_id,
        cache_type=CacheType.AI_ANALYSIS
    )