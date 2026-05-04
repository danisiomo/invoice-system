import uuid
from datetime import datetime
from pydantic import BaseModel

class UserShort(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str

    class Config:
        from_attributes = True

class ResponsibleCreate(BaseModel):
    user_id: uuid.UUID
    department: str | None = None
    regional_center_id: uuid.UUID

class ResponsibleUpdate(BaseModel):
    user_id: uuid.UUID | None = None
    department: str | None = None
    regional_center_id: uuid.UUID | None = None

class ResponsibleResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user: UserShort
    department: str | None
    regional_center_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ResponsibleListResponse(BaseModel):
    items: list[ResponsibleResponse]
    total: int
    page: int
    page_size: int
    pages: int