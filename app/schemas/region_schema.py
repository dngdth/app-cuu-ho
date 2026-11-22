from pydantic import BaseModel, ConfigDict

class RegionBase(BaseModel):
    name: str
    parent_id: int | None = None

class RegionCreate(RegionBase):
    pass

class RegionUpdate(RegionBase):
    pass

class RegionOut(RegionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class RegionResponse(RegionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)