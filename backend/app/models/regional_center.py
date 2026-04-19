import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RegionalCenter(Base):
    """Р/ц"""
    __tablename__ = "regional_centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True,
        comment="Код регионального центра"
    )
    name: Mapped[str] = mapped_column(
        String(500), comment="Наименование"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    branches = relationship("Branch", back_populates="regional_center")
    vat_accounts = relationship("VatAccount", back_populates="regional_center")