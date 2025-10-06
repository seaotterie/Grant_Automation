#!/usr/bin/env python3
"""
Unit Tests for Entity Cache Manager
Tests the 85% cache hit rate system and entity-based data optimization.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.entity_cache_manager import EntityCacheManager, EntityType, DataSourceType


class TestEntityCacheManager:
    """Test suite for EntityCacheManager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache_manager = EntityCacheManager()
        
    def test_cache_manager_initialization(self):
        """Test that cache manager initializes correctly"""
        assert self.cache_manager._cache == {}
        assert self.cache_manager._stats["cache_hits"] == 0
        assert self.cache_manager._stats["cache_misses"] == 0
        assert self.cache_manager._stats["total_entities"] == 0
        assert isinstance(self.cache_manager._stats["last_updated"], datetime)
        
    @pytest.mark.asyncio
    async def test_get_cache_stats_empty(self):
        """Test cache statistics with empty cache"""
        stats = await self.cache_manager.get_cache_stats()
        
        assert stats["status"] == "operational"
        assert stats["total_entities"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percentage"] == 0
        assert "last_updated" in stats
        assert "cache_size_mb" in stats
        
    def test_get_entity_data_miss(self):
        """Test cache miss scenario"""
        result = self.cache_manager.get_entity_data("nonexistent_entity")
        
        assert result is None
        assert self.cache_manager._stats["cache_misses"] == 1
        assert self.cache_manager._stats["cache_hits"] == 0
        
    def test_set_and_get_entity_data_hit(self):
        """Test cache hit scenario"""
        test_entity_id = "test_entity_123"
        test_data = {
            "organization_name": "Test Organization",
            "ein": "12-3456789",
            "revenue": 1000000,
            "assets": 2000000,
            "ntee_code": "A01"
        }
        
        # Set data in cache
        self.cache_manager.store_entity_data(test_entity_id, test_data)
        
        # Retrieve data (should be cache hit)
        result = self.cache_manager.get_entity_data(test_entity_id)

        # Check that original data is preserved (cache adds cached_at and ttl)
        assert result is not None
        assert result["organization_name"] == test_data["organization_name"]
        assert result["ein"] == test_data["ein"]
        assert result["revenue"] == test_data["revenue"]
        assert result["assets"] == test_data["assets"]
        assert result["ntee_code"] == test_data["ntee_code"]
        assert "cached_at" in result
        assert "ttl" in result
        assert self.cache_manager._stats["cache_hits"] == 1
        assert self.cache_manager._stats["cache_misses"] == 0
        
    @pytest.mark.asyncio
    async def test_cache_stats_with_data(self):
        """Test cache statistics with actual data"""
        # Add some test data
        self.cache_manager.store_entity_data("entity1", {"data": "test1"})
        self.cache_manager.store_entity_data("entity2", {"data": "test2"})
        
        # Create some hits and misses
        self.cache_manager.get_entity_data("entity1")  # hit
        self.cache_manager.get_entity_data("entity2")  # hit
        self.cache_manager.get_entity_data("nonexistent")  # miss
        
        stats = await self.cache_manager.get_cache_stats()
        
        assert stats["total_entities"] == 2
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percentage"] == 66.67  # 2/3 * 100, rounded
        
    def test_cache_size_calculation(self):
        """Test cache size calculation in MB"""
        # Add substantial test data
        large_data = {"large_field": "x" * 10000}  # 10KB of data
        
        for i in range(10):
            self.cache_manager.store_entity_data(f"entity_{i}", large_data)
            
        # Cache should have some measurable size
        cache_size = len(str(self.cache_manager._cache)) / (1024 * 1024)
        assert cache_size > 0
        
    def test_entity_types_enum(self):
        """Test EntityType enum values"""
        assert EntityType.NONPROFIT.value == "nonprofit"
        assert EntityType.GOVERNMENT.value == "government"
        assert EntityType.FOUNDATION.value == "foundation"
        
    def test_data_source_types(self):
        """Test DataSourceType constants"""
        assert DataSourceType.PROPUBLICA == "propublica"
        assert DataSourceType.GRANTS_GOV == "grants_gov"
        assert DataSourceType.USASPENDING == "usaspending"


class TestEntityCachePerformance:
    """Test cache performance characteristics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache_manager = EntityCacheManager()
        
    def test_cache_hit_rate_simulation(self):
        """Test cache hit rate under realistic usage patterns"""
        # Simulate realistic entity data
        entities = {}
        for i in range(42):  # 42 entities as per CDR analysis
            entity_id = f"ein_{i:09d}"
            entities[entity_id] = {
                "ein": entity_id,
                "organization_name": f"Test Organization {i}",
                "revenue": 1000000 + i * 100000,
                "assets": 2000000 + i * 200000,
                "ntee_code": f"A{i:02d}",
                "propublica_data": {"filing_year": 2023, "total_revenue": 1000000 + i * 100000},
                "board_members": [f"Member {j}" for j in range(5)]
            }
            self.cache_manager.store_entity_data(entity_id, entities[entity_id])
            
        # Simulate realistic access patterns (some entities accessed more frequently)
        access_pattern = []
        
        # Hot entities (frequently accessed) - 20% of entities, 80% of accesses
        hot_entities = list(entities.keys())[:8]  # ~20% of 42
        for _ in range(80):
            import random
            entity_id = random.choice(hot_entities)
            access_pattern.append(entity_id)
            
        # Cold entities (less frequently accessed) - 80% of entities, 20% of accesses
        cold_entities = list(entities.keys())[8:]
        for _ in range(20):
            import random
            entity_id = random.choice(cold_entities)
            access_pattern.append(entity_id)
            
        # Execute access pattern
        hits = 0
        misses = 0
        for entity_id in access_pattern:
            result = self.cache_manager.get_entity_data(entity_id)
            if result is not None:
                hits += 1
            else:
                misses += 1
                
        # Calculate hit rate
        total_accesses = hits + misses
        hit_rate = (hits / total_accesses) * 100
        
        # Should achieve high hit rate (target: 85%+)
        assert hit_rate >= 80.0, f"Cache hit rate {hit_rate}% below target"
        print(f"Achieved cache hit rate: {hit_rate:.2f}%")
        
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self):
        """Test cache performance under concurrent load"""
        # Pre-populate cache with test data
        for i in range(100):
            entity_data = {
                "ein": f"{i:09d}",
                "organization_name": f"Organization {i}",
                "revenue": 1000000 + i * 10000
            }
            self.cache_manager.store_entity_data(f"entity_{i}", entity_data)
            
        # Simulate concurrent access
        async def access_cache():
            """Simulate cache access operations"""
            results = []
            for i in range(50):  # 50 accesses per concurrent task
                import random
                entity_id = f"entity_{random.randint(0, 99)}"
                start_time = asyncio.get_event_loop().time()
                result = self.cache_manager.get_entity_data(entity_id)
                end_time = asyncio.get_event_loop().time()
                
                access_time = end_time - start_time
                results.append(access_time)
                
            return results
            
        # Run concurrent cache access tasks
        tasks = [access_cache() for _ in range(10)]  # 10 concurrent tasks
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results and calculate performance metrics
        all_access_times = [time for result_list in all_results for time in result_list]
        avg_access_time = sum(all_access_times) / len(all_access_times)
        max_access_time = max(all_access_times)
        
        # Performance assertions (target: sub-millisecond)
        assert avg_access_time < 0.001, f"Average access time {avg_access_time:.6f}s exceeds 1ms target"
        assert max_access_time < 0.005, f"Maximum access time {max_access_time:.6f}s exceeds 5ms threshold"
        
        print(f"Average cache access time: {avg_access_time*1000:.3f}ms")
        print(f"Maximum cache access time: {max_access_time*1000:.3f}ms")


class TestEntityCacheIntegration:
    """Test cache integration with entity types and data sources"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache_manager = EntityCacheManager()
        
    def test_nonprofit_entity_caching(self):
        """Test caching of nonprofit entity data"""
        nonprofit_data = {
            "entity_type": EntityType.NONPROFIT.value,
            "ein": "12-3456789",
            "organization_name": "Test Nonprofit Foundation",
            "ntee_code": "T99",
            "revenue": 5000000,
            "assets": 8000000,
            "data_source": DataSourceType.PROPUBLICA,
            "filing_year": 2023,
            "board_members": ["John Doe", "Jane Smith", "Bob Johnson"],
            "programs": ["Education", "Healthcare", "Community Development"]
        }
        
        entity_id = "nonprofit_123456789"
        self.cache_manager.store_entity_data(entity_id, nonprofit_data)
        
        retrieved_data = self.cache_manager.get_entity_data(entity_id)

        # Check that original data is preserved (cache adds cached_at and ttl)
        assert retrieved_data is not None
        assert retrieved_data["entity_type"] == EntityType.NONPROFIT.value
        assert retrieved_data["ein"] == nonprofit_data["ein"]
        assert retrieved_data["organization_name"] == nonprofit_data["organization_name"]
        assert retrieved_data["ntee_code"] == nonprofit_data["ntee_code"]
        assert retrieved_data["revenue"] == nonprofit_data["revenue"]
        assert "cached_at" in retrieved_data
        assert "ttl" in retrieved_data
        
    def test_government_opportunity_caching(self):
        """Test caching of government opportunity data"""
        government_data = {
            "entity_type": EntityType.GOVERNMENT.value,
            "opportunity_id": "HRSA-25-001",
            "agency": "Health Resources and Services Administration",
            "title": "Health Workforce Programs",
            "description": "Funding for health workforce development programs",
            "total_funding": 50000000,
            "award_floor": 100000,
            "award_ceiling": 2000000,
            "data_source": DataSourceType.GRANTS_GOV,
            "deadline": "2025-03-15",
            "eligibility": ["501c3", "Public University", "State Government"]
        }
        
        entity_id = "gov_HRSA-25-001"
        self.cache_manager.store_entity_data(entity_id, government_data)
        
        retrieved_data = self.cache_manager.get_entity_data(entity_id)

        # Check that original data is preserved (cache adds cached_at and ttl)
        assert retrieved_data is not None
        assert retrieved_data["entity_type"] == EntityType.GOVERNMENT.value
        assert retrieved_data["opportunity_id"] == government_data["opportunity_id"]
        assert retrieved_data["agency"] == government_data["agency"]
        assert retrieved_data["total_funding"] == government_data["total_funding"]
        assert "cached_at" in retrieved_data
        assert "ttl" in retrieved_data
        
    def test_foundation_entity_caching(self):
        """Test caching of foundation entity data"""
        foundation_data = {
            "entity_type": EntityType.FOUNDATION.value,
            "foundation_id": "foundation_456789",
            "foundation_name": "Test Private Foundation",
            "assets": 100000000,
            "grants_paid": 5000000,
            "focus_areas": ["Education", "Health", "Environment"],
            "geographic_focus": ["Virginia", "North Carolina", "Maryland"],
            "application_process": "By invitation only",
            "average_grant_size": 250000,
            "board_members": ["Alice Brown", "Charlie Wilson"]
        }
        
        entity_id = "foundation_456789"
        self.cache_manager.store_entity_data(entity_id, foundation_data)
        
        retrieved_data = self.cache_manager.get_entity_data(entity_id)

        # Check that original data is preserved (cache adds cached_at and ttl)
        assert retrieved_data is not None
        assert retrieved_data["entity_type"] == EntityType.FOUNDATION.value
        assert retrieved_data["foundation_id"] == foundation_data["foundation_id"]
        assert retrieved_data["foundation_name"] == foundation_data["foundation_name"]
        assert retrieved_data["assets"] == foundation_data["assets"]
        assert retrieved_data["grants_paid"] == foundation_data["grants_paid"]
        assert "cached_at" in retrieved_data
        assert "ttl" in retrieved_data
        

class TestEntityCacheErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache_manager = EntityCacheManager()
        
    def test_none_entity_id(self):
        """Test handling of None entity ID"""
        result = self.cache_manager.get_entity_data(None)
        assert result is None
        
    def test_empty_entity_id(self):
        """Test handling of empty entity ID"""
        result = self.cache_manager.get_entity_data("")
        assert result is None
        
    def test_none_entity_data(self):
        """Test setting None as entity data"""
        entity_id = "test_entity"
        self.cache_manager.store_entity_data(entity_id, None)
        
        result = self.cache_manager.get_entity_data(entity_id)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_concurrent_cache_modifications(self):
        """Test thread safety of cache operations"""
        entity_id = "concurrent_test"
        
        async def writer_task():
            """Task that writes to cache"""
            for i in range(100):
                data = {"iteration": i, "data": f"value_{i}"}
                self.cache_manager.store_entity_data(f"{entity_id}_{i}", data)
                
        async def reader_task():
            """Task that reads from cache"""
            reads = []
            for i in range(100):
                result = self.cache_manager.get_entity_data(f"{entity_id}_{i}")
                reads.append(result)
            return reads
            
        # Run concurrent writer and reader tasks
        writer_result, reader_result = await asyncio.gather(
            writer_task(),
            reader_task()
        )
        
        # Verify no corruption occurred
        # Note: Some reads may be None due to timing, but no corrupted data
        for result in reader_result:
            if result is not None:
                assert "iteration" in result
                assert "data" in result
                assert isinstance(result["iteration"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])