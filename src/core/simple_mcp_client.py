"""
Simple MCP Client Stub
Placeholder for removed Fetch MCP functionality
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """Stub implementation for removed MCP client"""

    def __init__(self, *args, **kwargs):
        """Initialize stub client"""
        logger.warning("SimpleMCPClient is a stub - MCP functionality not available")

    async def fetch_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Stub method for URL fetching"""
        logger.warning(f"MCP fetch not available for URL: {url}")
        return {
            "success": False,
            "error": "MCP fetch functionality not available",
            "content": "",
            "status_code": 0
        }

    async def close(self):
        """Stub close method"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass