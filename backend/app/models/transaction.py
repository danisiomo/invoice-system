import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Numeric, DateTime, Date,
    ForeignKey, Text, func, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TransactionType(str, PyEnum):
    INCOME = "income"
    VAT = "vat"


class TransactionStatus(str, PyEnum):
    NEW = "new"
    MATCHED = "matched"
    INVOICED = "invoiced"
    ERROR = "error"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    transaction_date: Mapped[date] = mapped_column(Date)

    # VARCHAR вместо native enum
    transaction_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="new")

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    contract_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    service_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    link_key: Mapped[str] = mapped_column(String(200), index=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)

    income_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("income_accounts.id"), nullable=True
    )
    vat_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vat_accounts.id"), nullable=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("counterparties.id"), nullable=True
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True
    )
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    income_account = relationship("IncomeAccount")
    vat_account = relationship("VatAccount")
    branch = relationship("Branch")
    counterparty = relationship("Counterparty")
    invoice = relationship("Invoice", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_link_key_type", "link_key", "transaction_type"),
    )