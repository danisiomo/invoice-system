import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from app.models.transaction import TransactionType, TransactionStatus


class TransactionCreate(BaseModel):
    external_id: str
    transaction_date: date
    transaction_type: TransactionType
    amount: Decimal
    contract_number: str | None = None
    service_code: str | None = None
    service_name: str | None = None
    vat_rate: Decimal | None = None
    link_key: str
    country_code: str | None = None
    income_account_id: uuid.UUID | None = None
    vat_account_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    counterparty_id: uuid.UUID | None = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    transaction_date: date
    transaction_type: TransactionType
    status: TransactionStatus
    amount: Decimal
    contract_number: str | None
    service_code: str | None
    service_name: str | None
    vat_rate: Decimal | None
    link_key: str
    country_code: str | None
    income_account_id: uuid.UUID | None
    vat_account_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    counterparty_id: uuid.UUID | None
    invoice_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TransactionBatchCreate(BaseModel):
    """Создание пачки проводок за раз"""
    transactions: list[TransactionCreate]


class TransactionBatchResponse(BaseModel):
    """Результат создания пачки"""
    created: int
    skipped: int      # уже существующие по external_id
    errors: int
    total: int