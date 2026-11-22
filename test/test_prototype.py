"""Provider, account, quota and durable-queue integration in rollback-only schemas."""
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import copy
import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core import config
from app.core.security import AccessMiddleware, hash_password
from app.dependencies import get_db
from app.models import RescueRequest
from app.models.operations_model import User, ApiCounter, ProcessingJob, UserSession
from app.routers import auth_router, jobs_router, processing_router, rescue_request_router, operations_router, geocode_router
from app.services.geoapify_service import GeoapifyService
from app.services.provider_store import ProviderLimit, ProviderStore
from app.services.job_service import enqueue, claim, run_step, fail_job, utcnow
from app.services.processing_service import ProcessingService
from ai.extraction import extract_post
from test.test_processing import db, record  # noqa: F401

ADDRESS = "10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế"


class MemoryStore:
    def __init__(self):
        self.cache, self.used = {}, 0
    def cached(self, key):
        return self.cache.get(key)
    def reserve(self, service):
        self.used += 1
    def remember(self, key, payload, seconds=0):
        self.cache[key] = payload


def candidate(**changes):
    return {"formatted": "10 kiệt 82 Đào Duy Anh, Phú Xuân, Huế, Việt Nam", "country_code": "vn",
            "result_type": "building", "lon": 107.57, "lat": 16.47, "place_id": "example-place",
            "rank": {"confidence": 0.95}, **changes}


@pytest.fixture(autouse=True)
def network_guard(monkeypatch):
    monkeypatch.setattr(config, "GEOCODING_ENABLED", True)
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected real provider call")
    monkeypatch.setattr(requests, "get", forbidden)
    monkeypatch.setattr(requests, "post", forbidden)


def test_geoapify_exact_match_and_cache(monkeypatch):
    store = MemoryStore()
    get = Mock(return_value=Mock(status_code=200, json=lambda: {"results": [candidate()]}))
    monkeypatch.setattr(requests, "get", get)
    service = GeoapifyService(api_key="private-test-key", store=store)
    first, second = service.resolve_address(ADDRESS), service.resolve_address(ADDRESS)
    assert first["coordinate"]["coordinates"] == [107.57, 16.47]
    assert first["provider"] == "geoapify" and second["cached"] is True
    assert get.call_count == store.used == 1
    assert "private-test-key" not in str(first)


@pytest.mark.parametrize("change", [{"country_code": "us"}, {"result_type": "street"},
    {"formatted": "10 Đào Duy Anh, Đà Nẵng"}, {"rank": {"confidence": 0.5}}, {"lat": 200}])
def test_geoapify_rejects_wrong_or_coarse_point(monkeypatch, change):
    monkeypatch.setattr(requests, "get", Mock(return_value=Mock(status_code=200, json=lambda: {"results": [candidate(**change)]})))
    result = GeoapifyService(api_key="test-key", store=MemoryStore()).resolve_address(ADDRESS)
    assert result["status"] in ("needs_review", "no_match") and "coordinate" not in result
    assert len(result["attempts"]) <= 2


def test_missing_key_disabled_quota_and_store_failure_do_not_call_http(monkeypatch):
    assert GeoapifyService(api_key="", store=MemoryStore()).resolve_address(ADDRESS)["status"] == "needs_api_key"
    monkeypatch.setattr(config, "GEOCODING_ENABLED", False)
    assert GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(ADDRESS)["status"] == "disabled"
    monkeypatch.setattr(config, "GEOCODING_ENABLED", True)
    store = MemoryStore()
    store.reserve = Mock(side_effect=ProviderLimit("local_quota_exceeded"))
    assert GeoapifyService(api_key="test", store=store).resolve_address(ADDRESS)["status"] == "quota_exceeded"
    store.cached = Mock(side_effect=RuntimeError("db is down"))
    assert GeoapifyService(api_key="test", store=store).resolve_address(ADDRESS)["error_code"] == "quota_store_unavailable"


def test_geoapify_429_stops_without_fallback(monkeypatch):
    get = Mock(return_value=Mock(status_code=429))
    monkeypatch.setattr(requests, "get", get)
    result = GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(ADDRESS)
    assert result["error_code"] == "provider_quota_exceeded" and get.call_count == 1


