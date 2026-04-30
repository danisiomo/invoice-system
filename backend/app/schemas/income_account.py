import uuid
from datetime import datetime

from pydantic import BaseModel


class IncomeAccountCreate(BaseModel):
    account_number: str
    name: str
    regional_center_id: uuid.UUID
    branch_id: uuid.UUID


class IncomeAccountUpdate(BaseModel):
    account_number: str | None = None
    name: str | None = None
    regional_center_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class IncomeAccountResponse(BaseModel):
    id: uuid.UUID
    account_number: str
    name: str
    regional_center_id: uuid.UUID
    branch_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class IncomeAccountListResponse(BaseModel):
    items: list[IncomeAccountResponse]
    total: int
    page: int
    page_size: int
    pages: int