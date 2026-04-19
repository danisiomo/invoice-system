import uuid
from datetime import datetime

from pydantic import BaseModel


class VatAccountCreate(BaseModel):
    account_number: str
    name: str
    regional_center_id: uuid.UUID
    branch_id: uuid.UUID


class VatAccountUpdate(BaseModel):
    account_number: str | None = None
    name: str | None = None
    regional_center_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class VatAccountResponse(BaseModel):
    id: uuid.UUID
    account_number: str
    name: str
    regional_center_id: uuid.UUID
    branch_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class VatAccountListResponse(BaseModel):
    items: list[VatAccountResponse]
    total: int
    page: int
    page_size: int
    pages: int