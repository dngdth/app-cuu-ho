import requests
from typing import Dict, Any, Optional

class BaseAPIClient:
    """Base class for API clients"""

    def __init__(self, base_url: str = "http://localhost:8099"):
        self.base_url = base_url
        self.session = requests.Session()

    def login(self, email: str, password: str):
        response = self._post("/auth/login", {"email": email, "password": password})
        self.session.headers["X-CSRF-Token"] = response["csrf_token"]
        return response["user"]

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request helper"""
        response = self.session.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request helper"""
        response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=300)
        response.raise_for_status()
        return response.json()

    def _put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PUT request helper"""
        response = self.session.put(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request helper"""
        response = self.session.delete(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
