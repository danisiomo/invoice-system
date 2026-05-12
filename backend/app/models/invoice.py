import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Numeric, DateTime, Date,
    ForeignKey, Boolean, func, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class InvoiceStatus(str, PyEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SENT = "sent"
    ERROR = "error"

class InvoiceDraftStatus(str, PyEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    invoice_date: Mapped[date] = mapped_column(Date)
    correction_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Статус
    status: Mapped[str] = mapped_column(
        String(50), default="draft"
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="RUB")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_with_vat: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    service_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unit_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    special_sales_book: Mapped[bool] = mapped_column(Boolean, default=False)
    inter_price_difference: Mapped[bool] = mapped_column(Boolean, default=False)

    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counterparties.id"), nullable=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    regional_center_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_centers.id"), nullable=True
    )
    confirmed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    counterparty = relationship("Counterparty")
    branch = relationship("Branch")
    regional_center = relationship("RegionalCenter")
    confirmed_by = relationship("User")
    transactions = relationship("Transaction", back_populates="invoice")

class InvoiceDraft(Base):
    __tablename__ = "invoice_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )