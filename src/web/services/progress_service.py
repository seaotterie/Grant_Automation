#!/usr/bin/env python3
"""
Progress Service for Real-Time Updates
Manages WebSocket connections and broadcasts progress updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Callable
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ProgressService:
    """Manages real-time progress updates via WebSocket connections."""
    
    def __init__(self):
        # workflow_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # workflow_id -> latest progress data
        self.progress_cache: Dict[str, Dict[str, Any]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(self, workflow_id: str, websocket: WebSocket):
        """Add a WebSocket connection for a workflow."""
        async with self._lock:
            if workflow_id not in self.active_connections:
                self.active_connections[workflow_id] = set()
            
            self.active_connections[workflow_id].add(websocket)
            logger.info(f"WebSocket connected for workflow {workflow_id}")
            
            # Send cached progress if available
            if workflow_id in self.progress_cache:
                try:
                    await websocket.send_text(json.dumps(self.progress_cache[workflow_id]))
                except Exception as e:
                    logger.error(f"Failed to send cached progress: {e}")
    
    async def disconnect(self, workflow_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if workflow_id in self.active_connections:
                self.active_connections[workflow_id].discard(websocket)
                
                # Clean up empty workflow connections
                if not self.active_connections[workflow_id]:
                    del self.active_connections[workflow_id]
                    logger.info(f"All connections closed for workflow {workflow_id}")
    
    async def broadcast_progress(self, workflow_id: str, progress_data: Dict[str, Any]):
        """Broadcast progress update to all connected clients."""
        # Add timestamp to progress data
        progress_data.update({
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id
        })
        
        # Cache the progress data
        async with self._lock:
            self.progress_cache[workflow_id] = progress_data
        
        # Broadcast to all connected clients
        if workflow_id in self.active_connections:
            connections_to_remove = set()
            message = json.dumps(progress_data)
            
            for websocket in self.active_connections[workflow_id].copy():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send progress to client: {e}")
                    connections_to_remove.add(websocket)
            
            # Remove failed connections
            if connections_to_remove:
                async with self._lock:
                    self.active_connections[workflow_id] -= connections_to_remove
    
    async def broadcast_completion(self, workflow_id: str, results: Dict[str, Any]):
        """Broadcast workflow completion."""
        completion_data = {
            "workflow_id": workflow_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        await self.broadcast_progress(workflow_id, completion_data)
        
        # Clean up after a delay
        await asyncio.sleep(5)
        async with self._lock:
            if workflow_id in self.progress_cache:
                del self.progress_cache[workflow_id]
    
    async def broadcast_error(self, workflow_id: str, error: str):
        """Broadcast workflow error."""
        error_data = {
            "workflow_id": workflow_id,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        
        await self.broadcast_progress(workflow_id, error_data)
    
    def get_active_workflows(self) -> List[str]:
        """Get list of workflows with active connections."""
        return list(self.active_connections.keys())
    
    def get_connection_count(self, workflow_id: str) -> int:
        """Get number of active connections for a workflow."""
        return len(self.active_connections.get(workflow_id, set()))
    
    async def cleanup_workflow(self, workflow_id: str):
        """Clean up all data for a workflow."""
        async with self._lock:
            # Close all connections
            if workflow_id in self.active_connections:
                for websocket in self.active_connections[workflow_id]:
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                del self.active_connections[workflow_id]
            
            # Remove cached progress
            if workflow_id in self.progress_cache:
                del self.progress_cache[workflow_id]
            
            logger.info(f"Cleaned up workflow {workflow_id}")

class ProgressTracker:
    """Helper class for tracking progress within workflows."""
    
    def __init__(self, workflow_id: str, progress_service: ProgressService):
        self.workflow_id = workflow_id
        self.progress_service = progress_service
        self.start_time = datetime.now()
        self.processed_count = 0
        self.total_count = 0
        self.current_processor = None
        self.current_organization = None
        self.qualification_breakdown = {}
    
    async def update_progress(self, 
                            processed: int = None,
                            total: int = None,
                            current_processor: str = None,
                            current_organization: str = None,
                            status: str = "running",
                            additional_data: Dict[str, Any] = None):
        """Update progress and broadcast to clients."""
        
        if processed is not None:
            self.processed_count = processed
        if total is not None:
            self.total_count = total
        if current_processor is not None:
            self.current_processor = current_processor
        if current_organization is not None:
            self.current_organization = current_organization
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if self.total_count > 0:
            progress_percentage = (self.processed_count / self.total_count) * 100
        
        # Calculate processing speed and ETA
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        processing_speed = self.processed_count / elapsed_time if elapsed_time > 0 else 0
        eta_minutes = None
        if processing_speed > 0 and self.total_count > self.processed_count:
            remaining = self.total_count - self.processed_count
            eta_seconds = remaining / processing_speed
            eta_minutes = eta_seconds / 60
        
        # Prepare progress data
        progress_data = {
            "progress_percentage": progress_percentage,
            "processed_count": self.processed_count,
            "total_count": self.total_count,
            "current_processor": self.current_processor,
            "current_organization": self.current_organization,
            "processing_speed": processing_speed,
            "eta_minutes": eta_minutes,
            "status": status,
            "elapsed_time": elapsed_time
        }
        
        # Add qualification breakdown if available
        if self.qualification_breakdown:
            progress_data["qualification_breakdown"] = self.qualification_breakdown
        
        # Add any additional data
        if additional_data:
            progress_data.update(additional_data)
        
        # Broadcast the update
        await self.progress_service.broadcast_progress(self.workflow_id, progress_data)
    
    def update_qualification_breakdown(self, breakdown: Dict[str, int]):
        """Update qualification factor breakdown."""
        self.qualification_breakdown = breakdown
    
    async def complete(self, results: Dict[str, Any]):
        """Mark workflow as completed and broadcast results."""
        await self.progress_service.broadcast_completion(self.workflow_id, results)
    
    async def error(self, error_message: str):
        """Mark workflow as failed and broadcast error."""
        await self.progress_service.broadcast_error(self.workflow_id, error_message)