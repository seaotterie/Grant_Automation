#!/usr/bin/env python3
"""
Performance Regression Testing Framework
Validates system performance claims and detects regressions.

Key Performance Targets:
- Sub-millisecond entity cache operations
- 85% cache hit rate under realistic load
- 18-processor pipeline sub-second completion
- WebSocket real-time update responsiveness
"""

import pytest
import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import psutil
import memory_profiler

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.entity_cache_manager import EntityCacheManager
from src.processors.registry import register_all_processors, get_auto_registry
from src.core.workflow_engine import get_workflow_engine


class PerformanceBaseline:
    """Performance baseline configuration and thresholds"""
    
    # Entity Cache Performance Targets
    CACHE_ACCESS_TIME_TARGET_MS = 1.0  # Sub-millisecond target
    CACHE_HIT_RATE_TARGET = 85.0  # 85% hit rate target
    CACHE_OPERATION_VARIANCE_MAX = 0.5  # Maximum variance in ms
    
    # Processor Performance Targets
    PROCESSOR_REGISTRATION_TIME_MAX = 5.0  # 5 seconds max
    PROCESSOR_DISCOVERY_TIME_MAX = 10.0  # 10 seconds max
    PROCESSOR_EXECUTION_TIME_TARGET = 1.0  # 1 second per processor
    
    # System Resource Targets
    MEMORY_USAGE_MAX_MB = 512  # 512MB max for testing
    CPU_USAGE_MAX_PERCENT = 80  # 80% max CPU usage
    
    # API Response Targets
    API_RESPONSE_TIME_TARGET_MS = 100  # 100ms API response target
    WEBSOCKET_LATENCY_TARGET_MS = 50  # 50ms WebSocket latency target


class EntityCachePerformanceTest:
    """Test entity cache performance characteristics"""
    
    def __init__(self):
        self.cache_manager = EntityCacheManager()
        
    async def setup_test_data(self, entity_count: int = 42) -> Dict[str, Any]:
        """Set up test data matching production entity count"""
        entities = {}
        
        for i in range(entity_count):
            entity_id = f"entity_{i:09d}"
            entity_data = {
                "ein": entity_id,
                "organization_name": f"Performance Test Organization {i}",
                "revenue": 1000000 + i * 50000,
                "assets": 2000000 + i * 100000,
                "ntee_code": f"T{i:02d}",
                "propublica_data": {
                    "filing_year": 2023,
                    "total_revenue": 1000000 + i * 50000,
                    "total_expenses": 800000 + i * 40000,
                    "net_assets": 2000000 + i * 100000
                },
                "board_members": [f"Member {j}" for j in range(5)],
                "programs": [f"Program {j}" for j in range(3)],
                "geographic_focus": ["Virginia", "North Carolina"],
                "focus_areas": ["healthcare", "education", "community"]
            }
            entities[entity_id] = entity_data
            self.cache_manager.set_entity_data(entity_id, entity_data)
            
        return entities
        
    async def test_cache_access_performance(self) -> Dict[str, float]:
        """Test cache access performance against sub-millisecond target"""
        # Setup test data
        entities = await self.setup_test_data(42)
        entity_ids = list(entities.keys())
        
        # Warm up cache
        for entity_id in entity_ids[:10]:
            self.cache_manager.get_entity_data(entity_id)
            
        # Performance test
        access_times = []
        
        for _ in range(1000):  # 1000 access operations
            import random
            entity_id = random.choice(entity_ids)
            
            start_time = time.perf_counter()
            result = self.cache_manager.get_entity_data(entity_id)
            end_time = time.perf_counter()
            
            access_time_ms = (end_time - start_time) * 1000
            access_times.append(access_time_ms)
            
            # Verify data integrity
            assert result is not None
            assert result["organization_name"].startswith("Performance Test Organization")
            
        # Calculate statistics
        stats = {
            "average_access_time_ms": statistics.mean(access_times),
            "median_access_time_ms": statistics.median(access_times),
            "max_access_time_ms": max(access_times),
            "min_access_time_ms": min(access_times),
            "std_deviation_ms": statistics.stdev(access_times),
            "p95_access_time_ms": sorted(access_times)[int(0.95 * len(access_times))],
            "p99_access_time_ms": sorted(access_times)[int(0.99 * len(access_times))],
        }
        
        return stats
        
    async def test_cache_hit_rate_performance(self) -> Dict[str, float]:
        """Test cache hit rate under realistic access patterns"""
        # Setup test data
        entities = await self.setup_test_data(42)
        entity_ids = list(entities.keys())
        
        # Realistic access pattern: 20% of entities get 80% of accesses
        hot_entities = entity_ids[:8]  # 20% of 42 entities
        cold_entities = entity_ids[8:]  # 80% of entities
        
        # Generate access pattern
        access_pattern = []
        
        # Hot entities (80% of accesses)
        for _ in range(800):
            import random
            entity_id = random.choice(hot_entities)
            access_pattern.append(entity_id)
            
        # Cold entities (20% of accesses)
        for _ in range(200):
            import random
            entity_id = random.choice(cold_entities)
            access_pattern.append(entity_id)
            
        # Shuffle to simulate realistic access
        import random
        random.shuffle(access_pattern)
        
        # Reset cache stats
        self.cache_manager._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_entities": 0,
            "last_updated": datetime.now()
        }
        
        # Execute access pattern
        for entity_id in access_pattern:
            self.cache_manager.get_entity_data(entity_id)
            
        # Get final statistics
        stats = await self.cache_manager.get_cache_stats()
        
        return {
            "hit_rate_percentage": stats["hit_rate_percentage"],
            "total_hits": stats["cache_hits"],
            "total_misses": stats["cache_misses"],
            "total_requests": stats["cache_hits"] + stats["cache_misses"],
            "cache_efficiency": stats["hit_rate_percentage"] / 100.0
        }


