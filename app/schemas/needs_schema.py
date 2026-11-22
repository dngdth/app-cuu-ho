from pydantic import BaseModel, ConfigDict

class NeedsBase(BaseModel):
    name: str
    description: str | None = None

class NeedsCreate(NeedsBase):
    pass

class NeedsUpdate(NeedsBase):
    pass

class NeedsOut(NeedsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
        
class NeedsResponse(NeedsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
