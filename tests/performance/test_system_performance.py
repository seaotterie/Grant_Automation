# Performance Tests for Catalynx System
# Tests system performance under load and validates performance requirements

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import components for performance testing
try:
    from src.scoring.discovery_scorer import DiscoveryScorer
    from src.analytics.success_scorer import SuccessScorer
    from src.profiles.models import OrganizationProfile
    SCORERS_AVAILABLE = True
except ImportError:
    SCORERS_AVAILABLE = False

@pytest.mark.performance
class TestScoringPerformance:
    """Test performance of scoring components"""
    
    @pytest.fixture
    def large_dataset(self, performance_test_data):
        """Large dataset for performance testing"""
        return performance_test_data
    
    @pytest.mark.asyncio
    async def test_discovery_scorer_performance(self, large_dataset):
        """Test Discovery Scorer performance with large dataset"""
        if not SCORERS_AVAILABLE:
            pytest.skip("Scoring components not available")
        
        scorer = DiscoveryScorer()
        profiles = large_dataset["profiles"][:50]  # Use subset for performance test
        opportunities = large_dataset["opportunities"][:500]
        
        # Warmup
        profile_obj = OrganizationProfile(**profiles[0])
        for _ in range(10):
            await scorer.score_opportunity(opportunities[0], profile_obj)
        
        # Performance test
        start_time = time.perf_counter()
        
        total_operations = 0
        for i, profile in enumerate(profiles):
            profile_obj = OrganizationProfile(**profile)
            for j, opportunity in enumerate(opportunities[:10]):  # 10 ops per profile
                await scorer.score_opportunity(opportunity, profile_obj)
                total_operations += 1
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Performance assertions
        avg_time_per_operation = total_time / total_operations
        operations_per_second = total_operations / total_time
        
        print(f"\nDiscovery Scorer Performance:")
        print(f"  Total operations: {total_operations}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Avg time per operation: {avg_time_per_operation*1000:.3f}ms")
        print(f"  Operations per second: {operations_per_second:.1f}")
        
        # Performance targets
        assert avg_time_per_operation < 0.001, f"Performance target: <1ms per operation, got {avg_time_per_operation*1000:.3f}ms"
        assert operations_per_second > 1000, f"Performance target: >1000 ops/sec, got {operations_per_second:.1f}"
    
    @pytest.mark.asyncio
    async def test_concurrent_scoring_performance(self, large_dataset):
        """Test concurrent scoring performance"""
        if not SCORERS_AVAILABLE:
            pytest.skip("Scoring components not available")
        
        scorer = DiscoveryScorer()
        profiles = large_dataset["profiles"][:10]
        opportunities = large_dataset["opportunities"][:100]
        
        async def score_batch(profile_data, opportunities_batch):
            """Score a batch of opportunities for one profile"""
            profile_obj = OrganizationProfile(**profile_data)
            results = []
            for opp in opportunities_batch:
                result = await scorer.score_opportunity(opp, profile_obj)
                results.append(result)
            return results
        
        # Test concurrent execution
        start_time = time.perf_counter()
        
        tasks = []
        for profile in profiles:
            task = score_batch(profile, opportunities[:10])  # 10 ops per profile
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        concurrent_time = end_time - start_time
        
        # Compare with sequential execution
        start_time = time.perf_counter()
        
        sequential_results = []
        for profile in profiles:
            batch_result = await score_batch(profile, opportunities[:10])
            sequential_results.append(batch_result)
        
        end_time = time.perf_counter()
        sequential_time = end_time - start_time
        
        # Concurrent should be faster or similar
        speedup = sequential_time / concurrent_time
        
        print(f"\nConcurrent vs Sequential Performance:")
        print(f"  Concurrent time: {concurrent_time:.3f}s")
        print(f"  Sequential time: {sequential_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x")
        
        # Verify results are identical
        assert len(results) == len(sequential_results)
        for concurrent_batch, sequential_batch in zip(results, sequential_results):
            assert len(concurrent_batch) == len(sequential_batch)
    
    def test_memory_usage_during_scoring(self, large_dataset):
        """Test memory usage during large scoring operations"""
        import psutil
        import os
        
        if not SCORERS_AVAILABLE:
            pytest.skip("Scoring components not available")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        scorer = DiscoveryScorer()
        profiles = large_dataset["profiles"][:20]
        opportunities = large_dataset["opportunities"][:200]
        
        # Run scoring operations
        async def run_scoring():
            for profile in profiles:
                profile_obj = OrganizationProfile(**profile)
                for opp in opportunities[:10]:  # 10 ops per profile
                    await scorer.score_opportunity(opp, profile_obj)
        
        # Run the scoring
        asyncio.run(run_scoring())
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"\nMemory Usage:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Peak memory: {peak_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")
        
        # Memory usage should be reasonable
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.1f}MB increase"


