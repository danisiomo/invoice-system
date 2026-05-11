import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Counterparty(Base):
    """Контрагент"""
    __tablename__ = "counterparties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inn: Mapped[str] = mapped_column(
        String(12), index=True, comment="ИНН"
    )
    kpp: Mapped[str | None] = mapped_column(
        String(9), nullable=True, comment="КПП"
    )
    full_name: Mapped[str] = mapped_column(
        String(500), comment="Полное наименование"
    )
    short_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Краткое наименование"
    )
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Адрес"
    )
    phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Телефон"
    )
    responsible_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("responsibles.id"),
        nullable=True,
        comment="Ответственный"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    responsible = relationship("Responsible")