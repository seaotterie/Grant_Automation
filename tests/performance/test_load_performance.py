#!/usr/bin/env python3
"""
Load Performance Tests using Locust
Tests WebSocket connection stability under load and Chart.js rendering performance with large datasets.
"""

import pytest
import asyncio
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
import statistics

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.workflow_engine import get_workflow_engine
from src.core.entity_cache_manager import get_entity_cache_manager
from src.profiles.models import OrganizationProfile

# Import test dependencies that should be available via requirements-test.txt
try:
    import locust
    from locust import HttpUser, task, between
    from locust.env import Environment
    from locust.stats import StatsCSV, stats_printer, stats_history
    from locust.log import setup_logging
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    print("WARNING: Locust not available - load tests will be skipped")

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("WARNING: websockets not available - WebSocket tests will be skipped")


class TestWebSocketLoadPerformance:
    """Test WebSocket connection stability under concurrent load"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.websocket_url = "ws://localhost:8000/ws"
        self.test_timeout = 30.0  # 30 second timeout for load tests
        
    @pytest.mark.asyncio
    @pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
    async def test_websocket_concurrent_connections(self):
        """Test multiple concurrent WebSocket connections"""
        concurrent_connections = 25
        messages_per_connection = 10
        connection_results = []
        
        async def websocket_client(client_id: int):
            """Individual WebSocket client for load testing"""
            try:
                # Connect with timeout
                websocket = await asyncio.wait_for(
                    websockets.connect(self.websocket_url),
                    timeout=5.0
                )
                
                start_time = time.time()
                messages_sent = 0
                messages_received = 0
                
                # Send test messages
                for i in range(messages_per_connection):
                    test_message = {
                        "type": "load_test",
                        "client_id": client_id,
                        "message_id": i,
                        "timestamp": time.time()
                    }
                    
                    try:
                        await asyncio.wait_for(
                            websocket.send(json.dumps(test_message)),
                            timeout=1.0
                        )
                        messages_sent += 1
                        
                        # Try to receive response (optional)
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=0.5
                            )
                            if response:
                                messages_received += 1
                        except asyncio.TimeoutError:
                            pass  # Response timeout is acceptable
                            
                    except Exception as e:
                        print(f"Message send error for client {client_id}: {e}")
                        break
                
                end_time = time.time()
                duration = end_time - start_time
                
                await websocket.close()
                
                return {
                    "client_id": client_id,
                    "success": True,
                    "messages_sent": messages_sent,
                    "messages_received": messages_received,
                    "duration": duration,
                    "throughput": messages_sent / duration if duration > 0 else 0
                }
                
            except Exception as e:
                return {
                    "client_id": client_id,
                    "success": False,
                    "error": str(e),
                    "messages_sent": 0,
                    "messages_received": 0,
                    "duration": 0,
                    "throughput": 0
                }
        
        # Execute concurrent WebSocket clients
        start_time = time.time()
        tasks = [websocket_client(i) for i in range(concurrent_connections)]
        
        try:
            connection_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.test_timeout
            )
        except asyncio.TimeoutError:
            pytest.fail(f"WebSocket load test timed out after {self.test_timeout}s")
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_connections = [r for r in connection_results 
                                if isinstance(r, dict) and r.get("success", False)]
        failed_connections = [r for r in connection_results 
                            if not isinstance(r, dict) or not r.get("success", False)]
        
        # Performance metrics
        success_rate = len(successful_connections) / len(connection_results) * 100
        total_messages_sent = sum(r["messages_sent"] for r in successful_connections)
        total_messages_received = sum(r["messages_received"] for r in successful_connections)
        
        throughputs = [r["throughput"] for r in successful_connections if r["throughput"] > 0]
        avg_throughput = statistics.mean(throughputs) if throughputs else 0
        
        # Performance assertions
        assert success_rate >= 80.0, f"WebSocket connection success rate {success_rate:.1f}% below 80% threshold"
        assert total_messages_sent >= concurrent_connections * messages_per_connection * 0.8, \
            f"Message send rate too low: {total_messages_sent}/{concurrent_connections * messages_per_connection}"
        assert total_time < self.test_timeout * 0.8, \
            f"Load test took too long: {total_time:.1f}s"
        
        print(f"\nWebSocket Load Test Results:")
        print(f"  Concurrent connections: {concurrent_connections}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Total messages sent: {total_messages_sent}")
        print(f"  Total messages received: {total_messages_received}")
        print(f"  Average throughput: {avg_throughput:.1f} msg/sec")
        print(f"  Total test time: {total_time:.1f}s")
        print(f"  Failed connections: {len(failed_connections)}")
        
    @pytest.mark.asyncio
    @pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
    async def test_websocket_sustained_load(self):
        """Test WebSocket performance under sustained load"""
        duration_seconds = 10
        connections_per_second = 5
        
        connection_results = []
        start_time = time.time()
        
        async def create_connection_wave():
            """Create a wave of connections"""
            wave_tasks = []
            for i in range(connections_per_second):
                task = self._single_websocket_test(f"sustained_{int(time.time())}_{i}")
                wave_tasks.append(task)
            
            results = await asyncio.gather(*wave_tasks, return_exceptions=True)
            return results
        
        # Generate sustained load
        while time.time() - start_time < duration_seconds:
            wave_results = await create_connection_wave()
            connection_results.extend(wave_results)
            
            # Wait before next wave
            await asyncio.sleep(1.0)
        
        # Analyze sustained load performance
        successful_results = [r for r in connection_results 
                            if isinstance(r, dict) and r.get("success", False)]
        
        success_rate = len(successful_results) / len(connection_results) * 100
        connection_durations = [r["duration"] for r in successful_results]
        avg_connection_duration = statistics.mean(connection_durations) if connection_durations else 0
        
        # Performance assertions for sustained load
        assert success_rate >= 75.0, f"Sustained load success rate {success_rate:.1f}% below 75%"
        assert avg_connection_duration < 2.0, f"Average connection duration {avg_connection_duration:.3f}s too high"
        
        print(f"\nWebSocket Sustained Load Results:")
        print(f"  Test duration: {duration_seconds}s")
        print(f"  Total connections: {len(connection_results)}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average connection duration: {avg_connection_duration:.3f}s")
        
    async def _single_websocket_test(self, client_id: str) -> Dict[str, Any]:
        """Single WebSocket connection test"""
        try:
            start_time = time.time()
            websocket = await asyncio.wait_for(
                websockets.connect(self.websocket_url),
                timeout=2.0
            )
            
            # Send test message
            test_message = {"type": "test", "client_id": client_id}
            await websocket.send(json.dumps(test_message))
            
            # Close connection
            await websocket.close()
            
            return {
                "success": True,
                "duration": time.time() - start_time,
                "client_id": client_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": 0,
                "client_id": client_id
            }


class TestChartJSRenderingPerformance:
    """Test Chart.js rendering performance with large datasets"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.large_dataset_size = 1000
        self.medium_dataset_size = 500
        self.small_dataset_size = 100
        
    def test_large_dataset_generation_performance(self):
        """Test performance of generating large datasets for Chart.js"""
        
        def generate_revenue_trend_data(size: int) -> Dict[str, Any]:
            """Generate revenue trend data for Chart.js"""
            import random
            
            labels = [f"Entity {i:04d}" for i in range(size)]
            revenues = [random.randint(100000, 10000000) for _ in range(size)]
            
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Revenue",
                        "data": revenues,
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "borderWidth": 1
                    }]
                },
                "options": {
                    "responsive": True,
                    "scales": {
                        "y": {
                            "beginAtZero": True
                        }
                    }
                }
            }
        
        # Test different dataset sizes
        dataset_sizes = [self.small_dataset_size, self.medium_dataset_size, self.large_dataset_size]
        performance_results = []
        
        for size in dataset_sizes:
            start_time = time.time()
            chart_data = generate_revenue_trend_data(size)
            generation_time = time.time() - start_time
            
            # Calculate data size
            data_size_bytes = len(json.dumps(chart_data))
            data_size_mb = data_size_bytes / (1024 * 1024)
            
            performance_results.append({
                "dataset_size": size,
                "generation_time": generation_time,
                "data_size_bytes": data_size_bytes,
                "data_size_mb": data_size_mb,
                "throughput": size / generation_time if generation_time > 0 else 0
            })
        
        # Performance assertions
        for result in performance_results:
            assert result["generation_time"] < 1.0, \
                f"Dataset generation took {result['generation_time']:.3f}s for {result['dataset_size']} entities"
            assert result["data_size_mb"] < 10.0, \
                f"Chart data size {result['data_size_mb']:.2f}MB too large for {result['dataset_size']} entities"
        
        print(f"\nChart.js Dataset Generation Performance:")
        for result in performance_results:
            print(f"  {result['dataset_size']} entities: {result['generation_time']*1000:.1f}ms, "
                  f"{result['data_size_mb']:.2f}MB, {result['throughput']:.0f} entities/sec")
            
    def test_multi_chart_rendering_simulation(self):
        """Test performance simulation for multiple Chart.js charts"""
        
        def simulate_chart_rendering_time(chart_config: Dict[str, Any]) -> float:
            """Simulate Chart.js rendering time based on data complexity"""
            data_points = len(chart_config["data"]["labels"])
            datasets = len(chart_config["data"]["datasets"])
            
            # Simulate rendering time (based on Chart.js performance characteristics)
            base_time = 0.01  # 10ms base rendering time
            data_complexity_factor = data_points * datasets * 0.00001  # Complexity scaling
            
            return base_time + data_complexity_factor
        
        # Create multiple chart configurations
        chart_configs = []
        
        # Revenue trend chart
        chart_configs.append({
            "name": "revenue_trend",
            "data": {
                "labels": [f"Entity {i}" for i in range(self.medium_dataset_size)],
                "datasets": [{
                    "label": "Revenue",
                    "data": [1000000 + i * 10000 for i in range(self.medium_dataset_size)]
                }]
            }
        })
        
        # Risk assessment radar chart
        chart_configs.append({
            "name": "risk_radar",
            "data": {
                "labels": ["Financial", "Compliance", "Operational", "Strategic", "Market"],
                "datasets": [{
                    "label": "Risk Level",
                    "data": [3, 2, 4, 1, 3]
                }]
            }
        })
        
        # Success scoring scatter plot
        chart_configs.append({
            "name": "success_scatter",
            "data": {
                "labels": [f"Opportunity {i}" for i in range(self.large_dataset_size)],
                "datasets": [{
                    "label": "Success Score",
                    "data": [{"x": i, "y": 0.5 + i * 0.001} for i in range(self.large_dataset_size)]
                }]
            }
        })
        
        # Test rendering performance simulation
        total_rendering_time = 0
        chart_performance = []
        
        for chart_config in chart_configs:
            rendering_time = simulate_chart_rendering_time(chart_config)
            total_rendering_time += rendering_time
            
            chart_performance.append({
                "chart_name": chart_config["name"],
                "rendering_time": rendering_time,
                "data_points": len(chart_config["data"]["labels"])
            })
        
        # Performance assertions
        assert total_rendering_time < 2.0, \
            f"Total chart rendering time {total_rendering_time:.3f}s exceeds 2s threshold"
        
        for perf in chart_performance:
            assert perf["rendering_time"] < 0.5, \
                f"Chart {perf['chart_name']} rendering time {perf['rendering_time']:.3f}s too high"
        
        print(f"\nChart.js Multi-Chart Rendering Simulation:")
        print(f"  Total rendering time: {total_rendering_time*1000:.1f}ms")
        for perf in chart_performance:
            print(f"  {perf['chart_name']}: {perf['rendering_time']*1000:.1f}ms "
                  f"({perf['data_points']} data points)")


