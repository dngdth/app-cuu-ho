"""Real model and PostgreSQL integration checks; all DB changes are rolled back."""
import csv
import io
import os
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ai.features import normalize_record, prepare_features
from ai.inference import EnsemblePredictor
from app.core.config import DATABASE_URL
from app.db.database import Base
from app.dependencies import get_db
from app.models.prediction_model import RescuePrediction
from app.models.rescue_request_model import RescueRequest
from app.routers import processing_router, rescue_request_router, geocode_router, operations_router
from app.services.processing_service import ProcessingService, posted_datetime
from app.services.transform_service import TransformService
from app.services.geocode_service import GeocodeService

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def samples():
    with (ROOT / "crawl/data_clean.csv").open(encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    return [rows[0], rows[1], rows[3], rows[-3]]


@pytest.fixture
def db():
    engine = create_engine(os.getenv("TEST_DATABASE_URL") or DATABASE_URL)
    with engine.connect() as connection:
        transaction = connection.begin()
        schema = "pipeline_test_" + uuid.uuid4().hex
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
        connection = connection.execution_options(schema_translate_map={None: schema})
        Base.metadata.create_all(connection)
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
    engine.dispose()


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(processing_router.router)
    app.include_router(rescue_request_router.router)
    app.include_router(geocode_router.router)
    app.include_router(operations_router.router)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client


def record(content="Test rescue", **kwargs):
    return {"content": content, "location": "Huế", "affected_people": 4,
            "disaster_type": ["lũ lụt"], "needs": ["phương tiện & cứu hộ"],
            "is_isolated": True, "deathly": True,
            "coordinate": {"type": "Point", "coordinates": [107.58, 16.46]}, **kwargs}


def test_batch_matches_individual_real_models(samples):
    predictor = EnsemblePredictor()
    batch = predictor.predict(samples)
    singles = [predictor.predict([row])[0] for row in samples]
    for combined, single in zip(batch, singles, strict=True):
        assert combined["urgency_label"] == single["urgency_label"]
        assert combined["urgency_probability"] == pytest.approx(single["urgency_probability"])
        assert combined["reliability_label"] == single["reliability_label"]
        assert set(combined["models"]) == {"gradient_boosting", "random_forest", "lightgbm"}
        if combined["method"] == "highest_probability":
            winner = max(combined["models"].values(), key=lambda item: item["urgency_probability"])
            assert combined["urgency_label"] == winner["urgency_label"]
        else:
            labels = {label for model in combined["models"].values() for label in model["urgency_distribution"]}
            averages = {label: sum(model["urgency_distribution"].get(label, 0) for model in combined["models"].values()) / 3 for label in labels}
            assert combined["urgency_label"] == max(averages, key=averages.get)
            assert combined["urgency_probability"] == pytest.approx(max(averages.values()))
    assert len({item["urgency_probability"] for item in batch}) > 1


def test_input_targets_do_not_leak_into_prediction(samples):
    first = EnsemblePredictor().predict(samples)
    changed = EnsemblePredictor().predict([{**row, "label": "WRONG", "confident": "WRONG",
                                           "urgency_score": 99} for row in samples])
    for before, after in zip(first, changed, strict=True):
        for name in before["models"]:
            for key in ("urgency_label", "reliability_label"):
                assert before["models"][name][key] == after["models"][name][key]
            for key in ("urgency_probability", "reliability_probability"):
                assert before["models"][name][key] == pytest.approx(after["models"][name][key])


def test_normalization_preserves_contacts_and_missing_values():
    row = normalize_record(record(contact="0901234567", affected_people="", is_isolated="FALSE"))
    assert row["contact"] == "0901234567"
    assert row["affected_people"] is None
    assert row["is_isolated"] is False
    binary = normalize_record(record(contact="1", content="Cần cứu hộ"))
    assert binary["contact"] is None
    assert normalize_record(binary)["contact_present"] is True
    features = prepare_features([binary])
    assert features.iloc[0]["contact"] == 1
    assert features.iloc[0]["phương tiện & cứu hộ"] == 1
    assert normalize_record(record(contact="[]"))["contact_present"] is False


def test_dates_need_a_collection_reference():
    assert posted_datetime("4w") is None
    assert posted_datetime("1w", "2025-11-21T12:00:00+00:00") == "2025-11-14T12:00:00+00:00"
    assert posted_datetime("2025-11-01T10:30:00Z") == "2025-11-01T10:30:00+00:00"
    assert TransformService.parse_posted_time("2025-11-01T10:30:00Z").year == 2025


def test_import_atomic_per_row_and_reimport_deduplicated(client, db):
    payload = {"records": [record(posted_time="4w"), record("Invalid", coordinate={"coordinates": [400, 100]}),
                           record("Another valid", coordinate=None, location=None)], "geocode": False}
    response = client.post("/processing/import", json=payload)
    assert response.status_code == 200, response.text
    report = response.json()
    assert (report["created"], report["failed"], report["located"], report["unlocated"]) == (2, 1, 1, 1)
    assert db.query(RescueRequest).count() == db.query(RescuePrediction).count() == 2
    requests = client.get("/rescue_request/").json()
    assert len(requests) == 2
    assert all(item["prediction"]["source"] == "ensemble" for item in requests)
    assert all(item["status"] == "unverified" for item in requests)
    historical = next(item for item in requests if item["content"] == "Test rescue")
    assert historical["posted_time"] is None
    assert historical["prediction"]["original_posted_time"] == "4w"
    assert historical["coordinate"]["coordinates"] == [107.58, 16.46]
    assert historical["needs"] and historical["disaster_types"]
    second = client.post("/processing/import", json={"records": [record(content="  TEST   rescue  ")], "geocode": False}).json()
    assert second["duplicates"] == 1 and second["created"] == 0


def test_create_endpoint_runs_inference(client):
    response = client.post("/rescue_request/", json=record())
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["prediction"]["source"] == "ensemble"
    assert item["urgency_score"] in (1, 2, 3)
    assert len(item["prediction"]["models"]) == 3


def test_csv_upload_quoted_newlines_and_invalid_rows(client, db):
    csv_data = '\ufeffcontent,location,affected_people,is_isolated,posted_time\r\n"Cần cứu,\nnhà ngập",Huế,4,TRUE,1w\r\nInvalid,Huế,abc,FALSE,1w\r\n'
    response = client.post("/processing/import-csv", files={"file": ("source.csv", csv_data.encode(), "text/csv")}, data={"geocode": "false"})
    assert response.status_code == 200, response.text
    assert response.json()["created"] == response.json()["failed"] == 1
    assert db.query(RescueRequest).count() == 1
    malformed = client.post("/processing/read-csv", files={"file": ("bad.csv", b"title\nx\n", "text/csv")})
    assert malformed.status_code == 422


def test_geocoding_uses_geojson_and_saved_prediction(client, monkeypatch):
    monkeypatch.setattr(GeocodeService, "resolve_address", lambda self, location: {
        "status": "located", "provider": "google", "method": "geocoding", "precision": "ROOFTOP",
        "coordinate": {"type": "Point", "coordinates": [108.2, 16.05]}, "message": "Test matched address"})
    response = client.post("/processing/import", json={"records": [record(coordinate=None)]}).json()
    assert response["located"] == 1
    item = client.get(f"/rescue_request/{response['results'][0]['id']}").json()
    assert item["coordinate"]["coordinates"] == [108.2, 16.05]


def test_no_invented_coordinates_and_invalid_boolean(client):
    result = client.post("/processing/import", json={"records": [record(location=None, coordinate=None), record("bad bool", deathly="maybe")], "geocode": False}).json()
    assert result["created"] == result["unlocated"] == result["failed"] == 1
    item = client.get(f"/rescue_request/{result['results'][0]['id']}").json()
    assert item["coordinate"] is None


def test_model_failure_does_not_persist_records(client, db, monkeypatch):
    def unavailable(self, rows):
        raise FileNotFoundError("model missing")
    monkeypatch.setattr(EnsemblePredictor, "predict", unavailable)
    response = client.post("/processing/import", json={"records": [record()]})
    assert response.status_code == 503
    assert db.query(RescueRequest).count() == 0


def test_preview_does_not_write_and_validates_input(client, db):
    preview = client.post("/processing/predict", json={"records": [record(), record("Second")]})
    assert preview.status_code == 200
    assert len(preview.json()) == 2
    assert db.query(RescueRequest).count() == 0
    assert client.post("/processing/predict", json={"records": [{"content": ""}]}).status_code == 422


def test_coordinates_from_google_maps_without_network():
    coordinate = ProcessingService.coordinate_in_text("https://maps.google.com/?q=16.46,107.58", "")
    assert coordinate["coordinates"] == [107.58, 16.46]


def test_geocoder_rejects_cross_province_result(monkeypatch):
    from app.services.google_geocoding import matching_candidate
    candidate = {"formatted_address": "Kim Long, Đồng Nai, Việt Nam", "types": ["street_address"],
                 "address_components": [{"short_name": "VN", "types": ["country"]}]}
    assert matching_candidate("Kim Long, Huế", candidate) == "wrong_region"


def test_failed_database_row_is_rolled_back_before_next_row(client, db, monkeypatch):
    from app.repositories.rescue_request_repository import RescueRequestRepository
    create = RescueRequestRepository.create

    def fail_one(session, data, **kwargs):
        if data.content == "Fail in database":
            session.execute(text("SELECT 1 / 0"))
        return create(session, data, **kwargs)

    monkeypatch.setattr(RescueRequestRepository, "create", fail_one)
    response = client.post("/processing/import", json={"records": [record("First"), record("Fail in database"), record("Last")], "geocode": False})
    assert response.status_code == 200
    assert response.json()["created"] == 2 and response.json()["failed"] == 1
    assert db.query(RescueRequest).count() == db.query(RescuePrediction).count() == 2


def test_short_maps_link_prioritized_over_address_and_existing_rows_can_be_resolved(client, db, monkeypatch):
    from app.services.google_maps_service import GoogleMapsService
    resolved = {"coordinate": {"type": "Point", "coordinates": [105.8231972, 21.6083114]},
                "source_url": "https://maps.app.goo.gl/example", "coordinate_source": "google_maps"}
    monkeypatch.setattr(GoogleMapsService, "resolve", lambda url: resolved)

    def no_geocode(*args):
        raise AssertionError("Do not geocode an address when the Maps link already contains a destination")

    monkeypatch.setattr(GeocodeService, "resolve_address", no_geocode)
    source = record(coordinate=None, location="", content="Rescue: https://maps.app.goo.gl/example")
    imported = client.post("/processing/import", json={"records": [source]}).json()
    assert imported["located"] == 1
    item = client.get(f"/rescue_request/{imported['results'][0]['id']}").json()
    assert item["coordinate"]["coordinates"] == [105.8231972, 21.6083114]
    assert item["prediction"]["coordinate_source"] == "google_maps"
    pending = client.post("/processing/import", json={"records": [{**source, "content": source["content"] + " second"}], "geocode": False}).json()
    assert pending["unlocated"] == 1
    before = db.query(RescueRequest).filter(RescueRequest.id == pending["results"][0]["id"]).one()
    models_before = before.prediction["models"]
    report = ProcessingService.resolve_existing_map_links(db)
    assert report["updated"] == 1
    db.expire_all()
    after = db.query(RescueRequest).filter(RescueRequest.id == before.id).one()
    assert after.prediction["models"] == models_before
    assert after.prediction["location_status"] == "located"
    assert client.post("/geocode/resolve-link", json={"url": "https://maps.app.goo.gl/example"}).status_code == 200


def test_missing_google_key_keeps_ai_result_and_reports_waiting_state(client, db, monkeypatch):
    monkeypatch.setattr(GeocodeService, "configured", property(lambda self: False))
    response = client.post("/processing/import", json={"records": [record(coordinate=None)]})
    assert response.status_code == 200
    item = client.get(f"/rescue_request/{response.json()['results'][0]['id']}").json()
    assert item["coordinate"] is None
    assert item["prediction"]["geocoding"]["status"] == "needs_api_key"
    models = item["prediction"]["models"]
    pending = client.post("/processing/geocode-pending", json={"limit": 20}).json()
    assert pending["status"] == "needs_api_key" and pending["checked"] == 0
    assert db.query(RescueRequest).one().prediction["models"] == models
    assert client.get("/geocode/status").json()["configured"] is False
    assert client.get("/geocode/forward", params={"address": "10 Đào Duy Anh, Huế"}).status_code == 503


def test_pending_geocoding_dry_run_and_save_preserve_ai(client, db, monkeypatch):
    from app.services.geocode_maintenance import geocode_pending
    monkeypatch.setattr(GeocodeService, "configured", property(lambda self: True))
    monkeypatch.setattr(GeocodeService, "enabled", property(lambda self: True))
    imported = client.post("/processing/import", json={"records": [record(coordinate=None)], "geocode": False}).json()
    id_ = imported["results"][0]["id"]
    models = db.query(RescueRequest).one().prediction["models"]
    monkeypatch.setattr(GeocodeService, "resolve_address", lambda *args: {
        "status": "located", "provider": "google", "method": "geocoding", "precision": "ROOFTOP",
        "coordinate": {"type": "Point", "coordinates": [107.57, 16.47]}, "message": "Test geocoded address"})
    def no_prediction(*args):
        raise AssertionError("Geocoding existing data must not rerun models")
    monkeypatch.setattr(EnsemblePredictor, "predict", no_prediction)
    assert geocode_pending(db, ids=[id_], dry_run=True)["updated"] == 1
    assert db.query(RescueRequest).one().coordinate is None
    assert geocode_pending(db, ids=[id_])["updated"] == 1
    db.expire_all()
    assert db.query(RescueRequest).one().prediction["models"] == models
    assert geocode_pending(db, ids=[id_])["checked"] == 0


def test_expired_api_coordinate_is_hidden_and_purged_but_source_address_remains(client, db):
    from datetime import datetime, timedelta, timezone
    from app.services.geocode_maintenance import purge_expired_geocodes
    imported = client.post("/processing/import", json={"records": [record()]}).json()
    item = db.query(RescueRequest).one()
    original_models = item.prediction["models"]
    item.prediction_result.details = {**item.prediction, "coordinate_source": "google_api",
        "geocoding": {"provider": "google", "status": "located", "place_id": "preserved-id",
            "formatted_address": "cached Google address", "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}}
    db.commit()
    read = client.get(f"/rescue_request/{imported['results'][0]['id']}").json()
    assert read["coordinate"] is None and read["map_link"] is None
    assert read["prediction"]["geocoding"]["status"] == "expired"
    assert "formatted_address" not in read["prediction"]["geocoding"]
    assert purge_expired_geocodes(db) == 1
    db.expire_all()
    saved = db.query(RescueRequest).one()
    assert saved.coordinate is None and saved.location == "Huế"
    assert saved.prediction["models"] == original_models
    assert saved.prediction["geocoding"]["place_id"] == "preserved-id"


def test_geocode_pending_moves_to_next_unattempted_request(client, db, monkeypatch):
    from datetime import datetime, timezone
    monkeypatch.setattr(GeocodeService, "configured", property(lambda self: True))
    monkeypatch.setattr(GeocodeService, "enabled", property(lambda self: True))
    client.post("/processing/import", json={"records": [record("First", coordinate=None), record("Second", coordinate=None)], "geocode": False})
    monkeypatch.setattr(GeocodeService, "resolve_address", lambda *args: {
        "provider": "google", "status": "no_match", "attempted_at": datetime.now(timezone.utc).isoformat(), "message": "No match"})
    first = client.post("/processing/geocode-pending", json={"limit": 1}).json()
    second = client.post("/processing/geocode-pending", json={"limit": 1}).json()
    assert first["results"][0]["id"] != second["results"][0]["id"]
    assert client.post("/processing/geocode-pending", json={"ids": []}).status_code == 422
