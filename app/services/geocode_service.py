"""Public geocoding facade using Geoapify; no Google Cloud Billing required."""
from app.services.geoapify_service import GeoapifyService


class GeocodeService(GeoapifyService):
    def forward_geocode(self, address: str, limit: int = 1):
        result = self.resolve_address(address)
        if result['status'] != 'located':
            return None
        return {'type': 'Point', 'coordinates': result['coordinate']['coordinates'],
                'address': result['formatted_address'], 'provider': 'geoapify',
                'method': result['method'], 'precision': result['precision'],
                'place_id': result['place_id'], 'expires_at': result['expires_at']}
