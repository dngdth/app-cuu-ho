from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from app.dependencies import get_db
from app.services.geocode_service import GeocodeService
from app.services.google_maps_service import GoogleMapsService, maps_url
from app.services.geoapify_service import ProviderError
from app.services.provider_store import ProviderLimit, usage_summary
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/geocode", tags=["location"])
geocode_service = GeocodeService()


@router.get("/status")
def geocode_status():
    ready = geocode_service.configured and geocode_service.enabled
    return {"provider": "geoapify", "configured": ready, "key_configured": geocode_service.configured,
            "enabled": geocode_service.enabled, "methods": ["geoapify_geocoding"],
            "message": "Sẵn sàng định vị bằng Geoapify." if ready else
                "Bổ sung GEOAPIFY_API_KEY và bật GEOCODING_ENABLED để tìm địa chỉ. Bản đồ OpenStreetMap không cần key."}


@router.get("/usage")
def usage(db: Session = Depends(get_db)):
    return usage_summary(db)


class MapsLinkInput(BaseModel):
    url: str = Field(min_length=1, max_length=8192)


@router.post("/resolve-link")
def resolve_maps_link(data: MapsLinkInput):
    if not maps_url(data.url):
        raise HTTPException(422, "Cần một link Google Maps hợp lệ.")
    result = GoogleMapsService.resolve(data.url)
    if result is None:
        raise HTTPException(404, "Chưa lấy được tọa độ đích từ link này; hãy bổ sung địa chỉ hoặc tọa độ.")
    return result


@router.get("/forward")
def geocode_forward(address: str = Query(..., min_length=3, max_length=2000)):
    result = geocode_service.resolve_address(address)
    if result["status"] != "located":
        code = {"needs_api_key": 503, "disabled": 503, "quota_exceeded": 429, "provider_error": 502,
                "missing_address": 422, "insufficient_address": 422}.get(result["status"], 404)
        raise HTTPException(code, result)
    return {**result["coordinate"], "address": result["formatted_address"],
            "geocoding": {key: value for key, value in result.items() if key != "coordinate"}}


class RouteInput(BaseModel):
    start: dict
    end: dict
    mode: Literal["drive", "walk", "bicycle"] = "drive"

    @field_validator("start", "end")
    @classmethod
    def point(cls, value):
        return ProcessingService.valid_coordinate(value)


@router.post("/route")
def route(data: RouteInput):
    if not geocode_service.configured or not geocode_service.enabled:
        raise HTTPException(503, "Cần cấu hình Geoapify để tìm đường. Không cần Google Cloud Billing.")
    try:
        return geocode_service.route(data.start["coordinates"], data.end["coordinates"], data.mode)
    except ProviderLimit as exc:
        raise HTTPException(429, "Đã đạt giới hạn lượt tìm đường của ứng dụng.") from exc
    except ProviderError as exc:
        raise HTTPException(502, "Chưa tìm được đường đi; kiểm tra kết nối, key và vị trí.") from exc