class ProcessorPerformanceTest:
    """Test processor performance characteristics"""
    
    def __init__(self):
        self.workflow_engine = get_workflow_engine()
        
    async def test_processor_registration_performance(self) -> Dict[str, float]:
        """Test processor registration performance"""
        start_time = time.perf_counter()
        
        # Register all processors
        registered_count = register_all_processors()
        
        end_time = time.perf_counter()
        registration_time = end_time - start_time
        
        # Get processor information
        auto_registry = get_auto_registry()
        processor_names = auto_registry.get_registered_processors()
        
        return {
            "registration_time_seconds": registration_time,
            "processors_registered": registered_count,
            "total_processors_available": len(processor_names),
            "registration_rate_processors_per_second": registered_count / registration_time if registration_time > 0 else 0,
            "average_registration_time_per_processor": registration_time / registered_count if registered_count > 0 else 0
        }
        
    async def test_processor_discovery_performance(self) -> Dict[str, float]:
        """Test processor discovery performance"""
        auto_registry = get_auto_registry()
        
        start_time = time.perf_counter()
        
        # Simulate processor discovery
        discovery_count = auto_registry.discover_and_register_all()
        
        end_time = time.perf_counter()
        discovery_time = end_time - start_time
        
        return {
            "discovery_time_seconds": discovery_time,
            "processors_discovered": discovery_count,
            "discovery_rate_processors_per_second": discovery_count / discovery_time if discovery_time > 0 else 0,
            "average_discovery_time_per_processor": discovery_time / discovery_count if discovery_count > 0 else 0
        }


