import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Numeric, DateTime, Date, Enum,
    ForeignKey, Text, func, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TransactionType(str, PyEnum):
    """Тип проводки"""
    INCOME = "income"   # Доходная
    VAT = "vat"         # НДС


class TransactionStatus(str, PyEnum):
    """Статус обработки проводки"""
    NEW = "new"             # Только поступила
    MATCHED = "matched"     # Связана с парной проводкой
    INVOICED = "invoiced"   # Включена в счёт-фактуру
    ERROR = "error"         # Ошибка обработки


class Transaction(Base):
    """Проводка из АБС"""
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Идентификатор из АБС
    external_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True,
        comment="Внешний ID проводки в АБС"
    )

    # Даты
    transaction_date: Mapped[date] = mapped_column(
        Date, comment="Дата проводки"
    )

    # Тип и статус
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), comment="Тип: доходная или НДС"
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.NEW,
        comment="Статус обработки"
    )

    # Финансовые данные
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), comment="Сумма проводки"
    )

    # Номер договора
    contract_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Номер договора"
    )

    # Услуга
    service_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Код услуги"
    )
    service_name: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Наименование услуги"
    )

    # НДС
    vat_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Ставка НДС"
    )

    # Ключ связывания — по нему ищем пару доходная + НДС
    link_key: Mapped[str] = mapped_column(
        String(200), index=True,
        comment="Ключ связки для поиска парной проводки"
    )

    # Код страны
    country_code: Mapped[str | None] = mapped_column(
        String(3), nullable=True, comment="Код страны"
    )

    # Связи со справочниками
    income_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("income_accounts.id"),
        nullable=True,
        comment="Счёт доходов"
    )
    vat_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vat_accounts.id"),
        nullable=True,
        comment="Счёт НДС"
    )

    # Связь с отделением
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id"),
        nullable=True,
        comment="Отделение банка"
    )

    # Контрагент
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("counterparties.id"),
        nullable=True,
        comment="Контрагент"
    )

    # Ссылка на СФ (заполняется после включения в СФ)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=True,
        comment="Счёт-фактура"
    )

    # Исходное сообщение из очереди
    raw_data: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Исходное сообщение из RabbitMQ (JSON)"
    )

    # Метаданные
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
        # Индекс для быстрого поиска пар по ключу связки
        Index("ix_transactions_link_key_type", "link_key", "transaction_type"),
    )