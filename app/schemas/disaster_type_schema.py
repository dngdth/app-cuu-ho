from pydantic import BaseModel, ConfigDict

class DisasterTypeBase(BaseModel):
    name: str
    description: str | None = None

class DisasterTypeCreate(DisasterTypeBase):
    pass

class DisasterTypeUpdate(DisasterTypeBase):
    pass

class DisasterTypeOut(DisasterTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
        
class DisasterTypeResponse(DisasterTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
