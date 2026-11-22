from typing import Dict, Any, List
from .base_client import BaseAPIClient

class RegionClient(BaseAPIClient):
    """Client for Region API operations"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all regions"""
        return self._get("/region/")

    def get_by_id(self, region_id: int) -> Dict[str, Any]:
        """Get region by ID"""
        return self._get(f"/region/{region_id}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new region"""
        return self._post("/region/", data)

    def update(self, region_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update region"""
        return self._put(f"/region/{region_id}", data)

    def delete(self, region_id: int) -> Dict[str, Any]:
        """Delete region"""
        return self._delete(f"/region/{region_id}")

    def import_csv(self, file_path: str) -> Dict[str, Any]:
        """Import regions from CSV file"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(f"{self.base_url}/region/import-csv", files=files)
            response.raise_for_status()
            return response.json()