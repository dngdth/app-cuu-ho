"""
Transform service: Generate/Geocode/Parse data cho rescue requests
"""
import re
import ast
from datetime import datetime, timedelta
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from app.services.geocode_service import GeocodeService
from app.services.google_maps_service import GoogleMapsService

# Lazy imports để tránh circular dependency
def _get_models():
    from app.models.needs_model import Needs
    from app.models.disaster_type_model import DisasterType
    from app.models.region_model import Region
    return Needs, DisasterType, Region

class TransformService:
    def __init__(self):
        self.geocode_service = GeocodeService()

    @staticmethod
    def parse_posted_time(time_str: str) -> Optional[datetime]:
        """Convert '1w', '2d', '3h' → datetime"""
        if not time_str:
            return datetime.utcnow()
        
        time_str = str(time_str).strip().lower()
        match = re.match(r'(\d+)([wdhm])', time_str)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            now = datetime.utcnow()
            
            if unit == 'w':
                return now - timedelta(weeks=value)
            elif unit == 'd':
                return now - timedelta(days=value)
            elif unit == 'h':
                return now - timedelta(hours=value)
            elif unit == 'm':
                return now - timedelta(minutes=value)
        
        try:
            return datetime.fromisoformat(time_str.replace("z", "+00:00"))
        except ValueError:
            raise ValueError("posted_time must be ISO datetime or a relative duration")

    @staticmethod
    def map_text_to_score(text_value: str) -> float:
        """Map CAO/TRUNG BÌNH/THẤP → 3/2/1"""
        if not text_value:
            return 2.0
        
        text_value = str(text_value).strip().upper()
        try:
            score = float(text_value)
            if not 0 <= score <= 10:
                raise ValueError("Score must be between 0 and 10")
            return score
        except ValueError:
            pass
        mapping = {
            'CAO': 3.0,
            'TRUNG BÌNH': 2.0,
            'TRUNG BINH': 2.0,
            'THẤP': 1.0,
            'THAP': 1.0
        }
        
        return mapping.get(text_value, 2.0)

    @staticmethod
    def generate_title(content: str, location: str = None, max_length: int = 100) -> str:
        """Generate title từ content và location"""
        if not content:
            return "Yêu cầu cứu hộ"
        
        content = str(content).strip()
        first_sentence = content.split('.')[0].split('\n')[0].strip()
        
        keywords = []
        if 'cần' in first_sentence.lower() or 'hỗ trợ' in first_sentence.lower():
            keywords.append('CẦN HỖ TRỢ')
        
        location_short = ""
        if location:
            parts = [p.strip() for p in str(location).split(',')]
            if len(parts) >= 2:
                location_short = f"{parts[-2]}, {parts[-1]}"
            elif len(parts) == 1:
                location_short = parts[0]
        
        if keywords:
            title = f"{keywords[0]}"
            if location_short:
                title += f" - {location_short}"
        else:
            title = first_sentence[:max_length]
            if location_short and len(title) < 80:
                title += f" - {location_short}"
        
        if len(title) > max_length:
            title = title[:max_length-3] + "..."
        
        return title

    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Geocode location using existing geocode service
        Returns: (longitude, latitude) or None
        """
        if not location:
            return None
        
        location = str(location).strip()

        resolved = GoogleMapsService.resolve_record(location)
        if resolved:
            return tuple(resolved["coordinate"]["coordinates"])
        
        # Check if already has coordinate in format (lat, lng)
        coord_match = re.search(r'\(([0-9.]+),\s*([0-9.]+)\)', location)
        if coord_match:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))
            return (lng, lat)
        
        # Use existing geocode service
        try:
            result = self.geocode_service.forward_geocode(location)
            if result and result.get("coordinates"):
                coords = result["coordinates"]
                return (coords[0], coords[1])  # (lng, lat)
        except:
            pass
        
        return None

    @staticmethod
    def generate_map_link(coordinate: Optional[Tuple[float, float]]) -> Optional[str]:
        """Generate Google Maps link from coordinate"""
        if not coordinate:
            return None
        
        lng, lat = coordinate
        return f"https://maps.google.com/?q={lat},{lng}"

    @staticmethod
    def find_region_id(db: Session, location: str) -> Optional[int]:
        from app.services.region_catalog import find_region
        return find_region(db, location)

    @staticmethod
    def parse_needs_text(db: Session, needs_text: str) -> List[int]:
        """
        Parse needs từ text → list of IDs
        Input: "lương thực, thuốc men" hoặc "['lương thực', 'thuốc men']"
        """
        if not needs_text:
            return []
        
        Needs, _, _ = _get_models()
        
        needs_text = str(needs_text)
        
        # Try parse as list
        try:
            if needs_text.startswith('['):
                needs_names = ast.literal_eval(needs_text)
            else:
                needs_names = [n.strip() for n in needs_text.split(',')]
        except:
            needs_names = [n.strip() for n in needs_text.split(',')]
        
        needs_ids = []
        
        for name in needs_names:
            name = name.strip().lower()
            if not name:
                continue
            
            need = db.query(Needs).filter(
                Needs.name.ilike(f"%{name}%")
            ).first()
            
            if need:
                needs_ids.append(need.id)
        
        return needs_ids

    @staticmethod
    def parse_disaster_type_text(db: Session, disaster_text: str) -> List[int]:
        """Parse disaster_type từ text → list of IDs"""
        if not disaster_text:
            return []
        
        _, DisasterType, _ = _get_models()
        
        disaster_text = str(disaster_text).strip().lower()
        
        disaster = db.query(DisasterType).filter(
            DisasterType.name.ilike(f"%{disaster_text}%")
        ).first()
        
        if disaster:
            return [disaster.id]
        
        return []
