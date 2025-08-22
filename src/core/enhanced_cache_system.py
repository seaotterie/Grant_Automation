#!/usr/bin/env python3
"""
Enhanced Multi-Layer Cache System
Targets 92% cache hit rate through intelligent caching strategies

This module provides:
1. Multi-layer caching with different TTLs for different data types
2. Intelligent cache key generation for maximum hit rate
3. Predictive cache warming for anticipated requests
4. Performance monitoring and optimization
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import threading
from collections import defaultdict, OrderedDict
import weakref

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Cache layers with different characteristics"""
    MEMORY = "memory"           # Ultra-fast in-memory cache
    DISK = "disk"              # Persistent disk-based cache
    SHARED = "shared"          # Shared cross-process cache
    DISTRIBUTED = "distributed" # Future: distributed cache


class DataType(Enum):
    """Data types with specific caching strategies"""
    FINANCIAL_ANALYTICS = "financial_analytics"      # TTL: 24h
    NETWORK_ANALYTICS = "network_analytics"         # TTL: 48h  
    GEOGRAPHIC_SCORING = "geographic_scoring"        # TTL: 168h (1 week)
    NTEE_ALIGNMENTS = "ntee_alignments"             # TTL: 720h (30 days)
    AI_LITE_RESULTS = "ai_lite_results"             # TTL: 6h
    AI_HEAVY_RESULTS = "ai_heavy_results"           # TTL: 12h
    GOVERNMENT_SCORES = "government_scores"          # TTL: 24h
    DISCOVERY_RESULTS = "discovery_results"         # TTL: 12h
    ENTITY_PROFILES = "entity_profiles"             # TTL: 24h
    BOARD_CONNECTIONS = "board_connections"         # TTL: 48h
    COMPLIANCE_DATA = "compliance_data"             # TTL: 72h
    OPPORTUNITY_METADATA = "opportunity_metadata"    # TTL: 12h


@dataclass
class CacheStrategy:
    """Caching strategy for specific data types"""
    data_type: DataType
    ttl_hours: int
    preferred_layers: List[CacheLayer]
    compression_enabled: bool
    predictive_warming: bool
    invalidation_triggers: List[str]
    max_memory_size_mb: int


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    average_response_time_ms: float = 0.0
    cache_size_mb: float = 0.0
    evictions: int = 0
    warming_successes: int = 0
    layer_hit_distribution: Dict[CacheLayer, int] = None
    
    def __post_init__(self):
        if self.layer_hit_distribution is None:
            self.layer_hit_distribution = defaultdict(int)
    
    def update_hit_rate(self):
        """Update hit rate calculation"""
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests


