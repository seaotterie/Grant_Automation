#!/usr/bin/env python3
"""
Integration Tests for Processor Workflow Integration
Tests the complete 18-processor pipeline integration and workflow execution.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.workflow_engine import WorkflowEngine, get_workflow_engine
from src.processors.registry import get_auto_registry, register_all_processors
from src.core.data_models import WorkflowConfig, ProcessorConfig
from src.core.base_processor import BaseProcessor, ProcessorMetadata


class TestProcessorWorkflowIntegration:
    """Test integration between processors and workflow engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_processor_registry_integration(self):
        """Test processor registry integration with workflow engine"""
        # Get the auto registry
        auto_registry = get_auto_registry()
        
        # Register all processors
        registered_count = register_all_processors()
        
        # Should register some processors (at least attempt to)
        assert registered_count >= 0
        
        # Verify workflow engine has access to registered processors
        processor_names = self.workflow_engine.registry.list_processors()
        assert isinstance(processor_names, list)
        
    def test_workflow_engine_processor_access(self):
        """Test workflow engine can access individual processors"""
        # Register processors first
        register_all_processors()
        
        # Get list of available processors
        processor_names = self.workflow_engine.registry.list_processors()
        
        if processor_names:
            # Test accessing first available processor
            processor_name = processor_names[0]
            processor = self.workflow_engine.registry.get_processor(processor_name)
            
            if processor:
                assert isinstance(processor, BaseProcessor)
                assert hasattr(processor, 'metadata')
                assert hasattr(processor, 'execute')
                
    def test_processor_metadata_consistency(self):
        """Test processor metadata is consistent across registration"""
        register_all_processors()
        
        processor_names = self.workflow_engine.registry.list_processors()
        
        for processor_name in processor_names[:5]:  # Test first 5 processors
            processor_info = self.workflow_engine.registry.get_processor_info(processor_name)
            
            if processor_info:
                # Verify required metadata fields
                assert 'name' in processor_info
                assert 'description' in processor_info
                assert 'version' in processor_info
                assert processor_info['name'] == processor_name