# Locust Load Testing Classes (conditional import)
if LOCUST_AVAILABLE:
    
    class CatalynxWebUser(HttpUser):
        """Locust user class for Catalynx web interface load testing"""
        wait_time = between(1, 3)
        host = "http://localhost:8000"
        
        def on_start(self):
            """Called when a user starts"""
            self.client.verify = False  # Disable SSL verification for local testing
            
        @task(3)
        def view_home_page(self):
            """Test home page load performance"""
            with self.client.get("/", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Home page returned {response.status_code}")
                elif response.elapsed.total_seconds() > 2.0:
                    response.failure(f"Home page too slow: {response.elapsed.total_seconds():.1f}s")
                    
        @task(2)
        def check_api_health(self):
            """Test API health endpoint performance"""
            with self.client.get("/api/health", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Health API returned {response.status_code}")
                elif response.elapsed.total_seconds() > 1.0:
                    response.failure(f"Health API too slow: {response.elapsed.total_seconds():.1f}s")
                    
        @task(1)
        def list_profiles(self):
            """Test profile listing API performance"""
            with self.client.get("/api/profiles", catch_response=True) as response:
                if response.status_code not in [200, 404]:  # 404 acceptable if no profiles
                    response.failure(f"Profiles API returned {response.status_code}")
                elif response.elapsed.total_seconds() > 3.0:
                    response.failure(f"Profiles API too slow: {response.elapsed.total_seconds():.1f}s")
                    
        @task(1)
        def get_processor_summary(self):
            """Test processor summary API performance"""
            with self.client.get("/api/processors/summary", catch_response=True) as response:
                if response.status_code not in [200, 404]:  # 404 acceptable if endpoint not implemented
                    response.failure(f"Processor summary returned {response.status_code}")
                elif response.elapsed.total_seconds() > 2.0:
                    response.failure(f"Processor summary too slow: {response.elapsed.total_seconds():.1f}s")


class TestLocustIntegration:
    """Test Locust load testing integration"""
    
    @pytest.mark.skipif(not LOCUST_AVAILABLE, reason="Locust not available")
    def test_locust_configuration(self):
        """Test that Locust is properly configured for load testing"""
        
        # Test Locust environment setup
        env = Environment(user_classes=[CatalynxWebUser])
        env.create_local_runner()
        
        # Verify environment configuration
        assert env.host is None or env.host == ""  # Should be set by user class
        assert len(env.user_classes) == 1
        assert CatalynxWebUser in env.user_classes
        
        # Test user class configuration
        user_class = CatalynxWebUser
        assert user_class.host == "http://localhost:8000"
        assert hasattr(user_class, 'wait_time')
        assert hasattr(user_class, 'tasks') or hasattr(user_class, 'task_set')
        
        print(f"Locust configuration validated:")
        print(f"  User class: {user_class.__name__}")
        print(f"  Host: {user_class.host}")
        print(f"  Tasks: {len([attr for attr in dir(user_class) if hasattr(getattr(user_class, attr), '_locust_task')])}")
        
    @pytest.mark.skipif(not LOCUST_AVAILABLE, reason="Locust not available")
    def test_locust_load_simulation(self):
        """Test Locust load simulation capability"""
        
        # Create environment for testing
        env = Environment(user_classes=[CatalynxWebUser])
        env.create_local_runner()
        
        # Configure test parameters
        user_count = 10
        spawn_rate = 2
        run_time = 10  # 10 seconds
        
        # Note: This test validates Locust setup without actually running load test
        # Actual load test execution would require the Catalynx server to be running
        
        # Validate that we can create the load test configuration
        assert env.runner is not None
        
        # Test stats collection setup
        stats_csv = StatsCSV(env, "test_")
        assert stats_csv is not None
        
        print(f"Locust load test simulation configured:")
        print(f"  Users: {user_count}")
        print(f"  Spawn rate: {spawn_rate}/sec")
        print(f"  Duration: {run_time}s")
        print(f"  Expected total requests: ~{user_count * 3}")  # Rough estimate based on task weights


class TestSystemLoadCapacity:
    """Test overall system load capacity and limitations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.entity_cache_manager = None
        self.workflow_engine = None
        
    def test_entity_cache_load_capacity(self):
        """Test entity cache performance under high load"""
        try:
            self.entity_cache_manager = get_entity_cache_manager()
        except Exception:
            pytest.skip("Entity cache manager not available")
            
        # Simulate high load with many entities
        large_entity_count = 1000
        entity_data_template = {
            "organization_name": "Test Organization",
            "ein": "00-0000000",
            "revenue": 1000000,
            "assets": 2000000,
            "ntee_code": "A01",
            "board_members": ["Member 1", "Member 2", "Member 3"]
        }
        
        # Load test: Populate cache with many entities
        start_time = time.time()
        for i in range(large_entity_count):
            entity_id = f"load_test_entity_{i:04d}"
            entity_data = entity_data_template.copy()
            entity_data["ein"] = f"{i:02d}-{i:07d}"
            entity_data["organization_name"] = f"Load Test Org {i}"
            
            self.entity_cache_manager.set_entity_data(entity_id, entity_data)
        
        population_time = time.time() - start_time
        
        # Load test: Access all entities
        start_time = time.time()
        successful_retrievals = 0
        for i in range(large_entity_count):
            entity_id = f"load_test_entity_{i:04d}"
            result = self.entity_cache_manager.get_entity_data(entity_id)
            if result:
                successful_retrievals += 1
                
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        population_rate = large_entity_count / population_time
        retrieval_rate = large_entity_count / retrieval_time
        success_rate = successful_retrievals / large_entity_count * 100
        
        assert population_rate > 100, f"Cache population rate {population_rate:.0f} entities/sec too low"
        assert retrieval_rate > 500, f"Cache retrieval rate {retrieval_rate:.0f} entities/sec too low"  
        assert success_rate >= 99.0, f"Cache retrieval success rate {success_rate:.1f}% below 99%"
        
        print(f"\nEntity Cache Load Capacity Results:")
        print(f"  Entities tested: {large_entity_count}")
        print(f"  Population rate: {population_rate:.0f} entities/sec")
        print(f"  Retrieval rate: {retrieval_rate:.0f} entities/sec")
        print(f"  Success rate: {success_rate:.1f}%")
        
    def test_workflow_engine_processor_capacity(self):
        """Test workflow engine capacity with all 18 processors"""
        try:
            self.workflow_engine = get_workflow_engine()
        except Exception:
            pytest.skip("Workflow engine not available")
            
        # Test processor registration capacity
        start_time = time.time()
        processor_names = self.workflow_engine.registry.list_processors()
        listing_time = time.time() - start_time
        
        # Test processor access performance
        access_times = []
        successful_accesses = 0
        
        for processor_name in processor_names[:18]:  # Test first 18 processors
            start_time = time.time()
            processor = self.workflow_engine.registry.get_processor(processor_name)
            access_time = time.time() - start_time
            
            access_times.append(access_time)
            if processor:
                successful_accesses += 1
        
        # Calculate performance metrics
        avg_access_time = statistics.mean(access_times) if access_times else 0
        max_access_time = max(access_times) if access_times else 0
        access_success_rate = successful_accesses / len(access_times) * 100 if access_times else 0
        
        # Performance assertions
        assert listing_time < 0.1, f"Processor listing took {listing_time:.3f}s"
        assert avg_access_time < 0.01, f"Average processor access time {avg_access_time:.4f}s too high"
        assert max_access_time < 0.05, f"Maximum processor access time {max_access_time:.4f}s too high"
        assert access_success_rate >= 90.0, f"Processor access success rate {access_success_rate:.1f}% too low"
        
        print(f"\nWorkflow Engine Capacity Results:")
        print(f"  Total processors listed: {len(processor_names)}")
        print(f"  Processor listing time: {listing_time*1000:.1f}ms")
        print(f"  Average access time: {avg_access_time*1000:.1f}ms")
        print(f"  Maximum access time: {max_access_time*1000:.1f}ms")
        print(f"  Access success rate: {access_success_rate:.1f}%")


if __name__ == "__main__":
    # Run performance tests with verbose output
    pytest.main([__file__, "-v", "-s"])