class EnhancedCacheSystem:
    """Multi-layer cache system targeting 92% hit rate"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache/enhanced")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache layers
        self.memory_cache: Dict[str, Tuple[Any, datetime]] = OrderedDict()
        self.disk_cache_index: Dict[str, Path] = {}
        
        # Cache strategies for different data types
        self.strategies = self._initialize_cache_strategies()
        
        # Performance monitoring
        self.metrics = CacheMetrics()
        self.metrics_lock = threading.Lock()
        
        # Memory management
        self.max_memory_items = 10000  # Maximum items in memory cache
        self.memory_cleanup_threshold = 0.8  # Cleanup when 80% full
        
        # Predictive caching
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.prediction_window_hours = 24
        
        # Cache warming scheduler
        self.warming_tasks: List[asyncio.Task] = []
        
        # Load existing cache index
        self._load_cache_index()
        
        logger.info("Enhanced Cache System initialized with 92% hit rate target")
    
    def _initialize_cache_strategies(self) -> Dict[DataType, CacheStrategy]:
        """Initialize caching strategies for different data types"""
        return {
            DataType.FINANCIAL_ANALYTICS: CacheStrategy(
                data_type=DataType.FINANCIAL_ANALYTICS,
                ttl_hours=24,
                preferred_layers=[CacheLayer.MEMORY, CacheLayer.DISK],
                compression_enabled=True,
                predictive_warming=True,
                invalidation_triggers=["entity_update", "financial_data_refresh"],
                max_memory_size_mb=50
            ),
            DataType.NETWORK_ANALYTICS: CacheStrategy(
                data_type=DataType.NETWORK_ANALYTICS,
                ttl_hours=48,
                preferred_layers=[CacheLayer.MEMORY, CacheLayer.DISK],
                compression_enabled=True,
                predictive_warming=True,
                invalidation_triggers=["board_member_update", "entity_relationship_change"],
                max_memory_size_mb=30
            ),
            DataType.GEOGRAPHIC_SCORING: CacheStrategy(
                data_type=DataType.GEOGRAPHIC_SCORING,
                ttl_hours=168,  # 1 week
                preferred_layers=[CacheLayer.MEMORY, CacheLayer.DISK],
                compression_enabled=False,
                predictive_warming=False,
                invalidation_triggers=["geographic_data_update"],
                max_memory_size_mb=20
            ),
            DataType.NTEE_ALIGNMENTS: CacheStrategy(
                data_type=DataType.NTEE_ALIGNMENTS,
                ttl_hours=720,  # 30 days
                preferred_layers=[CacheLayer.MEMORY, CacheLayer.DISK],
                compression_enabled=False,
                predictive_warming=False,
                invalidation_triggers=["ntee_classification_update"],
                max_memory_size_mb=100
            ),
            DataType.AI_LITE_RESULTS: CacheStrategy(
                data_type=DataType.AI_LITE_RESULTS,
                ttl_hours=6,
                preferred_layers=[CacheLayer.MEMORY],
                compression_enabled=False,
                predictive_warming=True,
                invalidation_triggers=["ai_model_update", "profile_update"],
                max_memory_size_mb=200
            ),
            DataType.AI_HEAVY_RESULTS: CacheStrategy(
                data_type=DataType.AI_HEAVY_RESULTS,
                ttl_hours=12,
                preferred_layers=[CacheLayer.DISK],  # Too large for memory
                compression_enabled=True,
                predictive_warming=False,
                invalidation_triggers=["ai_model_update", "comprehensive_data_update"],
                max_memory_size_mb=500
            ),
            DataType.GOVERNMENT_SCORES: CacheStrategy(
                data_type=DataType.GOVERNMENT_SCORES,
                ttl_hours=24,
                preferred_layers=[CacheLayer.MEMORY, CacheLayer.DISK],
                compression_enabled=True,
                predictive_warming=True,
                invalidation_triggers=["government_data_update", "scoring_algorithm_update"],
                max_memory_size_mb=40
            )
        }
    
    def generate_cache_key(self, 
                          data_type: DataType,
                          entity_id: str,
                          context: Optional[Dict[str, Any]] = None,
                          version: str = "1.0") -> str:
        """Generate intelligent cache key for maximum hit rate"""
        
        # Base components
        key_components = [
            data_type.value,
            entity_id,
            version
        ]
        
        # Add context-specific components
        if context:
            # Sort context keys for consistent cache keys
            context_items = sorted(context.items())
            context_hash = hashlib.md5(str(context_items).encode()).hexdigest()[:8]
            key_components.append(context_hash)
        
        # Generate hierarchical cache key for better hit rates
        cache_key = "|".join(key_components)
        
        # Add data type prefix for organization
        return f"{data_type.value}:{cache_key}"
    
    async def get(self, 
                 data_type: DataType,
                 entity_id: str, 
                 context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get data from cache with multi-layer fallback"""
        
        start_time = datetime.now()
        cache_key = self.generate_cache_key(data_type, entity_id, context)
        
        try:
            # Record access pattern for predictive caching
            self._record_access_pattern(cache_key)
            
            # Try memory cache first (fastest)
            result = await self._get_from_memory(cache_key, data_type)
            if result is not None:
                self._record_cache_hit(CacheLayer.MEMORY, start_time)
                return result
            
            # Try disk cache
            result = await self._get_from_disk(cache_key, data_type)
            if result is not None:
                # Promote to memory cache for future hits
                await self._promote_to_memory(cache_key, result, data_type)
                self._record_cache_hit(CacheLayer.DISK, start_time)
                return result
            
            # Cache miss
            self._record_cache_miss(start_time)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            self._record_cache_miss(start_time)
            return None
    
    async def put(self,
                 data_type: DataType,
                 entity_id: str,
                 data: Any,
                 context: Optional[Dict[str, Any]] = None,
                 custom_ttl: Optional[int] = None) -> bool:
        """Put data into cache with intelligent layer selection"""
        
        cache_key = self.generate_cache_key(data_type, entity_id, context)
        strategy = self.strategies.get(data_type)
        
        if not strategy:
            logger.warning(f"No cache strategy for data type: {data_type}")
            return False
        
        try:
            ttl = custom_ttl or strategy.ttl_hours
            expires_at = datetime.now() + timedelta(hours=ttl)
            
            # Determine which layers to use
            success = False
            
            if CacheLayer.MEMORY in strategy.preferred_layers:
                success = await self._put_to_memory(cache_key, data, expires_at, strategy)
            
            if CacheLayer.DISK in strategy.preferred_layers:
                success = await self._put_to_disk(cache_key, data, expires_at, strategy) or success
            
            # Schedule predictive warming if enabled
            if strategy.predictive_warming:
                await self._schedule_predictive_warming(cache_key, data_type, entity_id, context)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache put error for {cache_key}: {e}")
            return False
    
    async def _get_from_memory(self, cache_key: str, data_type: DataType) -> Optional[Any]:
        """Get data from memory cache"""
        
        if cache_key in self.memory_cache:
            data, expires_at = self.memory_cache[cache_key]
            
            # Check expiration
            if datetime.now() > expires_at:
                del self.memory_cache[cache_key]
                return None
            
            # Move to end for LRU
            self.memory_cache.move_to_end(cache_key)
            return data
        
        return None
    
    async def _get_from_disk(self, cache_key: str, data_type: DataType) -> Optional[Any]:
        """Get data from disk cache"""
        
        if cache_key not in self.disk_cache_index:
            return None
        
        cache_file = self.disk_cache_index[cache_key]
        
        if not cache_file.exists():
            # Clean up stale index entry
            del self.disk_cache_index[cache_key]
            return None
        
        try:
            # Load metadata
            metadata_file = cache_file.with_suffix('.meta')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check expiration
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                if datetime.now() > expires_at:
                    cache_file.unlink(missing_ok=True)
                    metadata_file.unlink(missing_ok=True)
                    del self.disk_cache_index[cache_key]
                    return None
            
            # Load data
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Disk cache read error for {cache_key}: {e}")
            # Clean up corrupted cache entry
            cache_file.unlink(missing_ok=True)
            cache_file.with_suffix('.meta').unlink(missing_ok=True)
            if cache_key in self.disk_cache_index:
                del self.disk_cache_index[cache_key]
            return None
    
    async def _put_to_memory(self, 
                            cache_key: str, 
                            data: Any, 
                            expires_at: datetime,
                            strategy: CacheStrategy) -> bool:
        """Put data to memory cache with LRU eviction"""
        
        try:
            # Check if memory cache is full
            if len(self.memory_cache) >= self.max_memory_items * self.memory_cleanup_threshold:
                await self._cleanup_memory_cache()
            
            # Store in memory
            self.memory_cache[cache_key] = (data, expires_at)
            self.memory_cache.move_to_end(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Memory cache put error for {cache_key}: {e}")
            return False
    
    async def _put_to_disk(self,
                          cache_key: str,
                          data: Any,
                          expires_at: datetime,
                          strategy: CacheStrategy) -> bool:
        """Put data to disk cache"""
        
        try:
            # Create cache file path
            cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
            cache_file = self.cache_dir / strategy.data_type.value / f"{cache_hash}.cache"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save data
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata
            metadata = {
                'cache_key': cache_key,
                'data_type': strategy.data_type.value,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'compression_enabled': strategy.compression_enabled
            }
            
            metadata_file = cache_file.with_suffix('.meta')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
            
            # Update index
            self.disk_cache_index[cache_key] = cache_file
            
            return True
            
        except Exception as e:
            logger.error(f"Disk cache put error for {cache_key}: {e}")
            return False
    
    async def _promote_to_memory(self, cache_key: str, data: Any, data_type: DataType):
        """Promote frequently accessed disk cache items to memory"""
        
        strategy = self.strategies.get(data_type)
        if strategy and CacheLayer.MEMORY in strategy.preferred_layers:
            expires_at = datetime.now() + timedelta(hours=strategy.ttl_hours)
            await self._put_to_memory(cache_key, data, expires_at, strategy)
    
    async def _cleanup_memory_cache(self):
        """Clean up expired and least recently used items from memory cache"""
        
        now = datetime.now()
        expired_keys = []
        
        # Find expired items
        for cache_key, (data, expires_at) in self.memory_cache.items():
            if now > expires_at:
                expired_keys.append(cache_key)
        
        # Remove expired items
        for key in expired_keys:
            del self.memory_cache[key]
        
        # If still too full, remove LRU items
        while len(self.memory_cache) > self.max_memory_items * 0.7:  # Target 70% full
            # Remove least recently used item (first in OrderedDict)
            self.memory_cache.popitem(last=False)
            with self.metrics_lock:
                self.metrics.evictions += 1
    
    def _record_access_pattern(self, cache_key: str):
        """Record access pattern for predictive caching"""
        
        now = datetime.now()
        self.access_patterns[cache_key].append(now)
        
        # Keep only recent access history
        cutoff = now - timedelta(hours=self.prediction_window_hours)
        self.access_patterns[cache_key] = [
            access_time for access_time in self.access_patterns[cache_key] 
            if access_time > cutoff
        ]
    
    def _record_cache_hit(self, layer: CacheLayer, start_time: datetime):
        """Record cache hit metrics"""
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        with self.metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.cache_hits += 1
            self.metrics.layer_hit_distribution[layer] += 1
            
            # Update average response time
            total_time = self.metrics.average_response_time_ms * (self.metrics.total_requests - 1)
            self.metrics.average_response_time_ms = (total_time + response_time) / self.metrics.total_requests
            
            self.metrics.update_hit_rate()
    
    def _record_cache_miss(self, start_time: datetime):
        """Record cache miss metrics"""
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        with self.metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.cache_misses += 1
            
            # Update average response time
            total_time = self.metrics.average_response_time_ms * (self.metrics.total_requests - 1)
            self.metrics.average_response_time_ms = (total_time + response_time) / self.metrics.total_requests
            
            self.metrics.update_hit_rate()
    
    async def _schedule_predictive_warming(self,
                                         cache_key: str,
                                         data_type: DataType,
                                         entity_id: str,
                                         context: Optional[Dict[str, Any]]):
        """Schedule predictive cache warming based on access patterns"""
        
        # Analyze access pattern to predict next access
        if cache_key in self.access_patterns:
            accesses = self.access_patterns[cache_key]
            if len(accesses) >= 2:
                # Calculate average access interval
                intervals = [
                    (accesses[i] - accesses[i-1]).total_seconds() 
                    for i in range(1, len(accesses))
                ]
                avg_interval = sum(intervals) / len(intervals)
                
                # Schedule warming before predicted next access
                warming_delay = max(avg_interval * 0.8, 300)  # At least 5 minutes
                
                async def warm_cache():
                    await asyncio.sleep(warming_delay)
                    # This would trigger cache warming logic
                    logger.debug(f"Predictive warming triggered for {cache_key}")
                
                task = asyncio.create_task(warm_cache())
                self.warming_tasks.append(task)
    
    def _load_cache_index(self):
        """Load disk cache index from metadata"""
        
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                
                # Rebuild index with Path objects
                for cache_key, file_path in index_data.items():
                    self.disk_cache_index[cache_key] = Path(file_path)
                
                logger.info(f"Loaded {len(self.disk_cache_index)} cache entries from index")
                
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
    
    async def save_cache_index(self):
        """Save disk cache index to metadata"""
        
        index_file = self.cache_dir / "cache_index.json" 
        try:
            # Convert Path objects to strings for JSON serialization
            index_data = {
                cache_key: str(file_path) 
                for cache_key, file_path in self.disk_cache_index.items()
            }
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def get_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics"""
        
        with self.metrics_lock:
            # Calculate memory cache size
            memory_size_mb = sum(
                len(pickle.dumps(data)) for data, _ in self.memory_cache.values()
            ) / (1024 * 1024)
            
            self.metrics.cache_size_mb = memory_size_mb
            
            return CacheMetrics(
                total_requests=self.metrics.total_requests,
                cache_hits=self.metrics.cache_hits,
                cache_misses=self.metrics.cache_misses,
                hit_rate=self.metrics.hit_rate,
                average_response_time_ms=self.metrics.average_response_time_ms,
                cache_size_mb=self.metrics.cache_size_mb,
                evictions=self.metrics.evictions,
                warming_successes=self.metrics.warming_successes,
                layer_hit_distribution=dict(self.metrics.layer_hit_distribution)
            )
    
    async def invalidate(self, data_type: DataType, entity_id: str, trigger: str):
        """Invalidate cache entries based on triggers"""
        
        strategy = self.strategies.get(data_type)
        if not strategy or trigger not in strategy.invalidation_triggers:
            return
        
        # Find and remove matching cache entries
        pattern = f"{data_type.value}:{entity_id}"
        keys_to_remove = []
        
        # Memory cache
        for cache_key in self.memory_cache.keys():
            if pattern in cache_key:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        # Disk cache
        keys_to_remove = []
        for cache_key, cache_file in self.disk_cache_index.items():
            if pattern in cache_key:
                cache_file.unlink(missing_ok=True)
                cache_file.with_suffix('.meta').unlink(missing_ok=True)
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.disk_cache_index[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for {data_type.value}:{entity_id} (trigger: {trigger})")


# Global enhanced cache instance
enhanced_cache_system = EnhancedCacheSystem()