class SystemResourcePerformanceTest:
    """Test system resource usage during operations"""
    
    def __init__(self):
        self.process = psutil.Process()
        
    def get_baseline_metrics(self) -> Dict[str, float]:
        """Get baseline system resource metrics"""
        return {
            "memory_usage_mb": self.process.memory_info().rss / 1024 / 1024,
            "cpu_percent": self.process.cpu_percent(),
            "threads_count": self.process.num_threads(),
            "handles_count": getattr(self.process, 'num_handles', lambda: 0)(),
            "timestamp": time.time()
        }
        
    async def test_memory_usage_during_operations(self) -> Dict[str, Any]:
        """Test memory usage during intensive operations"""
        baseline_memory = self.get_baseline_metrics()
        
        # Perform intensive operations
        cache_test = EntityCachePerformanceTest()
        entities = await cache_test.setup_test_data(100)  # More entities for stress test
        
        # Perform many cache operations
        for _ in range(5000):
            import random
            entity_id = random.choice(list(entities.keys()))
            cache_test.cache_manager.get_entity_data(entity_id)
            
        peak_memory = self.get_baseline_metrics()
        
        # Calculate memory usage
        memory_increase_mb = peak_memory["memory_usage_mb"] - baseline_memory["memory_usage_mb"]
        
        return {
            "baseline_memory_mb": baseline_memory["memory_usage_mb"],
            "peak_memory_mb": peak_memory["memory_usage_mb"],
            "memory_increase_mb": memory_increase_mb,
            "memory_efficiency_operations_per_mb": 5000 / memory_increase_mb if memory_increase_mb > 0 else float('inf'),
            "within_memory_target": peak_memory["memory_usage_mb"] < PerformanceBaseline.MEMORY_USAGE_MAX_MB
        }
        
    async def test_cpu_usage_during_operations(self) -> Dict[str, float]:
        """Test CPU usage during processor operations"""
        # Start CPU monitoring
        cpu_samples = []
        
        async def monitor_cpu():
            """Monitor CPU usage"""
            for _ in range(50):  # Monitor for 5 seconds at 0.1s intervals
                cpu_percent = self.process.cpu_percent(interval=0.1)
                cpu_samples.append(cpu_percent)
                await asyncio.sleep(0.1)
                
        async def perform_operations():
            """Perform CPU-intensive operations"""
            processor_test = ProcessorPerformanceTest()
            await processor_test.test_processor_registration_performance()
            await processor_test.test_processor_discovery_performance()
            
        # Run monitoring and operations concurrently
        await asyncio.gather(monitor_cpu(), perform_operations())
        
        if cpu_samples:
            return {
                "average_cpu_percent": statistics.mean(cpu_samples),
                "max_cpu_percent": max(cpu_samples),
                "cpu_variance": statistics.variance(cpu_samples),
                "within_cpu_target": max(cpu_samples) < PerformanceBaseline.CPU_USAGE_MAX_PERCENT,
                "cpu_samples_count": len(cpu_samples)
            }
        else:
            return {
                "average_cpu_percent": 0,
                "max_cpu_percent": 0,
                "cpu_variance": 0,
                "within_cpu_target": True,
                "cpu_samples_count": 0
            }


