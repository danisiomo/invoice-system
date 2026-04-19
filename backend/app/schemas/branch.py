import uuid
from datetime import datetime

from pydantic import BaseModel


class BranchCreate(BaseModel):
    code: str
    name: str
    address: str | None = None
    inn: str | None = None
    kpp: str | None = None
    regional_center_id: uuid.UUID


class BranchResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    address: str | None
    inn: str | None
    kpp: str | None
    regional_center_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True