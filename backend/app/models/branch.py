import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, func, Boolean
from app.database import Base


class Branch(Base):
    """Отделение банка"""
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True,
        comment="Код отделения"
    )
    name: Mapped[str] = mapped_column(
        String(500), comment="Наименование отделения"
    )
    address: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Адрес"
    )
    inn: Mapped[str | None] = mapped_column(
        String(12), nullable=True, comment="ИНН"
    )
    kpp: Mapped[str | None] = mapped_column(
        String(9), nullable=True, comment="КПП"
    )
    regional_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_centers.id"),
        comment="Региональный центр"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    auto_confirm: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Флаг автоматического подтверждения СФ"
    )
    regional_center = relationship("RegionalCenter", back_populates="branches")
    vat_accounts = relationship("VatAccount", back_populates="branch")