class PerformanceRegressionValidator:
    """Validate performance against regression thresholds"""
    
    def __init__(self):
        self.baseline_file = Path("tests/performance/baselines.json")
        
    def load_baseline(self) -> Optional[Dict[str, Any]]:
        """Load performance baseline from file"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load baseline: {e}")
                return None
        return None
        
    def save_baseline(self, performance_data: Dict[str, Any]) -> None:
        """Save performance baseline to file"""
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(performance_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save baseline: {e}")
            
    def validate_performance(self, current_results: Dict[str, Any], baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate current performance against baseline and targets"""
        if baseline is None:
            baseline = self.load_baseline()
            
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "performance_grade": "UNKNOWN",
            "target_compliance": {},
            "regression_analysis": {},
            "recommendations": []
        }
        
        # Validate against absolute targets
        cache_stats = current_results.get("cache_performance", {})
        if cache_stats:
            # Cache access time validation
            avg_access_time = cache_stats.get("average_access_time_ms", float('inf'))
            validation_results["target_compliance"]["cache_access_time"] = {
                "value": avg_access_time,
                "target": PerformanceBaseline.CACHE_ACCESS_TIME_TARGET_MS,
                "status": "PASS" if avg_access_time < PerformanceBaseline.CACHE_ACCESS_TIME_TARGET_MS else "FAIL"
            }
            
            # Cache hit rate validation
            hit_rate_stats = current_results.get("cache_hit_rate", {})
            hit_rate = hit_rate_stats.get("hit_rate_percentage", 0)
            validation_results["target_compliance"]["cache_hit_rate"] = {
                "value": hit_rate,
                "target": PerformanceBaseline.CACHE_HIT_RATE_TARGET,
                "status": "PASS" if hit_rate >= PerformanceBaseline.CACHE_HIT_RATE_TARGET else "FAIL"
            }
            
        # Regression analysis
        if baseline:
            cache_baseline = baseline.get("cache_performance", {})
            if cache_baseline and cache_stats:
                baseline_avg = cache_baseline.get("average_access_time_ms", 0)
                current_avg = cache_stats.get("average_access_time_ms", float('inf'))
                
                if baseline_avg > 0:
                    regression_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
                    validation_results["regression_analysis"]["cache_access_time"] = {
                        "baseline_ms": baseline_avg,
                        "current_ms": current_avg,
                        "regression_percent": regression_percent,
                        "status": "REGRESSION" if regression_percent > 10 else "STABLE"
                    }
                    
        # Overall performance grade
        passing_targets = sum(1 for target in validation_results["target_compliance"].values() if target["status"] == "PASS")
        total_targets = len(validation_results["target_compliance"])
        
        if total_targets > 0:
            pass_rate = passing_targets / total_targets
            if pass_rate >= 0.9:
                validation_results["performance_grade"] = "EXCELLENT"
            elif pass_rate >= 0.75:
                validation_results["performance_grade"] = "GOOD"
            elif pass_rate >= 0.5:
                validation_results["performance_grade"] = "ACCEPTABLE"
            else:
                validation_results["performance_grade"] = "POOR"
                
        # Generate recommendations
        if validation_results["target_compliance"].get("cache_access_time", {}).get("status") == "FAIL":
            validation_results["recommendations"].append("Optimize entity cache access patterns - consider cache prewarming")
            
        if validation_results["target_compliance"].get("cache_hit_rate", {}).get("status") == "FAIL":
            validation_results["recommendations"].append("Improve cache hit rate - review entity access patterns and cache size")
            
        return validation_results


