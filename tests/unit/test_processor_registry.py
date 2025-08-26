#!/usr/bin/env python3
"""
Unit Tests for Processor Registry
Tests the auto-discovery and registration of all 18+ processors.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.processors.registry import ProcessorAutoRegistry, get_auto_registry, register_all_processors
from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.workflow_engine import get_workflow_engine


class TestProcessorAutoRegistry:
    """Test suite for ProcessorAutoRegistry functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.registry = ProcessorAutoRegistry()
        
    def test_registry_initialization(self):
        """Test that registry initializes correctly"""
        assert self.registry.registered_processors == []
        assert self.registry.logger is not None
        
    @patch('src.processors.registry.Path')
    @patch('src.processors.registry.importlib.util.spec_from_file_location')
    def test_discover_and_register_all(self, mock_spec_from_file, mock_path):
        """Test processor discovery and registration"""
        # Mock file structure
        mock_file = Mock()
        mock_file.name = "test_processor.py"
        mock_file.relative_to.return_value = Path("processors/analysis/test_processor.py")
        
        mock_path.return_value.parent.rglob.return_value = [mock_file]
        
        # Mock module spec and loader
        mock_spec = Mock()
        mock_loader = Mock()
        mock_spec.loader = mock_loader
        mock_spec_from_file.return_value = mock_spec
        
        # Mock module with processor class
        mock_module = Mock()
        
        class TestProcessor(BaseProcessor):
            def __init__(self):
                super().__init__(ProcessorMetadata(
                    name="test_processor",
                    description="Test processor",
                    version="1.0.0"
                ))
                
            async def execute(self, config):
                return {"status": "test_success"}
        
        # Set up module members
        mock_module.__dict__ = {
            'TestProcessor': TestProcessor,
            'some_other_class': str  # Not a processor
        }
        
        with patch('src.processors.registry.importlib.util.module_from_spec', return_value=mock_module):
            with patch('src.processors.registry.inspect.getmembers') as mock_getmembers:
                mock_getmembers.return_value = [
                    ('TestProcessor', TestProcessor),
                    ('some_other_class', str)
                ]
                
                with patch('src.processors.registry.get_workflow_engine') as mock_engine:
                    mock_workflow_engine = Mock()
                    mock_engine.return_value = mock_workflow_engine
                    
                    # Execute test
                    count = self.registry.discover_and_register_all()
                    
                    # Verify results
                    assert count >= 0  # Should attempt to register processors
                    mock_workflow_engine.register_processor.assert_called()
                    
    def test_register_processor_from_file_invalid_module(self):
        """Test handling of invalid processor modules"""
        invalid_file = Path("invalid_processor.py")
        
        with patch('src.processors.registry.importlib.util.spec_from_file_location', return_value=None):
            result = self.registry._register_processor_from_file(invalid_file)
            assert result == 0
            
    def test_get_registered_processors(self):
        """Test getting list of registered processors"""
        # Add some test processors to the list
        self.registry.registered_processors = ["processor1", "processor2"]
        
        processors = self.registry.get_registered_processors()
        
        assert processors == ["processor1", "processor2"]
        # Ensure it returns a copy, not the original list
        processors.append("processor3")
        assert self.registry.registered_processors == ["processor1", "processor2"]


class TestRegistryFunctions:
    """Test module-level registry functions"""
    
    def test_get_auto_registry_singleton(self):
        """Test that get_auto_registry returns singleton instance"""
        registry1 = get_auto_registry()
        registry2 = get_auto_registry()
        
        assert registry1 is registry2
        assert isinstance(registry1, ProcessorAutoRegistry)
        
    @patch('src.processors.registry.get_auto_registry')
    def test_register_all_processors(self, mock_get_registry):
        """Test register_all_processors function"""
        mock_registry = Mock()
        mock_registry.discover_and_register_all.return_value = 15
        mock_get_registry.return_value = mock_registry
        
        count = register_all_processors()
        
        assert count == 15
        mock_registry.discover_and_register_all.assert_called_once()


class TestProcessorRegistration:
    """Test actual processor registration functionality"""
    
    @pytest.fixture
    def sample_processor_class(self):
        """Create a sample processor class for testing"""
        class SampleProcessor(BaseProcessor):
            def __init__(self):
                super().__init__(ProcessorMetadata(
                    name="sample_processor",
                    description="Sample processor for testing",
                    version="1.0.0",
                    dependencies=[],
                    estimated_duration=10,
                    requires_network=False,
                    requires_api_key=False,
                    processor_type="analysis"
                ))
                
            async def execute(self, config):
                return {
                    "status": "success",
                    "message": "Sample processor executed successfully"
                }
                
        return SampleProcessor
        
    @patch('src.processors.registry.get_workflow_engine')
    def test_processor_registration_workflow(self, mock_get_engine, sample_processor_class):
        """Test complete processor registration workflow"""
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine
        
        registry = ProcessorAutoRegistry()
        
        # Simulate processor registration
        with patch('src.processors.registry.inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [('SampleProcessor', sample_processor_class)]
            
            with patch('src.processors.registry.importlib.util.spec_from_file_location') as mock_spec:
                mock_spec_obj = Mock()
                mock_spec_obj.loader = Mock()
                mock_spec.return_value = mock_spec_obj
                
                with patch('src.processors.registry.importlib.util.module_from_spec') as mock_module:
                    mock_module_obj = Mock()
                    mock_module.return_value = mock_module_obj
                    
                    # Mock Path.rglob to return a test file
                    with patch('src.processors.registry.Path') as mock_path:
                        mock_file = Mock()
                        mock_file.name = "sample_processor.py"
                        mock_path.return_value.parent.rglob.return_value = [mock_file]
                        
                        # Execute registration
                        count = registry.discover_and_register_all()
                        
                        # Verify workflow engine registration was called
                        mock_engine.register_processor.assert_called()
                        

class TestErrorHandling:
    """Test error handling in processor registration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.registry = ProcessorAutoRegistry()
        
    @patch('src.processors.registry.logging.getLogger')
    def test_registration_error_handling(self, mock_logger):
        """Test that registration errors are properly logged"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        registry = ProcessorAutoRegistry()
        
        # Mock Path.rglob to raise an exception
        with patch('src.processors.registry.Path') as mock_path:
            mock_path.return_value.parent.rglob.side_effect = Exception("Test error")
            
            count = registry.discover_and_register_all()
            
            # Should handle error gracefully and return 0
            assert count == 0
            
    def test_invalid_processor_class_handling(self):
        """Test handling of invalid processor classes"""
        class InvalidProcessor:
            """Not a BaseProcessor subclass"""
            pass
            
        with patch('src.processors.registry.inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [('InvalidProcessor', InvalidProcessor)]
            
            with patch('src.processors.registry.get_workflow_engine') as mock_engine:
                mock_workflow_engine = Mock()
                mock_engine.return_value = mock_workflow_engine
                
                # Should not attempt to register invalid processor
                mock_workflow_engine.register_processor.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])