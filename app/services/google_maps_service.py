"""Resolve Google Maps share links without treating the map camera as a pin."""
import html
import re
from functools import lru_cache
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import requests

NUMBER = r"-?\d+(?:\.\d+)?"
PAIR = re.compile(rf"(?:loc:)?\s*({NUMBER})\s*,\s*({NUMBER})\s*", re.IGNORECASE)
HOSTS = {"maps.app.goo.gl", "goo.gl", "maps.google.com", "maps.google.com.vn",
         "google.com", "www.google.com", "google.com.vn", "www.google.com.vn"}


def maps_url(value):
    if not isinstance(value, str) or len(value) > 8192:
        return False
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or parsed.hostname not in HOSTS:
            return False
        if parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            return False
        if parsed.hostname == "maps.app.goo.gl":
            return bool(parsed.path.strip("/"))
        if parsed.hostname == "goo.gl":
            return parsed.path.startswith("/maps/")
        if parsed.hostname.startswith("maps.google."):
            return parsed.path in ("", "/") or parsed.path.startswith("/maps")
        return parsed.path.startswith("/maps")
    except ValueError:
        return False


def point(latitude, longitude):
    lat, lng = float(latitude), float(longitude)
    if -90 <= lat <= 90 and -180 <= lng <= 180:
        return {"type": "Point", "coordinates": [lng, lat]}
    return None


def coordinate_from_url(url):
    if not maps_url(url):
        return None
    decoded = unquote(html.unescape(url))
    parsed = urlsplit(decoded)
    if parsed.hostname in ("maps.app.goo.gl", "goo.gl"):
        return None
    query = parse_qs(parsed.query)
    # A directions URL identifies its destination separately from the origin.
    for name in ("destination", "daddr"):
        if name in query:
            match = PAIR.fullmatch(query[name][0])
            return point(*match.groups()) if match else None
    # !3d/!4d identify a place pin; /@lat,lng is only the map camera.
    pins = re.findall(rf"!3d({NUMBER})!4d({NUMBER})", decoded)
    if pins:
        return point(*pins[-1])
    if "query_place_id" in query or "destination_place_id" in query:
        return None
    for name in ("q", "query"):
        if name in query:
            match = PAIR.fullmatch(query[name][0])
            if match:
                return point(*match.groups())
    match = re.search(rf"/maps/(?:place|search)/({NUMBER}),\s*({NUMBER})(?:/|$)", parsed.path)
    return point(*match.groups()) if match else None


def map_links(*texts):
    seen = set()
    for text in texts:
        for match in re.findall(r"https?://[^\s<>\"']+", str(text or "")):
            candidate = html.unescape(match).rstrip(".,;)]}")
            if maps_url(candidate) and candidate not in seen:
                seen.add(candidate)
                yield candidate
                if len(seen) >= 8:
                    return


class GoogleMapsService:
    @staticmethod
    @lru_cache(maxsize=2048)
    def resolve(url):
        if not maps_url(url):
            return None
        current = url
        visited = set()
        for _ in range(6):
            if not maps_url(current) or current in visited:
                return None
            visited.add(current)
            coordinate = coordinate_from_url(current)
            if coordinate:
                return {"coordinate": coordinate, "source_url": url, "coordinate_source": "google_maps"}
            # Only follow redirects between exact known Maps hosts. No arbitrary
            # URLs, HTML scraping, login, or consent-page traversal.
            if current.startswith("http:"):
                current = "https:" + current[5:]
            try:
                response = requests.get(current, allow_redirects=False, stream=True,
                                        timeout=(3, 7), headers={"User-Agent": "RescueMap/1.0"})
                try:
                    if response.status_code not in (301, 302, 303, 307, 308):
                        return None
                    destination = response.headers.get("Location")
                    if not destination:
                        return None
                    current = urljoin(current, destination)
                finally:
                    response.close()
            except requests.RequestException:
                return None
        return None

    @classmethod
    def resolve_record(cls, *texts):
        for url in map_links(*texts):
            result = cls.resolve(url)
            if result:
                return result
        return None