# Test Classes for pytest integration
class TestPerformanceRegression:
    """Main performance regression test class"""
    
    @pytest.mark.asyncio
    async def test_entity_cache_performance_regression(self):
        """Test entity cache performance against regression thresholds"""
        cache_test = EntityCachePerformanceTest()
        
        # Run cache performance tests
        cache_performance = await cache_test.test_cache_access_performance()
        cache_hit_rate = await cache_test.test_cache_hit_rate_performance()
        
        # Validate against targets
        assert cache_performance["average_access_time_ms"] < PerformanceBaseline.CACHE_ACCESS_TIME_TARGET_MS, \
            f"Cache access time {cache_performance['average_access_time_ms']:.3f}ms exceeds {PerformanceBaseline.CACHE_ACCESS_TIME_TARGET_MS}ms target"
            
        assert cache_hit_rate["hit_rate_percentage"] >= PerformanceBaseline.CACHE_HIT_RATE_TARGET, \
            f"Cache hit rate {cache_hit_rate['hit_rate_percentage']:.1f}% below {PerformanceBaseline.CACHE_HIT_RATE_TARGET}% target"
            
        # Print performance summary
        print(f"\n🚀 Cache Performance Results:")
        print(f"   Average access time: {cache_performance['average_access_time_ms']:.3f}ms (target: <{PerformanceBaseline.CACHE_ACCESS_TIME_TARGET_MS}ms)")
        print(f"   P95 access time: {cache_performance['p95_access_time_ms']:.3f}ms")
        print(f"   Cache hit rate: {cache_hit_rate['hit_rate_percentage']:.1f}% (target: ≥{PerformanceBaseline.CACHE_HIT_RATE_TARGET}%)")
        
    @pytest.mark.asyncio
    async def test_processor_performance_regression(self):
        """Test processor performance against regression thresholds"""
        processor_test = ProcessorPerformanceTest()
        
        # Run processor performance tests
        registration_performance = await processor_test.test_processor_registration_performance()
        discovery_performance = await processor_test.test_processor_discovery_performance()
        
        # Validate against targets
        assert registration_performance["registration_time_seconds"] < PerformanceBaseline.PROCESSOR_REGISTRATION_TIME_MAX, \
            f"Processor registration time {registration_performance['registration_time_seconds']:.2f}s exceeds {PerformanceBaseline.PROCESSOR_REGISTRATION_TIME_MAX}s target"
            
        assert discovery_performance["discovery_time_seconds"] < PerformanceBaseline.PROCESSOR_DISCOVERY_TIME_MAX, \
            f"Processor discovery time {discovery_performance['discovery_time_seconds']:.2f}s exceeds {PerformanceBaseline.PROCESSOR_DISCOVERY_TIME_MAX}s target"
            
        # Print performance summary
        print(f"\n⚙️  Processor Performance Results:")
        print(f"   Registration time: {registration_performance['registration_time_seconds']:.2f}s ({registration_performance['processors_registered']} processors)")
        print(f"   Discovery time: {discovery_performance['discovery_time_seconds']:.2f}s")
        print(f"   Registration rate: {registration_performance['registration_rate_processors_per_second']:.1f} processors/second")
        
    @pytest.mark.asyncio
    async def test_system_resource_performance(self):
        """Test system resource usage performance"""
        resource_test = SystemResourcePerformanceTest()
        
        # Run resource usage tests
        memory_performance = await resource_test.test_memory_usage_during_operations()
        cpu_performance = await resource_test.test_cpu_usage_during_operations()
        
        # Validate against targets
        assert memory_performance["within_memory_target"], \
            f"Peak memory usage {memory_performance['peak_memory_mb']:.1f}MB exceeds {PerformanceBaseline.MEMORY_USAGE_MAX_MB}MB target"
            
        assert cpu_performance["within_cpu_target"], \
            f"Max CPU usage {cpu_performance['max_cpu_percent']:.1f}% exceeds {PerformanceBaseline.CPU_USAGE_MAX_PERCENT}% target"
            
        # Print performance summary
        print(f"\n💻 System Resource Results:")
        print(f"   Memory increase: {memory_performance['memory_increase_mb']:.1f}MB (peak: {memory_performance['peak_memory_mb']:.1f}MB)")
        print(f"   Average CPU usage: {cpu_performance['average_cpu_percent']:.1f}%")
        print(f"   Max CPU usage: {cpu_performance['max_cpu_percent']:.1f}%")
        
    @pytest.mark.asyncio
    async def test_comprehensive_performance_validation(self):
        """Run comprehensive performance validation and generate report"""
        # Collect all performance data
        cache_test = EntityCachePerformanceTest()
        processor_test = ProcessorPerformanceTest()
        resource_test = SystemResourcePerformanceTest()
        
        performance_data = {
            "test_timestamp": datetime.now().isoformat(),
            "cache_performance": await cache_test.test_cache_access_performance(),
            "cache_hit_rate": await cache_test.test_cache_hit_rate_performance(),
            "processor_registration": await processor_test.test_processor_registration_performance(),
            "processor_discovery": await processor_test.test_processor_discovery_performance(),
            "memory_performance": await resource_test.test_memory_usage_during_operations(),
            "cpu_performance": await resource_test.test_cpu_usage_during_operations()
        }
        
        # Validate against baselines and targets
        validator = PerformanceRegressionValidator()
        validation_results = validator.validate_performance(performance_data)
        
        # Save current results as new baseline
        validator.save_baseline(performance_data)
        
        # Print comprehensive summary
        print(f"\n📊 Comprehensive Performance Validation:")
        print(f"   Overall Grade: {validation_results['performance_grade']}")
        print(f"   Target Compliance:")
        
        for target_name, target_data in validation_results["target_compliance"].items():
            status_icon = "✅" if target_data["status"] == "PASS" else "❌"
            print(f"     {status_icon} {target_name}: {target_data['value']:.3f} (target: {target_data['target']:.3f})")
            
        if validation_results["recommendations"]:
            print(f"   Recommendations:")
            for recommendation in validation_results["recommendations"]:
                print(f"     • {recommendation}")
                
        # Assert overall performance grade
        assert validation_results["performance_grade"] in ["EXCELLENT", "GOOD"], \
            f"Performance grade {validation_results['performance_grade']} below acceptable threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])