import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Responsible(Base):
    """Справочник ответственных по с/ф"""
    __tablename__ = "responsibles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(100), comment="Логин пользователя"
    )
    full_name: Mapped[str] = mapped_column(
        String(255), comment="ФИО"
    )
    department: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Отдел"
    )
    regional_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regional_centers.id"),
        comment="Региональный центр"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    regional_center = relationship("RegionalCenter")