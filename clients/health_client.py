from typing import Dict, Any
from .base_client import BaseAPIClient

class HealthClient(BaseAPIClient):
    """Client for Health Check API operations"""

    def check(self) -> Dict[str, Any]:
        """Health check"""
        return self._get("/health")