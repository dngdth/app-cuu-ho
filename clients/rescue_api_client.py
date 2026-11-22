from .rescue_request_client import RescueRequestClient
from .needs_client import NeedsClient
from .disaster_type_client import DisasterTypeClient
from .region_client import RegionClient
from .geocode_client import GeocodeClient
from .health_client import HealthClient

class RescueAPIClient:
    """Main API client with all resource clients"""

    def __init__(self, base_url: str = "http://localhost:8099"):
        self.base_url = base_url
        self.rescue_requests = RescueRequestClient(base_url)
        self.needs = NeedsClient(base_url)
        self.disaster_types = DisasterTypeClient(base_url)
        self.regions = RegionClient(base_url)
        self.geocode = GeocodeClient(base_url)
        self.health = HealthClient(base_url)

    def login(self, email: str, password: str):
        user = self.rescue_requests.login(email, password)
        for client in (self.needs, self.disaster_types, self.regions, self.geocode, self.health):
            client.session = self.rescue_requests.session
        return user
