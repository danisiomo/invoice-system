import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import String, Numeric, DateTime, Date, Enum, ForeignKey, Boolean, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class InvoiceDraftStatus(str, PyEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"

class InvoiceStatus(str, PyEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"

class InvoiceDraft(Base):
    """Проект с/ф"""
    __tablename__ = "invoice_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    operation_id: Mapped[str] = mapped_column(
        String(200), index=True,
        comment="Ключ связывания с проводками"
    )
    draft_date: Mapped[date] = mapped_column(
        Date, comment="Дата проводки"
    )

    buyer_name: Mapped[str | None] = mapped_column(String(500))
    buyer_inn: Mapped[str | None] = mapped_column(String(12))
    buyer_kpp: Mapped[str | None] = mapped_column(String(9))
    buyer_address: Mapped[str | None] = mapped_column(Text)

    seller_kpp: Mapped[str | None] = mapped_column(String(9))

    income_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0,
        comment="Сумма комиссии без НДС"
    )
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=20,
        comment="Ставка НДС"
    )
    vat_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0,
        comment="Сумма НДС"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=0,
        comment="Итого с НДС"
    )
    currency_code: Mapped[str] = mapped_column(
        String(3), default="810",
        comment="Код валюты (810=RUB)"
    )
    special_sales_book: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Специальная книга продаж"
    )
    interprice_difference: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Межценовая разница"
    )
    branch_code: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[InvoiceDraftStatus] = mapped_column(
        Enum(InvoiceDraftStatus), default=InvoiceDraftStatus.DRAFT
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Invoice(Base):
    """Оформленная с/ф"""
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True,
        comment="Номер счёта-фактуры"
    )
    invoice_date: Mapped[date] = mapped_column(Date)

    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoice_drafts.id"), nullable=True
    )
    buyer_name: Mapped[str] = mapped_column(String(500))
    buyer_inn: Mapped[str] = mapped_column(String(12))
    buyer_kpp: Mapped[str | None] = mapped_column(String(9))
    buyer_address: Mapped[str | None] = mapped_column(Text)
    seller_kpp: Mapped[str | None] = mapped_column(String(9))
    income_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default="810")
    special_sales_book: Mapped[bool] = mapped_column(Boolean, default=False)
    branch_code: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), default=InvoiceStatus.ACTIVE
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )