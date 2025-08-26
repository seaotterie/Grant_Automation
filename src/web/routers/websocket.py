#!/usr/bin/env python3
"""
WebSocket Router
Handles WebSocket connections for real-time progress updates
Extracted from monolithic main.py for better modularity
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Import progress services
from src.web.services.progress_service import ProgressService

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance (no prefix for WebSocket routes)
router = APIRouter(tags=["websocket"])

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, connection_info: Dict[str, Any] = None):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = connection_info or {}
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_progress_update(self, workflow_id: str, progress_data: Dict[str, Any]):
        """Send progress update to relevant connections."""
        message = json.dumps({
            "type": "progress_update",
            "workflow_id": workflow_id,
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connections (in a real implementation, would filter by workflow_id)
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

# Global connection manager
connection_manager = ConnectionManager()

# Progress service integration
progress_service = ProgressService(broadcast_func=connection_manager.send_progress_update)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication."""
    await connection_manager.connect(websocket)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "WebSocket connection established",
            "timestamp": datetime.now().isoformat(),
            "connection_count": connection_manager.get_connection_count()
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(websocket, message_data)
                
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    message_type = message_data.get("type", "unknown")
    
    try:
        if message_type == "subscribe_progress":
            # Subscribe to progress updates for a specific workflow
            workflow_id = message_data.get("workflow_id")
            if workflow_id:
                # Store subscription info
                if websocket in connection_manager.connection_data:
                    connection_manager.connection_data[websocket]["subscribed_workflows"] = \
                        connection_manager.connection_data[websocket].get("subscribed_workflows", [])
                    connection_manager.connection_data[websocket]["subscribed_workflows"].append(workflow_id)
                
                response = {
                    "type": "subscription_confirmed",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
        
        elif message_type == "ping":
            # Respond to ping with pong
            pong_response = {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(pong_response))
        
        elif message_type == "get_status":
            # Send current system status
            status_response = {
                "type": "system_status",
                "data": {
                    "active_connections": connection_manager.get_connection_count(),
                    "server_time": datetime.now().isoformat(),
                    "status": "operational"
                },
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(status_response))
        
        else:
            # Unknown message type
            error_response = {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(error_response))
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        error_response = {
            "type": "error",
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_response))


@router.get("/ws/stats")
async def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    try:
        return {
            "websocket_stats": {
                "active_connections": connection_manager.get_connection_count(),
                "total_connections_data": len(connection_manager.connection_data),
                "server_uptime": datetime.now().isoformat()  # Simplified uptime
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility function to broadcast progress updates from other parts of the application
async def broadcast_progress_update(workflow_id: str, progress_data: Dict[str, Any]):
    """Utility function to broadcast progress updates."""
    await connection_manager.send_progress_update(workflow_id, progress_data)


# Export the connection manager for use in other modules
def get_connection_manager():
    """Get the global connection manager instance."""
    return connection_manager