import pytest
import requests

from app.services.google_maps_service import GoogleMapsService, coordinate_from_url, map_links, maps_url


@pytest.fixture(autouse=True)
def reset_cache():
    GoogleMapsService.resolve.cache_clear()
    yield
    GoogleMapsService.resolve.cache_clear()


@pytest.mark.parametrize("url,coordinates", [
    ("https://maps.google.com?q=21.6083114,105.8231972", [105.8231972, 21.6083114]),
    ("https://www.google.com/maps/search/?api=1&query=16.05%2C108.2", [108.2, 16.05]),
    ("https://www.google.com/maps/place/Test/@10,100,8z/data=!3d16.05!4d108.2", [108.2, 16.05]),
    ("https://www.google.com/maps/dir/?api=1&origin=10,100&destination=16.05,108.2", [108.2, 16.05]),
    ("https://www.google.com/maps/place/-33.86,151.2/", [151.2, -33.86]),
])
def test_extract_destination_in_geojson_order(url, coordinates):
    assert coordinate_from_url(url)["coordinates"] == coordinates


@pytest.mark.parametrize("url", [
    "https://www.google.com/maps/@16.05,108.2,15z",
    "https://www.google.com/maps?center=16.05,108.2&map_action=map",
    "https://www.google.com/maps/place/Test/@16.05,108.2,15z/?query_place_id=abc",
    "https://www.google.com/maps?q=91,181",
    "https://www.google.com/maps/dir/?origin=16.05,108.2&destination=Somewhere",
    "https://www.google.com/maps?q=Not+a+specific+point",
    "https://maps.app.goo.gl/opaque?q=16.05,108.2",
    "https://www.google.com/maps/search/?query=16.05,108.2&query_place_id=opaque",
])
def test_do_not_confuse_camera_origin_or_search_text_with_a_pin(url):
    assert coordinate_from_url(url) is None


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8099/health", "https://maps.app.goo.gl.evil.test/link",
    "https://www.google.com.evil.test/maps", "https://user:password@maps.google.com/maps",
    "https://maps.google.com:8443/maps", "https://goo.gl/not-maps",
])
def test_only_known_google_maps_urls_are_allowed(url):
    assert not maps_url(url)


def test_short_link_redirect_and_cache(monkeypatch):
    calls = []

    class Redirect:
        status_code = 302
        headers = {"Location": "https://maps.google.com?q=21.6083114,105.8231972&entry=gps"}
        def close(self):
            pass

    def get(url, **options):
        calls.append(url)
        assert options["allow_redirects"] is False
        return Redirect()

    monkeypatch.setattr(requests, "get", get)
    url = "https://maps.app.goo.gl/atQ1h3QUhhSDZ3tQ8?g_st=ipc"
    result = GoogleMapsService.resolve(url)
    assert result["coordinate"]["coordinates"] == [105.8231972, 21.6083114]
    assert GoogleMapsService.resolve(url) == result
    assert calls == [url]


def test_redirect_to_non_google_host_is_never_requested(monkeypatch):
    calls = []

    class Redirect:
        status_code = 302
        headers = {"Location": "http://127.0.0.1/private"}
        def close(self):
            pass

    monkeypatch.setattr(requests, "get", lambda url, **kwargs: (calls.append(url) or Redirect()))
    assert GoogleMapsService.resolve("https://maps.app.goo.gl/test") is None
    assert len(calls) == 1


def test_timeout_does_not_break_import(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "get", timeout)
    assert GoogleMapsService.resolve("https://maps.app.goo.gl/test") is None


def test_multiple_links_are_found_in_content_without_following_facebook():
    links = list(map_links("Facebook https://facebook.com/example Maps https://maps.app.goo.gl/abc. Next https://goo.gl/maps/def"))
    assert links == ["https://maps.app.goo.gl/abc", "https://goo.gl/maps/def"]
