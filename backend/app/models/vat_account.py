import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VatAccount(Base):
    """Справочник счетов НДС"""
    __tablename__ = "vat_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_number: Mapped[str] = mapped_column(
        String(25), index=True,
        comment="Номер счета по НДС"
    )
    name: Mapped[str] = mapped_column(
        String(500), comment="Наименование счета"
    )
    regional_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_centers.id"),
        comment="Региональный центр"
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"),
        comment="Отделение"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    regional_center = relationship("RegionalCenter", back_populates="vat_accounts")
    branch = relationship("Branch", back_populates="vat_accounts")