from typing import Dict, Any
from .base_client import BaseAPIClient

class GeocodeClient(BaseAPIClient):
    """Client for Geocoding API operations"""

    def forward_geocode(self, address: str) -> Dict[str, Any]:
        """Convert address text to coordinates"""
        params = {"address": address}
        return self._get("/geocode/forward", params)