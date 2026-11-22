"""Resolve an input location without conflating missing keys with missing addresses."""
import re
from ai.address_extraction import extract_address, missing_address
from app.services.geocode_service import GeocodeService
from app.services.google_maps_service import GoogleMapsService, coordinate_from_url, map_links, point


def coordinate_in_text(*texts):
    for url in map_links(*texts):
        coordinate = coordinate_from_url(url)
        if coordinate:
            return coordinate
    for text in texts:
        match = re.search(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)", text or "")
        if match:
            coordinate = point(*match.groups())
            if coordinate:
                return coordinate
    return None


def resolve_location(row, network=True):
    row = dict(row)
    if missing_address(row.get("location")):
        row["location"] = extract_address(row.get("content"))
    source_url = row.get("map_link")
    coordinate = row.get("coordinate")
    source = "provided" if coordinate else None
    if coordinate is None:
        coordinate = coordinate_in_text(source_url, row.get("location"), row.get("content"))
        if coordinate:
            source = "source_text"
    if coordinate is None and network:
        resolved = GoogleMapsService.resolve_record(source_url, row.get("location"), row.get("content"))
        if resolved:
            coordinate, source, source_url = resolved["coordinate"], "google_maps", resolved["source_url"]
    if coordinate:
        return {"coordinate": coordinate, "coordinate_source": source, "source_map_link": source_url,
                "geocoding": {"status": "located", "provider": source, "precision": "SOURCE_POINT"}, "warnings": []}
    if network:
        geocoding = GeocodeService().resolve_address(row.get("location"))
    else:
        geocoding = {"status": "not_requested", "provider": "geoapify", "message": "Chưa yêu cầu tìm tọa độ qua dịch vụ bản đồ."}
    coordinate = geocoding.get("coordinate")
    # Coordinates live in the geometry column, not twice in stored JSON.
    details = {key: value for key, value in geocoding.items() if key != "coordinate"}
    return {"coordinate": coordinate, "coordinate_source": "geoapify" if coordinate else None,
            "source_map_link": source_url, "geocoding": details,
            "warnings": [geocoding["message"]] if geocoding.get("message") else []}
