"""Exercise review transactions in isolated PostgreSQL schemas, never public data."""
import copy
import pytest
from test.test_processing import db, client, record  # noqa: F401
from app.models import RescueRequest, Region
from app.models.request_event_model import RequestEvent
from app.services.processing_service import ProcessingService
from app.services.region_catalog import ensure_catalog, find_region
from app.services.geocode_service import GeocodeService


def create(db):
    result = ProcessingService.process(db, [record()], geocode=False)
    return result["results"][0]["id"]


def test_manual_coordinate_is_saved_and_does_not_run_ai(db, client, monkeypatch):
    id_ = create(db)
    before = copy.deepcopy(db.get(RescueRequest, id_).prediction)
    monkeypatch.setattr("ai.inference.EnsemblePredictor.predict", lambda *a: pytest.fail("Coordinate edit must not run AI"))
    response = client.patch(f"/operations/requests/{id_}/review", json={
        "coordinate": {"type": "Point", "coordinates": [107.6, 16.5]}, "note": "Đã kiểm tra vị trí", "actor": "Dũng"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["coordinate"]["coordinates"] == pytest.approx([107.6, 16.5])
    assert result["prediction"]["models"] == before["models"]
    assert result["prediction"]["geocoding"]["provider"] == "manual"
    history = client.get(f"/operations/requests/{id_}/events").json()
    assert len(history) == 1 and history[0]["actor"] == "Dũng"
    assert history[0]["changes"]["coordinate"]["source"] == "manual"
    assert "107.6" not in str(history)


def test_manual_location_removes_stale_geocoding_warning(db, client):
    id_ = create(db)
    item = db.get(RescueRequest, id_)
    item.prediction_result.details = {**item.prediction, "warnings": ["Old location warning", "Keep source warning"],
        "geocoding": {"status": "needs_review", "message": "Old location warning"}}
    db.commit()
    response = client.patch(f"/operations/requests/{id_}/review", json={
        "coordinate": {"coordinates": [107.6, 16.5]}, "note": "Đã đối chiếu tọa độ"})
    assert response.status_code == 200, response.text
    assert response.json()["prediction"]["warnings"] == ["Keep source warning"]


def test_cost_switch_stops_batch_before_database_changes(db, client, monkeypatch):
    id_ = create(db)
    before = copy.deepcopy(db.get(RescueRequest, id_).prediction)
    monkeypatch.setattr(GeocodeService, "configured", property(lambda self: True))
    monkeypatch.setattr(GeocodeService, "enabled", property(lambda self: False))
    monkeypatch.setattr("app.services.geocode_maintenance.resolve_location", lambda *a: pytest.fail("Disabled batch must not resolve locations"))
    result = client.post("/processing/geocode-pending", json={"limit": 20}).json()
    assert result["status"] == "disabled" and result["checked"] == 0
    assert db.get(RescueRequest, id_).prediction == before
    status = client.get("/geocode/status").json()
    assert status["key_configured"] is True and status["configured"] is False and status["enabled"] is False


def test_lifecycle_requires_note_and_enforces_transitions(db, client):
    id_ = create(db)
    url = f"/operations/requests/{id_}/review"
    assert client.patch(url, json={"status": "pending"}).status_code == 422
    assert client.patch(url, json={"status": "resolved", "note": "Bỏ qua xác minh"}).status_code == 422
    for status in ("pending", "in_progress", "resolved", "pending"):
        response = client.patch(url, json={"status": status, "note": "Đã liên hệ kiểm tra"})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == status
    assert db.query(RequestEvent).count() == 4


def test_address_edit_clears_old_point_and_recalculates_ai(db, client, monkeypatch):
    id_ = create(db)
    ensure_catalog(db)
    db.commit()
    monkeypatch.setattr(GeocodeService, "resolve_address", lambda self, address: {
        "status": "needs_api_key", "provider": "google", "message": "Chờ API"})
    monkeypatch.setattr("app.services.location_service.GoogleMapsService.resolve_record", lambda *a: None)
    response = client.put(f"/rescue_request/{id_}", json={"location": "10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế",
        "affected_people": 8, "note": "Đối chiếu địa chỉ trong bài gốc"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["coordinate"] is None and result["map_link"] is None
    assert result["location"].startswith("10/82") and result["region_id"] is not None
    assert result["prediction"]["geocoding"]["status"] == "needs_api_key"
    assert len(result["prediction"]["models"]) == 3
    assert client.get(f"/operations/requests/{id_}/events").json()[0]["changes"]["ai"]["recalculated"]


def test_bad_catalog_and_model_failure_roll_back_everything(db, client, monkeypatch):
    id_ = create(db)
    url = f"/operations/requests/{id_}/review"
    assert client.patch(url, json={"title": "New title", "needs_ids": [999999], "note": "Kiểm tra danh mục"}).status_code == 422
    assert db.get(RescueRequest, id_).title != "New title"
    def fail(*args):
        raise FileNotFoundError("missing model")
    monkeypatch.setattr("ai.inference.EnsemblePredictor.predict", fail)
    assert client.patch(url, json={"affected_people": 100, "note": "Cập nhật số người"}).status_code == 503
    assert db.get(RescueRequest, id_).affected_people == 4
    assert db.query(RequestEvent).count() == 0


@pytest.mark.parametrize("patch", [
    {"coordinate": {"coordinates": [180, 91]}}, {"coordinate": {"type": "LineString", "coordinates": [1, 2]}},
    {"affected_people": -1}, {"title": "  "}, {"urgency_score": 3}, {"status": "unknown"},
    {"coordinate": {"coordinates": [True, 16]}}, {"note": " a "}])
def test_review_rejects_invalid_data(client, patch):
    assert client.patch("/operations/requests/1/review", json={"note": "Kiểm tra đầu vào", **patch}).status_code == 422


def test_summary_nearby_and_explicit_region_matching(db, client):
    id_ = create(db)
    ensure_catalog(db)
    assert find_region(db, "10/82 Đào Duy Anh, Phú Xuân, Thành phố Huế") is not None
    assert find_region(db, "Không rõ địa điểm") is None
    assert find_region(db, "Hà Nội hoặc Huế") is None
    summary = client.get("/operations/summary").json()
    assert summary["total"] == summary["located"] == summary["statuses"]["unverified"] == 1
    result = client.get("/rescue_request/nearby/search?longitude=107.58&latitude=16.46&radius_km=1&limit=3")
    assert result.status_code == 200, result.text
    assert [row["id"] for row in result.json()] == [id_]