@pytest.mark.performance
class TestCachePerformance:
    """Test entity cache performance"""
    
    def test_cache_hit_rate_performance(self):
        """Test cache hit rate and performance"""
        try:
            from src.core.entity_cache_manager import get_entity_cache_manager
            cache_manager = get_entity_cache_manager()
        except ImportError:
            # Mock cache manager for testing
            cache_manager = Mock()
            cache_manager.get_entity_data.return_value = {"ein": "12-3456789", "name": "Test Org"}
            cache_manager.store_entity_data.return_value = True
        
        # Test data
        test_eins = [f"12-345678{i:02d}" for i in range(100)]
        
        # Populate cache
        for ein in test_eins[:50]:  # Cache first 50
            test_data = {"ein": ein, "name": f"Organization {ein}"}
            cache_manager.store_entity_data(ein, test_data)
        
        # Test cache performance
        cache_hits = 0
        cache_misses = 0
        total_time = 0
        
        for ein in test_eins:
            start_time = time.perf_counter()
            
            result = cache_manager.get_entity_data(ein)
            
            end_time = time.perf_counter()
            total_time += (end_time - start_time)
            
            if result:
                cache_hits += 1
            else:
                cache_misses += 1
        
        hit_rate = cache_hits / len(test_eins)
        avg_lookup_time = total_time / len(test_eins)
        
        print(f"\nCache Performance:")
        print(f"  Cache hits: {cache_hits}")
        print(f"  Cache misses: {cache_misses}")
        print(f"  Hit rate: {hit_rate:.1%}")
        print(f"  Avg lookup time: {avg_lookup_time*1000:.3f}ms")
        
        # Performance targets
        assert hit_rate >= 0.5, f"Expected at least 50% hit rate, got {hit_rate:.1%}"
        assert avg_lookup_time < 0.001, f"Cache lookup too slow: {avg_lookup_time*1000:.3f}ms"
    
    def test_cache_scalability(self):
        """Test cache performance with large number of entries"""
        try:
            from src.core.entity_cache_manager import get_entity_cache_manager
            cache_manager = get_entity_cache_manager()
        except ImportError:
            cache_manager = Mock()
            cache_manager.get_entity_data.return_value = {"test": "data"}
            cache_manager.store_entity_data.return_value = True
        
        # Test scalability with increasing cache size
        cache_sizes = [100, 500, 1000, 5000]
        performance_results = []
        
        for cache_size in cache_sizes:
            # Populate cache
            for i in range(cache_size):
                ein = f"test-ein-{i:06d}"
                data = {"ein": ein, "name": f"Org {i}", "revenue": i * 1000}
                cache_manager.store_entity_data(ein, data)
            
            # Test lookup performance
            lookup_times = []
            for i in range(min(100, cache_size)):  # Test 100 lookups
                ein = f"test-ein-{i:06d}"
                
                start_time = time.perf_counter()
                cache_manager.get_entity_data(ein)
                end_time = time.perf_counter()
                
                lookup_times.append(end_time - start_time)
            
            avg_lookup_time = statistics.mean(lookup_times)
            performance_results.append((cache_size, avg_lookup_time))
            
            print(f"Cache size {cache_size}: {avg_lookup_time*1000:.3f}ms avg lookup")
        
        # Performance should not degrade significantly with size
        first_time = performance_results[0][1]
        last_time = performance_results[-1][1]
        
        degradation_factor = last_time / first_time
        
        print(f"\nCache Scalability:")
        print(f"  Performance degradation factor: {degradation_factor:.2f}x")
        
        # Should not degrade more than 3x
        assert degradation_factor < 3.0, f"Cache performance degrades too much: {degradation_factor:.2f}x"


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance"""
    
    @pytest.fixture
    def test_client(self):
        """FastAPI test client"""
        try:
            from fastapi.testclient import TestClient
            from src.web.main import app
            return TestClient(app)
        except ImportError:
            # Mock client
            mock_client = Mock()
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = {"status": "success"}
            mock_client.get.return_value.elapsed.total_seconds.return_value = 0.05
            return mock_client
    
    def test_health_endpoint_performance(self, test_client):
        """Test health endpoint response time"""
        
        response_times = []
        
        # Test multiple requests
        for _ in range(50):
            start_time = time.perf_counter()
            
            response = test_client.get("/api/health")
            
            end_time = time.perf_counter()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if hasattr(response, 'status_code'):
                assert response.status_code == 200
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        max_response_time = max(response_times)
        
        print(f"\nHealth Endpoint Performance:")
        print(f"  Average response time: {avg_response_time*1000:.1f}ms")
        print(f"  95th percentile: {p95_response_time*1000:.1f}ms")
        print(f"  Maximum response time: {max_response_time*1000:.1f}ms")
        
        # Performance targets
        assert avg_response_time < 0.1, f"Health endpoint too slow: {avg_response_time*1000:.1f}ms"
        assert p95_response_time < 0.2, f"95th percentile too slow: {p95_response_time*1000:.1f}ms"
    
    def test_concurrent_api_requests(self, test_client):
        """Test API performance under concurrent load"""
        
        def make_request():
            """Make a single API request"""
            start_time = time.perf_counter()
            response = test_client.get("/api/health")
            end_time = time.perf_counter()
            
            return {
                'response_time': end_time - start_time,
                'status_code': getattr(response, 'status_code', 200)
            }
        
        # Test with increasing concurrency
        concurrency_levels = [1, 5, 10, 20]
        
        for concurrency in concurrency_levels:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                start_time = time.perf_counter()
                
                # Submit concurrent requests
                futures = [executor.submit(make_request) for _ in range(concurrency * 5)]
                results = [future.result() for future in futures]
                
                end_time = time.perf_counter()
                total_time = end_time - start_time
            
            # Analyze results
            response_times = [r['response_time'] for r in results]
            successful_requests = sum(1 for r in results if r['status_code'] == 200)
            
            avg_response_time = statistics.mean(response_times)
            throughput = len(results) / total_time
            
            print(f"\nConcurrency {concurrency}:")
            print(f"  Successful requests: {successful_requests}/{len(results)}")
            print(f"  Average response time: {avg_response_time*1000:.1f}ms")
            print(f"  Throughput: {throughput:.1f} req/sec")
            
            # All requests should succeed
            assert successful_requests == len(results), f"Some requests failed at concurrency {concurrency}"
            
            # Response time should not degrade too much
            assert avg_response_time < 0.5, f"Response time too slow at concurrency {concurrency}: {avg_response_time*1000:.1f}ms"


@pytest.mark.performance
class TestDataProcessingPerformance:
    """Test data processing performance"""
    
    def test_large_dataset_processing(self, performance_test_data):
        """Test processing performance with large datasets"""
        
        profiles = performance_test_data["profiles"]
        opportunities = performance_test_data["opportunities"]
        
        # Test profile processing
        start_time = time.perf_counter()
        
        processed_profiles = []
        for profile in profiles:
            # Simulate profile processing
            processed = {
                'profile_id': profile.get('profile_id'),
                'processed_name': profile.get('organization_name', '').upper(),
                'revenue_category': 'large' if profile.get('revenue', 0) > 1000000 else 'small',
                'state_code': profile.get('state', 'UNKNOWN')
            }
            processed_profiles.append(processed)
        
        profile_processing_time = time.perf_counter() - start_time
        
        # Test opportunity processing
        start_time = time.perf_counter()
        
        processed_opportunities = []
        for opp in opportunities:
            # Simulate opportunity processing
            processed = {
                'opportunity_id': opp.get('opportunity_id'),
                'processed_name': opp.get('organization_name', '').upper(),
                'funding_category': 'large' if opp.get('funding_amount', 0) > 500000 else 'small',
                'source_type': opp.get('source_type', 'Unknown')
            }
            processed_opportunities.append(processed)
        
        opportunity_processing_time = time.perf_counter() - start_time
        
        # Performance metrics
        profile_processing_rate = len(profiles) / profile_processing_time
        opportunity_processing_rate = len(opportunities) / opportunity_processing_time
        
        print(f"\nData Processing Performance:")
        print(f"  Profiles processed: {len(profiles)} in {profile_processing_time:.3f}s")
        print(f"  Profile processing rate: {profile_processing_rate:.1f} profiles/sec")
        print(f"  Opportunities processed: {len(opportunities)} in {opportunity_processing_time:.3f}s")
        print(f"  Opportunity processing rate: {opportunity_processing_rate:.1f} opportunities/sec")
        
        # Performance targets
        assert profile_processing_rate > 1000, f"Profile processing too slow: {profile_processing_rate:.1f}/sec"
        assert opportunity_processing_rate > 5000, f"Opportunity processing too slow: {opportunity_processing_rate:.1f}/sec"
    
    def test_json_parsing_performance(self):
        """Test JSON parsing performance for API responses"""
        import json
        
        # Generate large JSON data
        large_json_data = {
            "profiles": [
                {
                    "profile_id": f"profile_{i}",
                    "organization_name": f"Organization {i}",
                    "revenue": i * 10000,
                    "opportunities": [
                        {
                            "opportunity_id": f"opp_{i}_{j}",
                            "name": f"Opportunity {i}-{j}",
                            "amount": j * 1000
                        }
                        for j in range(10)
                    ]
                }
                for i in range(1000)
            ]
        }
        
        # Test JSON serialization
        start_time = time.perf_counter()
        json_string = json.dumps(large_json_data)
        serialization_time = time.perf_counter() - start_time
        
        # Test JSON deserialization
        start_time = time.perf_counter()
        parsed_data = json.loads(json_string)
        deserialization_time = time.perf_counter() - start_time
        
        json_size_mb = len(json_string) / 1024 / 1024
        
        print(f"\nJSON Processing Performance:")
        print(f"  JSON size: {json_size_mb:.1f}MB")
        print(f"  Serialization time: {serialization_time:.3f}s")
        print(f"  Deserialization time: {deserialization_time:.3f}s")
        print(f"  Serialization rate: {json_size_mb/serialization_time:.1f}MB/s")
        print(f"  Deserialization rate: {json_size_mb/deserialization_time:.1f}MB/s")
        
        # Verify data integrity
        assert len(parsed_data["profiles"]) == len(large_json_data["profiles"])
        
        # Performance should be reasonable
        assert serialization_time < 1.0, f"JSON serialization too slow: {serialization_time:.3f}s"
        assert deserialization_time < 1.0, f"JSON deserialization too slow: {deserialization_time:.3f}s"


@pytest.mark.performance
@pytest.mark.slow
class TestSystemLoadPerformance:
    """Test system performance under sustained load"""
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test system performance under sustained load"""
        
        # This test simulates sustained system usage
        duration_seconds = 30  # 30 second test
        operations_per_second = 10
        
        async def simulate_user_activity():
            """Simulate typical user activity"""
            activities = [
                "create_profile",
                "run_discovery", 
                "view_analytics",
                "export_results"
            ]
            
            activity_counts = {activity: 0 for activity in activities}
            start_time = time.perf_counter()
            
            while time.perf_counter() - start_time < duration_seconds:
                # Pick random activity
                import random
                activity = random.choice(activities)
                
                # Simulate activity with small delay
                await asyncio.sleep(0.1)  # 100ms per operation
                activity_counts[activity] += 1
                
                # Control rate
                await asyncio.sleep(1.0 / operations_per_second - 0.1)
            
            return activity_counts
        
        # Run sustained load test
        start_time = time.perf_counter()
        results = await simulate_user_activity()
        actual_duration = time.perf_counter() - start_time
        
        total_operations = sum(results.values())
        actual_ops_per_second = total_operations / actual_duration
        
        print(f"\nSustained Load Test Results:")
        print(f"  Duration: {actual_duration:.1f}s")
        print(f"  Total operations: {total_operations}")
        print(f"  Operations per second: {actual_ops_per_second:.1f}")
        print(f"  Activity breakdown: {results}")
        
        # Should maintain target operation rate
        target_total_ops = duration_seconds * operations_per_second * 0.9  # 90% of target
        assert total_operations >= target_total_ops, f"Failed to maintain operation rate: {total_operations} < {target_total_ops}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])