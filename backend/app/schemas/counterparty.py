import uuid
from datetime import datetime
from pydantic import BaseModel


class CounterpartyCreate(BaseModel):
    inn: str
    kpp: str | None = None
    full_name: str
    short_name: str | None = None
    address: str | None = None
    phone: str | None = None
    responsible_id: uuid.UUID | None = None


class CounterpartyUpdate(BaseModel):
    inn: str | None = None
    kpp: str | None = None
    full_name: str | None = None
    short_name: str | None = None
    address: str | None = None
    phone: str | None = None
    responsible_id: uuid.UUID | None = None


class CounterpartyResponse(BaseModel):
    id: uuid.UUID
    inn: str
    kpp: str | None
    full_name: str
    short_name: str | None
    address: str | None
    phone: str | None
    responsible_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CounterpartyListResponse(BaseModel):
    items: list[CounterpartyResponse]
    total: int
    page: int
    page_size: int
    pages: int