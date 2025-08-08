"""
Export Processor
Handles all export functionality including results, analytics, and reports.
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.base_processor import BaseProcessor, ProcessorMetadata
from src.core.workflow_engine import get_workflow_engine


class ExportProcessor(BaseProcessor):
    """
    Processor for handling all export operations.
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="export_processor",
            description="Export data to CSV, JSON and other formats",
            processor_type="export",
            dependencies=[],
            version="1.0.0",
            estimated_duration=30,
            requires_network=False,
            can_run_parallel=True
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, config) -> Dict[str, Any]:
        """
        Execute export operations based on config parameters.
        
        Args:
            config: Processing config with export_type and parameters
            
        Returns:
            Dictionary containing export results and file paths
        """
        context = config.parameters if hasattr(config, 'parameters') else config
        export_type = context.get('export_type', 'results')
        
        try:
            if export_type == 'results':
                return await self._export_results(context)
            elif export_type == 'analytics':
                return await self._export_analytics(context)
            elif export_type == 'board_network':
                return await self._export_board_network(context)
            elif export_type == 'classification':
                return await self._export_classification(context)
            elif export_type == 'government_opportunities':
                return await self._export_government_opportunities(context)
            else:
                raise ValueError(f"Unknown export type: {export_type}")
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'export_type': export_type
            }
    
    async def _export_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export general results."""
        try:
            result = await asyncio.create_subprocess_exec(
                "grant-research-env/Scripts/python.exe", "export_results.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'export_type': 'results',
                    'output': stdout.decode() if stdout else '',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Export failed: {stderr.decode() if stderr else 'Unknown error'}")
                
        except Exception as e:
            self.logger.error(f"Results export failed: {e}")
            raise
    
    async def _export_analytics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export analytics data."""
        try:
            result = await asyncio.create_subprocess_exec(
                "grant-research-env/Scripts/python.exe", "export_analytics.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'export_type': 'analytics',
                    'output': stdout.decode() if stdout else '',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Analytics export failed: {stderr.decode() if stderr else 'Unknown error'}")
                
        except Exception as e:
            self.logger.error(f"Analytics export failed: {e}")
            raise
    
    async def _export_board_network(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export board network analysis."""
        try:
            result = await asyncio.create_subprocess_exec(
                "grant-research-env/Scripts/python.exe", "export_board_network.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'export_type': 'board_network',
                    'output': stdout.decode() if stdout else '',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Board network export failed: {stderr.decode() if stderr else 'Unknown error'}")
                
        except Exception as e:
            self.logger.error(f"Board network export failed: {e}")
            raise
    
    async def _export_classification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export classification results."""
        try:
            result = await asyncio.create_subprocess_exec(
                "grant-research-env/Scripts/python.exe", "export_classification_results.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'export_type': 'classification',
                    'output': stdout.decode() if stdout else '',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Classification export failed: {stderr.decode() if stderr else 'Unknown error'}")
                
        except Exception as e:
            self.logger.error(f"Classification export failed: {e}")
            raise
    
    async def _export_government_opportunities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export government opportunities."""
        try:
            result = await asyncio.create_subprocess_exec(
                "grant-research-env/Scripts/python.exe", "export_government_opportunities.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'export_type': 'government_opportunities',
                    'output': stdout.decode() if stdout else '',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Government opportunities export failed: {stderr.decode() if stderr else 'Unknown error'}")
                
        except Exception as e:
            self.logger.error(f"Government opportunities export failed: {e}")
            raise


def register_processor():
    """Register the export processor."""
    engine = get_workflow_engine()
    engine.register_processor(ExportProcessor)