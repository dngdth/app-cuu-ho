from typing import Dict, Any, List
from .base_client import BaseAPIClient

class NeedsClient(BaseAPIClient):
    """Client for Needs API operations"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all needs"""
        return self._get("/needs/")

    def get_by_id(self, needs_id: int) -> Dict[str, Any]:
        """Get need by ID"""
        return self._get(f"/needs/{needs_id}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new need"""
        return self._post("/needs/", data)

    def update(self, needs_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update need"""
        return self._put(f"/needs/{needs_id}", data)

    def delete(self, needs_id: int) -> Dict[str, Any]:
        """Delete need"""
        return self._delete(f"/needs/{needs_id}")