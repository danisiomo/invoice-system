from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.sorting import get_sort_params, apply_sorting
from app.core.dependencies import get_current_user
from app.database import get_session, async_session
from app.models.data_load import DataLoadLog, DataLoadType, DataLoadStatus, DataLoadPeriod
from app.models.user import User
from app.schemas.data_load import (
    DataLoadLogResponse,
    DataLoadLogListResponse,
    DataLoadStandardRequest,
    DataLoadByDateRequest,
    DataLoadByAccountRequest,
)

router = APIRouter(prefix="/data-load", tags=["Журнал загрузки из АБС"])


def get_period_dates(period: DataLoadPeriod) -> datetime:
    now = datetime.now(timezone.utc)
    if period == DataLoadPeriod.HOUR:
        return now - timedelta(hours=1)
    elif period == DataLoadPeriod.DAY:
        return now - timedelta(days=1)
    elif period == DataLoadPeriod.WEEK:
        return now - timedelta(weeks=1)
    elif period == DataLoadPeriod.MONTH:
        return now - timedelta(days=30)
    elif period == DataLoadPeriod.THREE_MONTHS:
        return now - timedelta(days=90)
    return now - timedelta(days=90)

# фон загрузок

async def run_standard_load(log_id: str):
    """фоновая задача стандартной загрузки (пока заглушка). В реальности тут получение проводок из АБС через кролика"""
    import asyncio
    await asyncio.sleep(3)
    async with async_session() as session:
        result = await session.execute(
            select(DataLoadLog).where(DataLoadLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = DataLoadStatus.SUCCESS
            log.records_loaded = 0
            log.finished_at = datetime.now(timezone.utc)
            await session.commit()


async def run_by_date_load(log_id: str):
    """фоновая задача загрузки за день"""
    import asyncio
    await asyncio.sleep(2)

    async with async_session() as session:
        result = await session.execute(
            select(DataLoadLog).where(DataLoadLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = DataLoadStatus.SUCCESS
            log.records_loaded = 0
            log.finished_at = datetime.now(timezone.utc)
            await session.commit()


async def run_by_account_load(log_id: str):
    """фон загрузки по счёту"""
    import asyncio
    await asyncio.sleep(2)

    async with async_session() as session:
        result = await session.execute(
            select(DataLoadLog).where(DataLoadLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if log:
            log.status = DataLoadStatus.SUCCESS
            log.records_loaded = 0
            log.finished_at = datetime.now(timezone.utc)
            await session.commit()

#  запуск загрузок

@router.post("/standard", response_model=DataLoadLogResponse, status_code=201)
async def load_standard(
    data: DataLoadStandardRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Стандартная загрузка"""
    last_load = await session.execute(
        select(DataLoadLog)
        .where(DataLoadLog.status == DataLoadStatus.SUCCESS)
        .order_by(DataLoadLog.started_at.desc())
        .limit(1)
    )
    last = last_load.scalar_one_or_none()
    period_start = last.period_end if last else date(2024, 1, 1)
    period_end = date.today()

    log = DataLoadLog(
        load_type=DataLoadType.STANDARD,
        status=DataLoadStatus.IN_PROGRESS,  # Сразу in_progress
        period_start=period_start,
        period_end=period_end,
        username=current_user.username,
        records_loaded=0,
        error_code=0,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)

    # Запускаем фоновую задачу
    background_tasks.add_task(run_standard_load, str(log.id))

    return log


@router.post("/by-date", response_model=DataLoadLogResponse, status_code=201)
async def load_by_date(
    data: DataLoadByDateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Загрузка за конкретный день"""
    log = DataLoadLog(
        load_type=DataLoadType.BY_DATE,
        status=DataLoadStatus.IN_PROGRESS,
        period_start=data.load_date,
        period_end=data.load_date,
        username=current_user.username,
        records_loaded=0,
        error_code=0,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)

    background_tasks.add_task(run_by_date_load, str(log.id))

    return log


@router.post("/by-account", response_model=DataLoadLogResponse, status_code=201)
async def load_by_account(
    data: DataLoadByAccountRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Загрузка по счёту"""
    log = DataLoadLog(
        load_type=DataLoadType.BY_ACCOUNT,
        status=DataLoadStatus.IN_PROGRESS,
        period_start=data.date_from,
        period_end=date.today(),
        account_number=data.account_number,
        username=current_user.username,
        records_loaded=0,
        error_code=0,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)

    background_tasks.add_task(run_by_account_load, str(log.id))

    return log

#  журнал загрузок

@router.get("/log", response_model=DataLoadLogListResponse)
async def get_load_log(
        period: DataLoadPeriod | None = Query(None),
        status: DataLoadStatus | None = None,
        load_type: DataLoadType | None = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        sort_by: str = Query("started_at", description="Поле для сортировки"),
        sort_order: str = Query("DESC", description="Направление: ASC или DESC"),
        session: AsyncSession = Depends(get_session),
        _: User = Depends(get_current_user),
):
    if sort_order.upper() not in ("ASC", "DESC"):
        raise HTTPException(400, "sort_order должен быть ASC или DESC")

    query = select(DataLoadLog)

    if period:
        period_start = get_period_dates(period)
        query = query.where(DataLoadLog.started_at >= period_start)
    if status:
        query = query.where(DataLoadLog.status == status)
    if load_type:
        query = query.where(DataLoadLog.load_type == load_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = apply_sorting(query, DataLoadLog, sort_by, sort_order.upper())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    logs = result.scalars().all()

    return DataLoadLogListResponse(
        items=[DataLoadLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/log/last", response_model=DataLoadLogResponse | None)
async def get_last_load(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Последняя успешная загрузка"""
    result = await session.execute(
        select(DataLoadLog)
        .where(DataLoadLog.status == DataLoadStatus.SUCCESS)
        .order_by(DataLoadLog.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/log/{log_id}", response_model=DataLoadLogResponse)
async def get_log_by_id(
    log_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Получить запись журнала по ID, для проверки статуса загрузки"""
    result = await session.execute(
        select(DataLoadLog).where(DataLoadLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(404, "Запись журнала не найдена")
    return log