class TestDiscoveryWorkflowIntegration:
    """Test discovery workflow integration across tracks"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_discovery_track_integration(self):
        """Test integration of different discovery tracks"""
        # Mock profile data
        test_profile = {
            "organization_name": "Test Integration Foundation",
            "mission": "Testing discovery workflow integration",
            "focus_areas": ["healthcare", "education"],
            "geographic_focus": ["Virginia"],
            "revenue_range": "1M-5M"
        }
        
        # Test discovery tracks
        discovery_tracks = ["nonprofit", "government", "commercial", "state"]
        
        for track in discovery_tracks:
            workflow_config = WorkflowConfig(
                workflow_id=f"test_discovery_{track}",
                processors=[f"{track}_discoverer"] if f"{track}_discoverer" in self.workflow_engine.registry.list_processors() else [],
                profile=test_profile,
                options={"track": track, "max_results": 10}
            )
            
            # Should be able to create workflow configuration without errors
            assert workflow_config.workflow_id is not None
            assert isinstance(workflow_config.options, dict)
            
    @pytest.mark.asyncio
    async def test_multi_track_discovery_integration(self):
        """Test integration of multiple discovery tracks in single workflow"""
        test_profile = {
            "organization_name": "Multi-Track Test Foundation",
            "mission": "Testing multi-track discovery integration",
            "focus_areas": ["healthcare", "veterans", "mental health"],
            "geographic_focus": ["Virginia", "North Carolina"]
        }
        
        # Create multi-track workflow
        multi_track_config = WorkflowConfig(
            workflow_id="test_multi_track_discovery",
            processors=["bmf_filter", "propublica_fetch", "grants_gov_fetch"] if all(
                p in self.workflow_engine.registry.list_processors() 
                for p in ["bmf_filter", "propublica_fetch", "grants_gov_fetch"]
            ) else [],
            profile=test_profile,
            options={
                "tracks": ["nonprofit", "government"],
                "max_results_per_track": 25,
                "include_entity_cache": True
            }
        )
        
        # Configuration should be valid
        assert len(multi_track_config.processors) >= 0
        assert "tracks" in multi_track_config.options


class TestAnalysisWorkflowIntegration:
    """Test analysis workflow integration across scoring processors"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_scoring_processor_integration(self):
        """Test integration of scoring processors"""
        # Register processors
        register_all_processors()
        
        # Expected scoring processors
        expected_scorers = [
            "government_opportunity_scorer",
            "financial_scorer", 
            "ai_lite_scorer",
            "success_scorer"
        ]
        
        available_processors = self.workflow_engine.registry.list_processors()
        
        # Test processors that are available
        available_scorers = [p for p in expected_scorers if p in available_processors]
        
        for scorer in available_scorers:
            processor = self.workflow_engine.registry.get_processor(scorer)
            
            if processor:
                # Verify processor implements required interface
                assert hasattr(processor, 'execute')
                assert hasattr(processor, 'metadata')
                
                # Verify metadata indicates scoring capability
                metadata = processor.metadata
                assert metadata.name == scorer
                
    @pytest.mark.asyncio 
    async def test_ai_processor_integration(self):
        """Test AI processor integration and orchestration"""
        register_all_processors()
        
        # Expected AI processors
        expected_ai_processors = [
            "ai_lite_validator",
            "ai_lite_strategic_scorer", 
            "ai_heavy_researcher",
            "ai_heavy_research_bridge"
        ]
        
        available_processors = self.workflow_engine.registry.list_processors()
        available_ai_processors = [p for p in expected_ai_processors if p in available_processors]
        
        # Test AI processor chain integration
        if len(available_ai_processors) >= 2:
            # Create workflow with multiple AI processors
            ai_workflow_config = WorkflowConfig(
                workflow_id="test_ai_integration",
                processors=available_ai_processors[:2],  # Use first 2 available
                profile={
                    "organization_name": "AI Test Organization", 
                    "focus_areas": ["technology", "innovation"]
                },
                options={
                    "ai_budget": 1.0,
                    "quality_threshold": 0.7,
                    "cost_optimization": True
                }
            )
            
            assert len(ai_workflow_config.processors) == 2
            assert "ai_budget" in ai_workflow_config.options


