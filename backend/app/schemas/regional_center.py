import uuid
from datetime import datetime

from pydantic import BaseModel


class RegionalCenterCreate(BaseModel):
    code: str
    name: str


class RegionalCenterResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class RegionalCenterUpdate(BaseModel):
    code: str | None = None
    name: str | None = None