@pytest.mark.parametrize("address,house,street", [
    (ADDRESS, "10/82", "Đào Duy Anh"),
    ("nhà số 9 kiệt 34 An Ninh, phường Kim Long, thành phố Huế", "9/34", "An Ninh"),
    ("10 kiệt 82 Đào Duy Anh, Thừa Thiên Huế", "10/82", "Đào Duy Anh"),
])
def test_structured_vietnamese_address_preserves_house_and_alley(address, house, street):
    from app.services.address_matching import structured_address
    assert structured_address(address) == {"housenumber": house, "street": street, "city": "Huế"}
    assert structured_address("9/34 An Ninh, Kim Long") is None


@pytest.mark.parametrize("address,house,street,other_street", [
    (ADDRESS, "10/82", "Đào Duy Anh", "Kiệt 227 Đào Duy Anh"),
    ("nhà số 9 kiệt 34 An Ninh, phường Kim Long, thành phố Huế", "9/34", "An Ninh", "Nguyễn An Ninh"),
])
def test_structured_fallback_exposes_street_suggestion_without_claiming_a_house(monkeypatch, address, house, street, other_street):
    approximate = candidate(formatted=f"{house}, {street}, Huế", housenumber=house, street=street,
        city="Huế", state="Thừa Thiên Huế", rank={"confidence": 0.5,
        "confidence_city_level": 1, "confidence_street_level": 1, "confidence_building_level": 0})
    unrelated_street = {**approximate, "street": other_street, "formatted": f"{house}, {other_street}, Huế"}
    get = Mock(side_effect=[Mock(status_code=200, json=lambda: {"results": []}),
                           Mock(status_code=200, json=lambda: {"results": [approximate, unrelated_street]})])
    monkeypatch.setattr(requests, "get", get)
    result = GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(address)
    assert result["status"] == "needs_review" and "coordinate" not in result
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["precision"] == "STREET"
    assert result["suggestions"][0]["requires_confirmation"] is True
    assert house not in result["suggestions"][0]["formatted_address"]
    assert result["expires_at"] and get.call_count == 2
    params = get.call_args.kwargs["params"]
    assert params["housenumber"] == house and params["city"] == "Huế" and "text" not in params


def test_geoapify_checks_structured_region_and_house_number_order(monkeypatch):
    response = candidate(formatted="10/82, Đào Duy Anh, TT, Việt Nam", city="Huế", state="Thừa Thiên Huế",
                         housenumber="10/82", street="Đào Duy Anh")
    monkeypatch.setattr(requests, "get", Mock(return_value=Mock(status_code=200, json=lambda: {"results": [response]})))
    assert GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(ADDRESS)["status"] == "located"
    response["housenumber"] = "82/10"
    assert GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(ADDRESS)["status"] == "needs_review"
    response["housenumber"] = "10/82"
    response["rank"]["confidence_building_level"] = 0
    assert GeoapifyService(api_key="test", store=MemoryStore()).resolve_address(ADDRESS)["status"] == "needs_review"


def test_route_preserves_geojson_and_has_disaster_warning(monkeypatch):
    geometry = {"type": "MultiLineString", "coordinates": [[[107.5, 16.4], [107.6, 16.5]]]}
    get = Mock(return_value=Mock(status_code=200, json=lambda: {"features": [{"geometry": geometry, "properties": {"distance": 1500, "time": 120}}]}))
    monkeypatch.setattr(requests, "get", get)
    result = GeoapifyService(api_key="test", store=MemoryStore()).route([107.5, 16.4], [107.6, 16.5])
    assert result["geometry"] == geometry and result["distance_m"] == 1500
    assert "ngập lụt" in result["warning"]
    assert get.call_args.kwargs["params"]["waypoints"] == "16.4,107.5|16.5,107.6"


def test_durable_daily_monthly_reservations_and_restart(db, monkeypatch):
    monkeypatch.setattr(config, "GEOCODING_DAILY_LIMIT", 1)
    monkeypatch.setattr(config, "GEOCODING_MONTHLY_LIMIT", 3)
    store = ProviderStore(session_factory=lambda: nullcontext(db))
    store.reserve("geocoding")
    with pytest.raises(ProviderLimit, match="quota"):
        ProviderStore(session_factory=lambda: nullcontext(db)).reserve("geocoding")
    db.rollback()
    rows = db.query(ApiCounter).filter(ApiCounter.service == "geocoding").all()
    assert len(rows) == 2 and all(row.count == 1 for row in rows)
    monkeypatch.setattr(config, "GEOCODING_DAILY_LIMIT", 20)
    monkeypatch.setattr(config, "GEOCODING_MONTHLY_LIMIT", 1)
    with pytest.raises(ProviderLimit, match="quota"):
        store.reserve("geocoding")
    db.rollback()
    assert all(row.count == 1 for row in db.query(ApiCounter).filter(ApiCounter.service == "geocoding"))


