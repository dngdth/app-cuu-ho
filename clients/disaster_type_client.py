from typing import Dict, Any, List
from .base_client import BaseAPIClient

class DisasterTypeClient(BaseAPIClient):
    """Client for Disaster Type API operations"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all disaster types"""
        return self._get("/disaster-type/")

    def get_by_id(self, disaster_type_id: int) -> Dict[str, Any]:
        """Get disaster type by ID"""
        return self._get(f"/disaster-type/{disaster_type_id}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new disaster type"""
        return self._post("/disaster-type/", data)

    def update(self, disaster_type_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update disaster type"""
        return self._put(f"/disaster-type/{disaster_type_id}", data)

    def delete(self, disaster_type_id: int) -> Dict[str, Any]:
        """Delete disaster type"""
        return self._delete(f"/disaster-type/{disaster_type_id}")