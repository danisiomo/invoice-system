import uuid
from datetime import datetime, date

from pydantic import BaseModel

from app.models.data_load import DataLoadType, DataLoadStatus, DataLoadPeriod


class DataLoadStandardRequest(BaseModel):
    pass


class DataLoadByDateRequest(BaseModel):
    load_date: date


class DataLoadByAccountRequest(BaseModel):
    account_number: str
    date_from: date


class DataLoadLogResponse(BaseModel):
    id: uuid.UUID
    load_type: DataLoadType
    status: DataLoadStatus
    period_start: date | None
    period_end: date | None
    account_number: str | None
    username: str | None
    records_loaded: int
    error_code: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None

    class Config:
        from_attributes = True


class DataLoadLogListResponse(BaseModel):
    items: list[DataLoadLogResponse]
    total: int
    page: int
    page_size: int
    pages: int