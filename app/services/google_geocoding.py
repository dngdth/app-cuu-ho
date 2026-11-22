"""Google address lookup with explicit failure reasons and destination precision."""
import math
import re
from datetime import datetime, timedelta, timezone

import requests

from app.core.config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_ENABLED
from app.services.address_utils import expected_provinces, folded

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
ADDRESS_TYPES = {"street_address", "premise", "subpremise", "establishment", "point_of_interest"}
STOP_WORDS = {"nha", "so", "duong", "hem", "kiet", "ngo", "dia", "chi", "thon", "xom"}


class ProviderError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def address_variants(address):
    address = re.sub(r"\s+", " ", str(address or "")).strip()
    address = re.sub(r"^địa chỉ\s*:\s*", "", address, flags=re.IGNORECASE)
    variants = [address] if address else []
    match = re.match(r"^(\d+[A-Za-z]?)\s*/\s*(\d+[A-Za-z]?)\s+([^/].*)$", address)
    if match:
        alley = "kiệt" if "hue" in folded(address) else "hẻm"
        variants.append(f"{match[1]} {alley} {match[2]} {match[3]}")
    return list(dict.fromkeys(variants))


def matching_candidate(original, candidate):
    formatted = candidate.get("formatted_address") or candidate.get("formattedAddress") or ""
    components = candidate.get("address_components", candidate.get("addressComponents", []))
    countries = [item.get("short_name", item.get("shortText", "")).upper()
                 for item in components if "country" in item.get("types", [])]
    if countries != ["VN"]:
        return "wrong_country"
    expected = expected_provinces(original)
    actual = folded(formatted)
    if expected and not any(re.search(r"\b" + re.escape(name) + r"\b", actual) for name in expected):
        return "wrong_region"
    first_part = folded(original.split(",")[0])
    tokens = set(re.findall(r"[a-z]+|\d+[a-z]?", first_part)) - STOP_WORDS
    actual_tokens = set(re.findall(r"[a-z]+|\d+[a-z]?", actual))
    if not tokens or not tokens.issubset(actual_tokens):
        return "address_mismatch"
    if candidate.get("partial_match"):
        return "partial_match"
    if not ADDRESS_TYPES.intersection(candidate.get("types", [])):
        return "area_or_street_center"
    return None


class GoogleGeocoder:
    def __init__(self, api_key=None):
        self.api_key = GOOGLE_MAPS_API_KEY if api_key is None else api_key

    @property
    def configured(self):
        return bool(self.api_key)

    @property
    def enabled(self):
        return GOOGLE_MAPS_ENABLED

    def _require_enabled(self):
        if not self.enabled:
            raise ProviderError("disabled")

    @staticmethod
    def _check_http(response):
        if response.status_code == 429:
            raise ProviderError("quota_exceeded")
        if response.status_code in (401, 403):
            raise ProviderError("request_denied")
        if response.status_code >= 400:
            raise ProviderError("provider_unavailable")

    def _geocode(self, query):
        self._require_enabled()
        response = requests.get(GEOCODING_URL, params={
            "address": query, "components": "country:VN", "region": "vn",
            "language": "vi", "key": self.api_key,
        }, timeout=(3, 7))
        self._check_http(response)
        body = response.json()
        status = body.get("status")
        if status == "ZERO_RESULTS":
            return []
        if status != "OK":
            raise ProviderError({"REQUEST_DENIED": "request_denied", "OVER_QUERY_LIMIT": "quota_exceeded",
                                 "OVER_DAILY_LIMIT": "quota_exceeded", "INVALID_REQUEST": "invalid_request"}.get(status, "provider_unavailable"))
        return body.get("results", [])

    def _text_search(self, query):
        self._require_enabled()
        response = requests.post(PLACES_URL, headers={
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.formattedAddress,places.location,places.types,places.addressComponents",
        }, json={"textQuery": query, "languageCode": "vi", "regionCode": "VN", "pageSize": 5}, timeout=(3, 7))
        self._check_http(response)
        return response.json().get("places", [])

    def resolve_address(self, address):
        variants = address_variants(address)
        base = {"provider": "google", "status": "unlocated", "attempts": [],
                "attempted_at": datetime.now(timezone.utc).isoformat()}
        if not variants or variants[0].lower().startswith(("http://", "https://")):
            return {**base, "status": "missing_address", "message": "Chưa có địa chỉ dạng chữ để tìm tọa độ."}
        if not self.configured:
            return {**base, "status": "needs_api_key", "message": "Chờ cấu hình Google API để tìm tọa độ từ địa chỉ."}
        if not self.enabled:
            return {**base, "status": "disabled", "message": "Đã tắt gọi Google API để kiểm soát chi phí. Cần kiểm tra quota trên Google Cloud trước khi bật lại."}
        if not expected_provinces(variants[0]):
            return {**base, "status": "insufficient_address", "message": "Cần bổ sung tỉnh/thành để đối chiếu kết quả địa chỉ."}
        coarse_match = False
        for query in variants:
            for method, search in (("geocoding", self._geocode), ("places_text_search", self._text_search)):
                attempt = {"method": method, "query": query}
                try:
                    candidates = search(query)
                except ProviderError as exc:
                    return {**base, "status": "provider_error", "error_code": exc.code,
                            "message": "Google chưa cho phép truy vấn. Kiểm tra API key, API đã bật và quota.",
                            "attempts": base["attempts"] + [{**attempt, "outcome": exc.code}]}
                except (requests.RequestException, ValueError):
                    return {**base, "status": "provider_error", "error_code": "network_or_response_error",
                            "message": "Chưa kết nối được dịch vụ tìm địa chỉ Google.",
                            "attempts": base["attempts"] + [{**attempt, "outcome": "network_or_response_error"}]}
                reasons = []
                for candidate in candidates:
                    reason = matching_candidate(variants[0], candidate)
                    if reason:
                        coarse_match |= reason in ("area_or_street_center", "partial_match")
                        reasons.append(reason)
                        continue
                    geometry = candidate.get("geometry", {})
                    location = geometry.get("location", candidate.get("location", {}))
                    try:
                        lat = float(location.get("lat", location.get("latitude")))
                        lng = float(location.get("lng", location.get("longitude")))
                        if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
                            raise ValueError("Invalid coordinate")
                    except (TypeError, ValueError):
                        reasons.append("invalid_coordinate")
                        continue
                    now = datetime.now(timezone.utc)
                    precision = geometry.get("location_type", "PLACE_MATCH")
                    # Keep API-derived content below the documented 30-day
                    # caching limit; hourly cleanup provides an extra-day margin.
                    return {**base, "status": "located", "method": method,
                            "coordinate": {"type": "Point", "coordinates": [lng, lat]},
                            "formatted_address": candidate.get("formatted_address", candidate.get("formattedAddress")),
                            "place_id": candidate.get("place_id", candidate.get("id")), "precision": precision,
                            "fetched_at": now.isoformat(), "expires_at": (now + timedelta(days=29)).isoformat(),
                            "message": "Đã tìm thấy vị trí từ địa chỉ. Cần đối chiếu với vị trí thực tế.",
                            "attempts": base["attempts"] + [{**attempt, "outcome": "matched"}]}
                base["attempts"].append({**attempt, "outcome": "rejected" if candidates else "no_results",
                                          "reasons": list(dict.fromkeys(reasons))})
        return {**base, "status": "needs_review" if coarse_match else "no_match",
                "message": "Chỉ tìm được vị trí gần đúng; cần kiểm tra thêm." if coarse_match else "Chưa tìm được địa chỉ khớp tỉnh/thành, đường và số nhà."}