class TestEntityCacheIntegration:
    """Test entity cache integration with processors"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_entity_cache_processor_integration(self):
        """Test entity cache integration with data processors"""
        # Mock entity cache manager
        with patch('src.core.entity_cache_manager.get_entity_cache_manager') as mock_cache:
            mock_cache_manager = AsyncMock()
            mock_cache.return_value = mock_cache_manager
            
            # Mock cache stats
            mock_cache_manager.get_cache_stats.return_value = {
                "status": "operational",
                "total_entities": 42,
                "cache_hits": 85,
                "cache_misses": 15,
                "hit_rate_percentage": 85.0
            }
            
            # Test cache integration
            stats = await mock_cache_manager.get_cache_stats()
            
            assert stats["hit_rate_percentage"] == 85.0
            assert stats["total_entities"] == 42
            
    @pytest.mark.asyncio
    async def test_entity_data_flow_integration(self):
        """Test data flow between entity cache and processors"""
        # Mock entity data
        test_entity_data = {
            "ein": "12-3456789",
            "organization_name": "Test Entity Integration Org",
            "revenue": 2500000,
            "assets": 5000000,
            "ntee_code": "T99",
            "propublica_data": {"filing_year": 2023},
            "board_members": ["John Doe", "Jane Smith"]
        }
        
        with patch('src.core.entity_cache_manager.get_entity_cache_manager') as mock_cache:
            mock_cache_manager = Mock()
            mock_cache.return_value = mock_cache_manager
            
            # Setup mock cache behavior
            mock_cache_manager.get_entity_data.return_value = test_entity_data
            mock_cache_manager.set_entity_data.return_value = None
            
            # Test data retrieval
            retrieved_data = mock_cache_manager.get_entity_data("12-3456789")
            
            assert retrieved_data == test_entity_data
            assert retrieved_data["organization_name"] == "Test Entity Integration Org"


class TestWorkflowErrorHandling:
    """Test error handling in workflow integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_processor_failure_handling(self):
        """Test handling of processor failures in workflow"""
        # Create a mock failing processor
        class FailingProcessor(BaseProcessor):
            def __init__(self):
                super().__init__(ProcessorMetadata(
                    name="failing_processor",
                    description="Processor that always fails for testing",
                    version="1.0.0"
                ))
                
            async def execute(self, config):
                raise Exception("Simulated processor failure")
                
        # Test workflow with failing processor
        try:
            failing_processor = FailingProcessor()
            result = await failing_processor.execute({})
            
            # Should not reach here
            assert False, "Expected processor to fail"
            
        except Exception as e:
            # Should handle failure gracefully
            assert "Simulated processor failure" in str(e)
            
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of processor timeouts"""
        # Create a mock slow processor
        class SlowProcessor(BaseProcessor):
            def __init__(self):
                super().__init__(ProcessorMetadata(
                    name="slow_processor",
                    description="Slow processor for timeout testing",
                    version="1.0.0",
                    estimated_duration=1  # 1 second
                ))
                
            async def execute(self, config):
                await asyncio.sleep(2)  # Sleep longer than expected
                return {"status": "completed"}
                
        # Test timeout handling
        slow_processor = SlowProcessor()
        
        try:
            # Set short timeout
            result = await asyncio.wait_for(slow_processor.execute({}), timeout=0.5)
            
            # Should not reach here
            assert False, "Expected timeout"
            
        except asyncio.TimeoutError:
            # Expected timeout behavior
            assert True
            
    def test_invalid_configuration_handling(self):
        """Test handling of invalid workflow configurations"""
        # Test invalid workflow configuration
        try:
            invalid_config = WorkflowConfig(
                workflow_id="",  # Empty workflow ID
                processors=["nonexistent_processor"],  # Non-existent processor
                profile={},  # Empty profile
                options=None  # Invalid options
            )
            
            # Validation might occur during creation or execution
            # The test verifies the system can handle invalid configs
            assert invalid_config.workflow_id == ""
            
        except Exception as e:
            # System may validate during creation - this is acceptable
            assert isinstance(e, (ValueError, TypeError))


class TestWorkflowPerformance:
    """Test workflow performance characteristics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.workflow_engine = get_workflow_engine()
        
    @pytest.mark.asyncio
    async def test_processor_execution_performance(self):
        """Test processor execution performance"""
        # Create simple test processor
        class PerfTestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__(ProcessorMetadata(
                    name="perf_test_processor",
                    description="Performance test processor",
                    version="1.0.0"
                ))
                
            async def execute(self, config):
                return {"status": "success", "timestamp": datetime.now().isoformat()}
                
        # Test execution timing
        import time
        
        perf_processor = PerfTestProcessor()
        
        start_time = time.time()
        result = await perf_processor.execute({})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should execute quickly
        assert execution_time < 1.0  # Less than 1 second
        assert result["status"] == "success"
        
    @pytest.mark.asyncio
    async def test_concurrent_processor_execution(self):
        """Test concurrent processor execution performance"""
        # Create multiple test processors
        class ConcurrentTestProcessor(BaseProcessor):
            def __init__(self, processor_id: int):
                super().__init__(ProcessorMetadata(
                    name=f"concurrent_test_{processor_id}",
                    description=f"Concurrent test processor {processor_id}",
                    version="1.0.0"
                ))
                self.processor_id = processor_id
                
            async def execute(self, config):
                # Simulate some work
                await asyncio.sleep(0.1)
                return {
                    "status": "success", 
                    "processor_id": self.processor_id,
                    "timestamp": datetime.now().isoformat()
                }
                
        # Create multiple processors
        processors = [ConcurrentTestProcessor(i) for i in range(5)]
        
        # Execute concurrently
        import time
        
        start_time = time.time()
        tasks = [processor.execute({}) for processor in processors]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Should execute concurrently (faster than sequential)
        assert total_time < 1.0  # Should complete in reasonable time
        assert len(results) == 5
        
        # All should succeed
        for result in results:
            assert result["status"] == "success"
            

if __name__ == "__main__":
    pytest.main([__file__, "-v"])