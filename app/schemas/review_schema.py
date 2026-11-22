from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.services.processing_service import ProcessingService


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    actor: str = Field(default="Người kiểm tra", min_length=1, max_length=100)
    note: str = Field(min_length=3, max_length=2000)
    title: str = Field(default="", min_length=1, max_length=500)
    location: str | None = Field(default=None, max_length=2000)
    contact: str | None = Field(default=None, max_length=500)
    map_link: str | None = Field(default=None, max_length=2000)
    coordinate: dict | None = None
    region_id: int | None = Field(default=None, gt=0)
    affected_people: int | None = Field(default=None, ge=0, le=1000000)
    infrastructure_damage: bool = False
    is_isolated: bool = False
    deathly: bool = False
    has_emergency: bool = False
    has_emotion: bool = False
    has_emphasis: bool = False
    needs_ids: list[int] = Field(default_factory=list)
    disaster_type_ids: list[int] = Field(default_factory=list)
    status: Literal["unverified", "pending", "in_progress", "resolved", "rejected"] = "unverified"

    @field_validator("actor", "note", "title")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Không được để trống")
        return value.strip()

    @field_validator("note")
    @classmethod
    def meaningful_note(cls, value):
        if len(value) < 3:
            raise ValueError("Ghi rõ căn cứ kiểm tra hoặc lý do thay đổi")
        return value

    @field_validator("coordinate")
    @classmethod
    def point(cls, value):
        return ProcessingService.valid_coordinate(value) if value is not None else None
