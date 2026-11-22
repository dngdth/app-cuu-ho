from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
import requests

from app.services.google_geocoding import GoogleGeocoder, ProviderError, address_variants

ADDRESS = "10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế"
FORMATTED = "10 kiệt 82 Đào Duy Anh, Phú Xuân, Huế, Việt Nam"


def geocode_candidate(**changes):
    return {"formatted_address": FORMATTED, "place_id": "test-place",
            "geometry": {"location": {"lat": 16.47, "lng": 107.57}, "location_type": "ROOFTOP"},
            "types": ["street_address"],
            "address_components": [{"short_name": "VN", "types": ["country"]}], **changes}


def place_candidate(**changes):
    return {"formattedAddress": FORMATTED, "id": "test-place",
            "location": {"latitude": 16.47, "longitude": 107.57}, "types": ["premise"],
            "addressComponents": [{"shortText": "VN", "types": ["country"]}], **changes}


def response(body, code=200):
    return Mock(status_code=code, json=Mock(return_value=body))


@pytest.fixture(autouse=True)
def no_unexpected_network(monkeypatch):
    monkeypatch.setattr("app.services.google_geocoding.GOOGLE_MAPS_ENABLED", True)
    def blocked(*args, **kwargs):
        raise AssertionError("Unexpected real Google API request in tests")
    monkeypatch.setattr(requests, "get", blocked)
    monkeypatch.setattr(requests, "post", blocked)


def test_disabled_with_valid_key_never_calls_paid_services(monkeypatch):
    monkeypatch.setattr("app.services.google_geocoding.GOOGLE_MAPS_ENABLED", False)
    service = GoogleGeocoder(api_key="test-key")
    result = service.resolve_address(ADDRESS)
    assert result["status"] == "disabled" and result["attempts"] == []
    for search in (service._geocode, service._text_search):
        with pytest.raises(ProviderError, match="disabled"):
            search(ADDRESS)


def test_missing_key_makes_no_network_request():
    result = GoogleGeocoder(api_key="").resolve_address(ADDRESS)
    assert result["status"] == "needs_api_key"
    assert "coordinate" not in result


def test_slash_address_variants_keep_original_and_alley_number():
    variants = address_variants(ADDRESS)
    assert variants == [ADDRESS, "10 kiệt 82 Đào Duy Anh, Phú Xuân, Thành phố Huế"]
    assert len(address_variants("10/82/3 Đào Duy Anh, Huế")) == 1


def test_exact_address_uses_google_geocoding_and_stores_expiry(monkeypatch):
    get = Mock(return_value=response({"status": "OK", "results": [geocode_candidate()]}))
    monkeypatch.setattr(requests, "get", get)
    result = GoogleGeocoder(api_key="test-server-key").resolve_address(ADDRESS)
    assert result["status"] == "located" and result["method"] == "geocoding"
    assert result["coordinate"]["coordinates"] == [107.57, 16.47]
    assert result["precision"] == "ROOFTOP"
    assert datetime.fromisoformat(result["expires_at"]) < datetime.now(timezone.utc) + timedelta(days=30)
    assert get.call_args.kwargs["params"]["components"] == "country:VN"
    assert "test-server-key" not in str(result)


def test_zero_results_falls_back_to_places_text_search(monkeypatch):
    monkeypatch.setattr(requests, "get", Mock(return_value=response({"status": "ZERO_RESULTS", "results": []})))
    post = Mock(return_value=response({"places": [place_candidate()]}))
    monkeypatch.setattr(requests, "post", post)
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["status"] == "located" and result["method"] == "places_text_search"
    assert result["precision"] == "PLACE_MATCH"
    assert post.call_args.kwargs["json"]["textQuery"] == ADDRESS
    assert "places.location" in post.call_args.kwargs["headers"]["X-Goog-FieldMask"]


def test_wrong_region_is_rejected_before_fallback_accepts_correct_place(monkeypatch):
    wrong = geocode_candidate(formatted_address="10 kiệt 82 Đào Duy Anh, Gia Lai, Việt Nam")
    monkeypatch.setattr(requests, "get", Mock(return_value=response({"status": "OK", "results": [wrong]})))
    monkeypatch.setattr(requests, "post", Mock(return_value=response({"places": [place_candidate()]})))
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["method"] == "places_text_search"
    assert result["attempts"][0]["reasons"] == ["wrong_region"]


def test_variants_are_only_tried_after_original_address_methods(monkeypatch):
    get = Mock(side_effect=[response({"status": "ZERO_RESULTS"}), response({"status": "OK", "results": [geocode_candidate()]})])
    monkeypatch.setattr(requests, "get", get)
    post = Mock(return_value=response({"places": []}))
    monkeypatch.setattr(requests, "post", post)
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["status"] == "located" and get.call_count == 2 and post.call_count == 1
    assert get.call_args.kwargs["params"]["address"].startswith("10 kiệt 82")


@pytest.mark.parametrize("status,error", [("REQUEST_DENIED", "request_denied"), ("OVER_QUERY_LIMIT", "quota_exceeded"), ("UNKNOWN_ERROR", "provider_unavailable")])
def test_provider_errors_are_explicit_without_trying_more_paid_calls(monkeypatch, status, error):
    get = Mock(return_value=response({"status": status, "error_message": "contains sensitive provider details"}))
    monkeypatch.setattr(requests, "get", get)
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["status"] == "provider_error" and result["error_code"] == error
    assert "sensitive provider details" not in str(result)
    assert get.call_count == 1


def test_timed_out_provider_is_not_mislabeled_as_unknown_address(monkeypatch):
    monkeypatch.setattr(requests, "get", Mock(side_effect=requests.Timeout()))
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["status"] == "provider_error"


@pytest.mark.parametrize("candidate", [
    geocode_candidate(types=["route"]),
    geocode_candidate(partial_match=True),
])
def test_street_center_and_partial_match_need_review(monkeypatch, candidate):
    monkeypatch.setattr(requests, "get", Mock(return_value=response({"status": "OK", "results": [candidate]})))
    monkeypatch.setattr(requests, "post", Mock(return_value=response({"places": []})))
    result = GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)
    assert result["status"] == "needs_review"
    assert "coordinate" not in result


def test_house_number_mismatch_is_not_accepted(monkeypatch):
    candidate = geocode_candidate(formatted_address="11 kiệt 82 Đào Duy Anh, Phú Xuân, Huế, Việt Nam")
    monkeypatch.setattr(requests, "get", Mock(return_value=response({"status": "OK", "results": [candidate]})))
    monkeypatch.setattr(requests, "post", Mock(return_value=response({"places": []})))
    assert GoogleGeocoder(api_key="test-key").resolve_address(ADDRESS)["status"] == "no_match"


def test_missing_address_and_missing_province_are_explicit():
    assert GoogleGeocoder(api_key="test-key").resolve_address(None)["status"] == "missing_address"
    assert GoogleGeocoder(api_key="test-key").resolve_address("10/82 Đào Duy Anh")["status"] == "insufficient_address"
