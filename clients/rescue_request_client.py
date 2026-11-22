from typing import Dict, Any, List
from .base_client import BaseAPIClient

class RescueRequestClient(BaseAPIClient):
    """Client for Rescue Request API operations"""

    def get_all(self, **params) -> List[Dict[str, Any]]:
        """Get all rescue requests with optional filtering"""
        return self._get("/rescue_request/", params)

    def get_by_id(self, request_id: int) -> Dict[str, Any]:
        """Get rescue request by ID"""
        return self._get(f"/rescue_request/{request_id}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new rescue request"""
        return self._post("/rescue_request/", data)

    def update(self, request_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update rescue request"""
        return self._put(f"/rescue_request/{request_id}", data)

    def delete(self, request_id: int) -> Dict[str, Any]:
        """Delete rescue request"""
        return self._delete(f"/rescue_request/{request_id}")

    def import_json_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import rescue requests from JSON data"""
        return self._post("/rescue_request/import-json-data", data)

    def process_data(self, data: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        return self._post("/processing/import", {"records": data, **options})
