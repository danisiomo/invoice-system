import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    number: str
    invoice_date: date
    status: str
    currency_code: str
    total_amount: Decimal
    vat_amount: Decimal
    total_with_vat: Decimal
    service_code: str | None
    service_name: str | None
    vat_rate: Decimal | None
    unit_name: str | None
    quantity: Decimal | None
    price: Decimal | None
    country_code: str | None
    special_sales_book: bool
    inter_price_difference: bool
    correction_number: str | None
    payment_document_number: str | None
    sent_at: datetime | None
    payment_date: date | None
    counterparty_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    regional_center_id: uuid.UUID | None
    confirmed_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    id: uuid.UUID
    number: str
    invoice_date: date
    status: str
    total_amount: Decimal
    vat_amount: Decimal
    total_with_vat: Decimal
    service_name: str | None
    counterparty_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceListPaginated(BaseModel):
    items: list[InvoiceListResponse]
    total: int
    page: int
    page_size: int
    pages: int


class InvoiceUpdate(BaseModel):
    #status: str | None = None
    service_name: str | None = None
    service_code: str | None = None
    unit_name: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    vat_rate: Decimal | None = None
    special_sales_book: bool | None = None
    inter_price_difference: bool | None = None
    correction_number: str | None = None
    payment_document_number: str | None = None
    payment_date: date | None = None
    counterparty_id: uuid.UUID | None = None