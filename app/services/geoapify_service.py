"""Geoapify adapter: keyless-safe, strict address matching, bounded requests."""
import math
import time
from datetime import datetime, timedelta, timezone
import requests
from app.core import config
from app.services.address_matching import address_variants, matching_candidate, structured_address, street_key
from app.services.address_utils import expected_provinces
from app.services.provider_store import ProviderStore, ProviderLimit, cache_key


class ProviderError(Exception):
    pass


def provider_error_message(code):
    return {
        "network_or_response_error": "Kết nối tới Geoapify bị lỗi hoặc phản hồi không đọc được. Kiểm tra mạng rồi thử lại tác vụ.",
        "request_denied": "Geoapify từ chối truy vấn. Kiểm tra API key và quyền truy cập của key.",
        "provider_quota_exceeded": "Geoapify đã giới hạn lượt truy vấn. Kiểm tra hạn mức tại nhà cung cấp rồi thử lại sau.",
        "local_quota_exceeded": "Đã đạt hạn mức định vị của ứng dụng. Chờ sang kỳ hạn mức tiếp theo.",
        "local_rate_limit": "Có nhiều truy vấn định vị cùng lúc. Chờ vài giây rồi thử lại tác vụ.",
        "quota_store_unavailable": "Không đọc được bộ đếm hạn mức trong database. Kiểm tra kết nối PostgreSQL rồi thử lại.",
        "provider_unavailable": "Geoapify trả về lỗi dịch vụ. Thử lại tác vụ sau.",
        "invalid_response": "Geoapify trả về dữ liệu không đúng định dạng. Thử lại tác vụ sau.",
    }.get(code, "Chưa thể tìm địa chỉ. Kiểm tra cấu hình Geoapify rồi thử lại.")


