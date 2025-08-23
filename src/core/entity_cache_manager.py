# Entity Cache Manager Implementation
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from enum import Enum

class EntityType(Enum):
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    FOUNDATION = "foundation"

class DataSourceType:
    PROPUBLICA = "propublica"
    GRANTS_GOV = "grants_gov"
    USASPENDING = "usaspending"

class EntityCacheManager:
    """Entity-based caching system for performance optimization"""
    
    def __init__(self):
        self._cache = {}
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_entities": 0,
            "last_updated": datetime.now()
        }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["cache_hits"] + self._stats["cache_misses"]
        hit_rate = (self._stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "status": "operational",
            "total_entities": len(self._cache),
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "hit_rate_percentage": round(hit_rate, 2),
            "last_updated": self._stats["last_updated"].isoformat(),
            "cache_size_mb": len(str(self._cache)) / (1024 * 1024)
        }
    
    def get_entity_data(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity data from cache"""
        if entity_id in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[entity_id]
        else:
            self._stats["cache_misses"] += 1
            return None
    
    def store_entity_data(self, entity_id: str, data: Dict[str, Any], ttl: int = 86400) -> bool:
        """Store entity data in cache"""
        try:
            self._cache[entity_id] = {
                **data,
                "cached_at": datetime.now().isoformat(),
                "ttl": ttl
            }
            self._stats["total_entities"] = len(self._cache)
            self._stats["last_updated"] = datetime.now()
            return True
        except Exception:
            return False
    
    def clear_cache(self) -> bool:
        """Clear the cache"""
        try:
            self._cache.clear()
            self._stats["total_entities"] = 0
            self._stats["last_updated"] = datetime.now()
            return True
        except Exception:
            return False
    
    async def list_entities(self, entity_type: EntityType) -> List[str]:
        """List entities of a specific type"""
        # For testing purposes, return sample data based on type
        if entity_type == EntityType.NONPROFIT:
            return ["12-3456789", "12-7654321", "12-1111111"]  # Sample EINs
        elif entity_type == EntityType.GOVERNMENT:
            return ["EPA-001", "NSF-002", "DOE-003"]  # Sample opportunity IDs
        elif entity_type == EntityType.FOUNDATION:
            return ["FDN-001", "FDN-002"]  # Sample foundation IDs
        else:
            return []

# Global cache manager instance
_cache_manager = None

def get_entity_cache_manager() -> EntityCacheManager:
    """Get the global entity cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = EntityCacheManager()
    return _cache_manager