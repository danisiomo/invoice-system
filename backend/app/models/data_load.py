import uuid
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Date, Enum, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class DataLoadType(str, PyEnum):
    STANDARD = "standard"
    BY_DATE = "by_date"
    BY_ACCOUNT = "by_account"

class DataLoadStatus(str, PyEnum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    ERROR = "error"

class DataLoadPeriod(str, PyEnum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    THREE_MONTHS = "three_months"

class DataLoadLog(Base):
    """Журнал загрузки данных из АБС"""
    __tablename__ = "data_load_logs"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    load_type: Mapped[DataLoadType] = mapped_column(
        Enum(DataLoadType), comment="Тип загрузки"
    )
    status: Mapped[DataLoadStatus] = mapped_column(
        Enum(DataLoadStatus), default=DataLoadStatus.IN_PROGRESS
    )
    period_start: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Начало периода загрузки"
    )
    period_end: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Конец периода загрузки"
    )
    account_number: Mapped[str | None] = mapped_column(
        String(25), nullable=True, comment="Номер лицевого счета"
    )
    username: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Логин пользователя"
    )
    records_loaded: Mapped[int] = mapped_column(
        Integer, default=0, comment="Количество загруженных проводок"
    )
    error_code: Mapped[int] = mapped_column(
        Integer, default=0, comment="Код ошибки"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Сообщение об ошибке"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="Дата и время начала загрузки"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Дата и время окончания загрузки"
    )