@pytest.fixture
def accounts(db):
    encoded = hash_password("test-password-12345")
    users = [User(email=f"{role}@example.test", name=role, password_hash=encoded, role=role) for role in ("admin", "operator", "viewer")]
    db.add_all(users); db.commit()
    return {user.role: user for user in users}


@pytest.fixture
def secure_client(db, accounts):
    app = FastAPI()
    for module in (auth_router, jobs_router, processing_router, rescue_request_router, operations_router, geocode_router):
        app.include_router(module.router)
    app.add_middleware(AccessMiddleware, session_factory=lambda: nullcontext(db))
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client


def login(client, role="operator"):
    response = client.post("/auth/login", json={"email": f"{role}@example.test", "password": "test-password-12345"})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response


def test_session_cookie_csrf_roles_and_logout(secure_client):
    client = secure_client
    assert client.post("/processing/import", json={"records": [record()]}).status_code == 401
    response = login(client)
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/auth/me").json()["user"]["role"] == "operator"
    assert client.post("/processing/import", json={"records": [record()]}, headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.post("/processing/import", json={"records": [record()]}, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get("/auth/users").status_code == 403
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").json()["user"] is None
    login(client, "viewer")
    assert client.post("/processing/import", json={"records": [record()]}).status_code == 403


def test_verified_actor_overrides_client_actor(secure_client):
    client = secure_client
    login(client)
    response = client.post("/rescue_request/", json=record())
    assert response.status_code == 201, response.text
    id_ = response.json()["id"]
    updated = client.patch(f"/operations/requests/{id_}/review", json={"status": "pending", "note": "Đã liên hệ xác minh", "actor": "Forged admin"})
    assert updated.status_code == 200, updated.text
    events = client.get(f"/operations/requests/{id_}/events").json()
    assert events[0]["actor"] == "operator (operator@example.test)"


def test_admin_can_create_and_revoke_account(secure_client):
    client = secure_client
    login(client, "admin")
    response = client.post("/auth/users", json={"email": "new@example.test", "name": "New", "password": "long-test-password", "role": "viewer"})
    assert response.status_code == 201, response.text
    assert "password" not in str(response.json())
    assert client.patch(f"/auth/users/{response.json()['id']}/access", json={"active": False}).json()["active"] is False


def test_job_atomic_progress_dedup_and_recovery(db, accounts):
    job = enqueue(db, "import", {"records": [record("Unique queue post"), record("Unique queue post")], "geocode": False}, accounts["operator"].id)
    assert claim(db, "worker-1") == job.id
    assert claim(db, "worker-2") is None
    assert run_step(db, job.id, "worker-1")
    assert db.query(RescueRequest).count() == 1 and db.get(ProcessingJob, job.id).progress == 1
    assert run_step(db, job.id, "worker-1")
    assert run_step(db, job.id, "worker-1") is False
    db.refresh(job)
    assert job.status == "completed" and job.report["created"] == job.report["duplicates"] == 1
    assert job.payload == {}


def test_geocoding_job_keeps_street_suggestion_separate_from_saved_coordinates(db, accounts, monkeypatch):
    from app.models.prediction_model import RescuePrediction

    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", "test")
    item = RescueRequest(title="Street review", location=ADDRESS)
    db.add(item); db.flush()
    db.add(RescuePrediction(rescue_request_id=item.id, details={
        "geocoding": {"message": "Old location warning"}, "warnings": ["Old location warning", "Keep source warning"]}))
    db.commit()
    suggestion = {"precision": "STREET", "coordinate": {"type": "Point", "coordinates": [107.57, 16.47]}}
    monkeypatch.setattr("app.services.geocode_maintenance.resolve_location", lambda *args: {
        "coordinate": None, "coordinate_source": None, "geocoding": {
            "status": "needs_review", "suggestions": [suggestion], "message": "Review street"},
        "warnings": ["Review street"]})
    job = enqueue(db, "geocode", {"ids": [item.id]}, accounts["operator"].id)
    assert claim(db, "review-worker") == job.id
    assert run_step(db, job.id, "review-worker")
    db.refresh(item); db.refresh(job)
    assert item.coordinate is None
    assert item.prediction["geocoding"]["suggestions"] == [suggestion]
    assert item.prediction["warnings"] == ["Keep source warning", "Review street"]
    assert job.report["located"] == 0 and job.report["unlocated"] == job.report["suggested"] == 1


def test_geocoding_queue_limits_region_and_prioritizes_unattempted(db, secure_client, monkeypatch):
    from app.models.region_model import Region
    from app.models.prediction_model import RescuePrediction
    from sqlalchemy import func

    monkeypatch.setattr(config, "GEOAPIFY_API_KEY", "test-key")
    hue, other = Region(name="Huế"), Region(name="Hà Nội")
    db.add_all([hue, other]); db.flush()
    wrong_region = RescueRequest(title="Other region", region_id=other.id)
    attempted = RescueRequest(title="Previously attempted", region_id=hue.id)
    located = RescueRequest(title="Already located", region_id=hue.id,
                            coordinate=func.ST_SetSRID(func.ST_MakePoint(107.58, 16.46), 4326))
    db.add_all([wrong_region, attempted, located]); db.flush()
    db.add(RescuePrediction(rescue_request_id=attempted.id, details={
        "geocoding": {"status": "no_match", "attempted_at": "2026-01-01T00:00:00+00:00"}}))
    fresh = [RescueRequest(title=f"Fresh Hue {index}", region_id=hue.id) for index in range(25)]
    db.add_all(fresh); db.commit()
    login(secure_client)
    response = secure_client.post("/jobs/geocode", json={"region_id": hue.id, "limit": 20})
    assert response.status_code == 202, response.text
    job = db.get(ProcessingJob, response.json()["id"])
    assert job.total == 20 and job.payload["ids"] == [item.id for item in fresh[:20]]
    for item in fresh[:20]:
        db.add(RescuePrediction(rescue_request_id=item.id, details={
            "geocoding": {"attempted_at": "2026-02-01T00:00:00+00:00"}}))
    db.commit()
    second = secure_client.post("/jobs/geocode", json={"region_id": hue.id, "limit": 6})
    assert second.status_code == 202, second.text
    assert db.get(ProcessingJob, second.json()["id"]).payload["ids"] == [item.id for item in fresh[20:]] + [attempted.id]
    assert secure_client.post("/jobs/geocode", json={"region_id": hue.id, "ids": [wrong_region.id]}).status_code == 404
    assert secure_client.post("/jobs/geocode", json={"region_id": 0}).status_code == 422


def test_job_failure_rolls_back_record_and_keeps_cursor(db, accounts, monkeypatch):
    job = enqueue(db, "import", {"records": [record()], "geocode": False}, accounts["operator"].id)
    claim(db, "worker")
    def fail(db, *args, **kwargs):
        db.add(RescueRequest(title="must roll back")); db.flush()
        raise RuntimeError("model unavailable")
    monkeypatch.setattr(ProcessingService, "process", fail)
    with pytest.raises(RuntimeError):
        run_step(db, job.id, "worker")
    db.rollback()
    fail_job(db, job.id, "worker")
    assert db.query(RescueRequest).count() == 0
    saved = db.get(ProcessingJob, job.id)
    assert saved.progress == 0 and saved.status == "queued"
    saved.status, saved.lease_until = "running", utcnow() - timedelta(seconds=1)
    db.commit()
    assert claim(db, "replacement") == saved.id


def test_extraction_preserves_explicit_address_and_does_not_invent_people():
    text = "Mẹ lớn tuổi, cần cứu hộ. Địa chỉ: 10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế"
    row = extract_post(text)
    assert row["location"] == ADDRESS and row["affected_people"] is None
    assert row["extraction_review_required"] is True and row["content"] == text
    assert extract_post("Có 3 người đang chờ cứu hộ")["affected_people"] == 3
    assert extract_post("Nhờ hỗ trợ gia đình em")["location"] is None


def test_missing_structured_address_is_recovered_from_original_text():
    from ai.features import normalize_record
    from app.schemas.rescue_request_schema import RescueRequestOut
    text = "Cần hỗ trợ. Địa chỉ: " + ADDRESS
    row = normalize_record({"content": text, "location": None})
    assert row["location"] == ADDRESS and row["location_extracted"] is True
    response = RescueRequestOut(id=1, title="Source", content=text, location=None)
    assert response.location == ADDRESS and response.location_inferred is True
    manual = normalize_record({"content": text, "location": "Địa chỉ do người dùng sửa, Huế"})
    assert manual["location"] == "Địa chỉ do người dùng sửa, Huế"