class GeoapifyService:
    def __init__(self, api_key=None, store=None):
        self.api_key = config.GEOAPIFY_API_KEY if api_key is None else api_key
        self.store = store or ProviderStore()

    @property
    def configured(self):
        return bool(self.api_key)

    @property
    def enabled(self):
        return config.GEOCODING_ENABLED

    def _request(self, service, params):
        if not self.configured or not self.enabled:
            raise ProviderError("disabled_or_missing_key")
        key = cache_key(service, params)
        try:
            cached = self.store.cached(key)
            if cached is not None:
                return cached, True
            for retry in range(4):
                try:
                    self.store.reserve(service)
                    break
                except ProviderLimit as exc:
                    if str(exc) != "local_rate_limit" or retry == 3:
                        raise
                    time.sleep(0.5)
        except ProviderLimit:
            raise
        except Exception as exc:
            # No provider calls when the persistent quota store is unavailable.
            raise ProviderError("quota_store_unavailable") from exc
        endpoint = "geocode/search" if service == "geocoding" else "routing"
        try:
            response = requests.get("https://api.geoapify.com/v1/" + endpoint,
                params={**params, "apiKey": self.api_key}, headers={"User-Agent": "RescueMapPrototype/1.0"}, timeout=(3, 8))
            if response.status_code == 429:
                raise ProviderError("provider_quota_exceeded")
            if response.status_code in (401, 403):
                raise ProviderError("request_denied")
            if response.status_code != 200:
                raise ProviderError("provider_unavailable")
            body = response.json()
            if not isinstance(body, dict) or (service == "geocoding" and not isinstance(body.get("results"), list)):
                raise ProviderError("invalid_response")
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError("network_or_response_error") from exc
        try:
            self.store.remember(key, body, seconds=86400 if service == "geocoding" else 3600)
        except Exception:
            # Reservation was committed already. Cache failures must not retry HTTP.
            pass
        return body, False

    def resolve_address(self, address):
        base = {"provider": "geoapify", "attempts": [], "attempted_at": datetime.now(timezone.utc).isoformat()}
        variants = address_variants(address)
        if not variants or variants[0].startswith(("http://", "https://")):
            return {**base, "status": "missing_address", "message": "Chưa có địa chỉ dạng chữ để tìm tọa độ."}
        if not self.configured:
            return {**base, "status": "needs_api_key", "message": "Chờ GEOAPIFY_API_KEY để tìm tọa độ. Bản đồ OpenStreetMap vẫn dùng được."}
        if not self.enabled:
            return {**base, "status": "disabled", "message": "Định vị đang tắt trong cấu hình."}
        if not expected_provinces(variants[0]):
            return {**base, "status": "insufficient_address", "message": "Cần bổ sung tỉnh/thành để đối chiếu địa chỉ."}
        near, suggestions = False, []
        structured = structured_address(variants[0])
        queries = [{"text": variants[0]}]
        if structured:
            queries.append(structured)
        elif len(variants) > 1:
            queries.append({"text": variants[1]})
        for query in queries:
            attempt = {"method": "geoapify_geocoding", "query": query.get("text", variants[0])}
            if "text" not in query:
                attempt["structured_query"] = query
            try:
                body, cached = self._request("geocoding", {**query, "filter": "countrycode:vn", "lang": "vi", "limit": 5, "format": "json"})
            except (ProviderError, ProviderLimit) as exc:
                return {**base, "status": "quota_exceeded" if isinstance(exc, ProviderLimit) else "provider_error",
                        "error_code": str(exc), "message": provider_error_message(str(exc)),
                        "attempts": base["attempts"] + [{**attempt, "outcome": str(exc)}]}
            reasons = []
            for candidate in body.get("results", []):
                if not isinstance(candidate, dict):
                    reasons.append("invalid_candidate")
                    continue
                rank = candidate.get("rank") or {}
                if not isinstance(rank, dict):
                    rank = {}
                formatted = ", ".join(str(candidate.get(key) or "") for key in ("formatted", "city", "county", "state"))
                compatible = {"formatted_address": formatted,
                    "address_components": [{"short_name": str(candidate.get("country_code", "")).upper(), "types": ["country"]}],
                    "types": ["premise"] if candidate.get("result_type") in ("building", "amenity") else []}
                reason = matching_candidate(variants[0], compatible)
                confidence = rank.get("confidence", 0)
                if structured and candidate.get("street") and street_key(candidate["street"]) != street_key(structured["street"]):
                    reason = reason or "street_mismatch"
                if structured and candidate.get("housenumber") and str(candidate["housenumber"]).replace(" ", "").lower() != structured["housenumber"].lower():
                    reason = reason or "house_number_mismatch"
                building_confidence = rank.get("confidence_building_level")
                house_unverified = building_confidence is not None and (
                    not isinstance(building_confidence, (int, float)) or not math.isfinite(building_confidence) or building_confidence < 0.85)
                low_confidence = not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or confidence < 0.85
                if reason or low_confidence or house_unverified:
                    reasons.append(reason or ("house_not_verified" if house_unverified else "low_confidence"))
                    near = True
                    # A provider may echo the requested house number onto a street
                    # centroid and still call it a building. Keep it for review only.
                    street_confidence = rank.get("confidence_street_level", 0)
                    if not reason and house_unverified and isinstance(street_confidence, (int, float)) and street_confidence >= 0.85:
                        try:
                            lng, lat = float(candidate["lon"]), float(candidate["lat"])
                            if math.isfinite(lng) and math.isfinite(lat) and -180 <= lng <= 180 and -90 <= lat <= 90:
                                suggestion = {"coordinate": {"type": "Point", "coordinates": [lng, lat]},
                                    "precision": "STREET", "formatted_address": ", ".join(str(candidate[key]) for key in ("street", "city", "state") if candidate.get(key)),
                                    "place_id": candidate.get("place_id"), "requires_confirmation": True,
                                    "message": "Chỉ xác định được tuyến đường; chưa xác định vị trí số nhà/ngõ/kiệt."}
                                if suggestion not in suggestions and len(suggestions) < 3:
                                    suggestions.append(suggestion)
                        except (KeyError, TypeError, ValueError):
                            pass
                    continue
                try:
                    lng, lat = float(candidate["lon"]), float(candidate["lat"])
                    if not (math.isfinite(lng) and math.isfinite(lat) and -180 <= lng <= 180 and -90 <= lat <= 90):
                        raise ValueError()
                except (KeyError, TypeError, ValueError):
                    reasons.append("invalid_coordinate")
                    continue
                now = datetime.now(timezone.utc)
                return {**base, "status": "located", "method": "geoapify_geocoding", "precision": candidate["result_type"].upper(),
                    "coordinate": {"type": "Point", "coordinates": [lng, lat]}, "formatted_address": candidate.get("formatted"),
                    "place_id": candidate.get("place_id"), "confidence": confidence,
                    "fetched_at": now.isoformat(), "expires_at": (now + timedelta(days=29)).isoformat(),
                    "attribution": "© Geoapify, © OpenStreetMap contributors", "cached": cached,
                    "message": "Đã tìm thấy vị trí; cần đối chiếu địa chỉ thực tế trước khi điều phối.",
                    "attempts": base["attempts"] + [{**attempt, "outcome": "matched"}]}
            base["attempts"].append({**attempt, "outcome": "rejected" if reasons else "no_results", "reasons": reasons})
        if suggestions:
            now = datetime.now(timezone.utc)
            return {**base, "status": "needs_review", "suggestions": suggestions,
                    "fetched_at": now.isoformat(), "expires_at": (now + timedelta(days=29)).isoformat(),
                    "attribution": "© Geoapify, © OpenStreetMap contributors",
                    "message": "Đã tìm thấy tuyến đường đúng khu vực, nhưng chưa xác định được số nhà. Mở Kiểm tra / cập nhật để xem vị trí gợi ý và đối chiếu."}
        return {**base, "status": "needs_review" if near else "no_match", "message": "Chưa tìm được vị trí nhà khớp địa chỉ; có thể bổ sung tọa độ thủ công."}

    def route(self, start, end, mode="drive"):
        body, cached = self._request("routing", {"waypoints": f"{start[1]},{start[0]}|{end[1]},{end[0]}", "mode": mode, "lang": "vi"})
        features = body.get("features", [])
        if not features or features[0].get("geometry", {}).get("type") not in ("LineString", "MultiLineString"):
            raise ProviderError("no_route")
        properties = features[0].get("properties", {})
        return {"geometry": features[0]["geometry"], "distance_m": properties.get("distance"),
                "duration_s": properties.get("time"), "cached": cached, "provider": "geoapify",
                "attribution": "© Geoapify, © OpenStreetMap contributors",
                "warning": "Đường đi tham khảo theo mạng đường; không phản ánh ngập lụt, sạt lở hoặc đường đang bị chặn."}
