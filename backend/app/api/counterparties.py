import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.sorting import get_sort_params, apply_sorting
from app.database import get_session
from app.models.counterparty import Counterparty
from app.models.user import User
from app.schemas.counterparty import (
    CounterpartyCreate, CounterpartyUpdate,
    CounterpartyResponse, CounterpartyListResponse,
)

router = APIRouter(prefix="/counterparties", tags=["Контрагенты"])


@router.get("", response_model=CounterpartyListResponse)
async def list_counterparties(
    inn: str | None = None,
    full_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: dict = Depends(get_sort_params),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Список контрагентов с фильтрацией"""
    query = select(Counterparty)

    if inn:
        query = query.where(Counterparty.inn.ilike(f"%{inn}%"))
    if full_name:
        query = query.where(Counterparty.full_name.ilike(f"%{full_name}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = apply_sorting(query, Counterparty, sort["sort_by"], sort["sort_order"])
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    counterparties = result.scalars().all()

    return CounterpartyListResponse(
        items=[CounterpartyResponse.model_validate(c) for c in counterparties],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=CounterpartyResponse, status_code=201)
async def create_counterparty(
    data: CounterpartyCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Создать контрагента"""
    counterparty = Counterparty(**data.model_dump())
    session.add(counterparty)
    await session.flush()
    await session.refresh(counterparty)
    return counterparty


@router.get("/{counterparty_id}", response_model=CounterpartyResponse)
async def get_counterparty(
    counterparty_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Получить контрагента по ID"""
    result = await session.execute(
        select(Counterparty).where(Counterparty.id == counterparty_id)
    )
    counterparty = result.scalar_one_or_none()
    if not counterparty:
        raise HTTPException(404, "Контрагент не найден")
    return counterparty


@router.patch("/{counterparty_id}", response_model=CounterpartyResponse)
async def update_counterparty(
    counterparty_id: uuid.UUID,
    data: CounterpartyUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Редактировать контрагента"""
    result = await session.execute(
        select(Counterparty).where(Counterparty.id == counterparty_id)
    )
    counterparty = result.scalar_one_or_none()
    if not counterparty:
        raise HTTPException(404, "Контрагент не найден")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(counterparty, field, value)

    await session.flush()
    await session.refresh(counterparty)
    return counterparty


@router.delete("/{counterparty_id}", status_code=204)
async def delete_counterparty(
    counterparty_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Удалить контрагента"""
    result = await session.execute(
        select(Counterparty).where(Counterparty.id == counterparty_id)
    )
    counterparty = result.scalar_one_or_none()
    if not counterparty:
        raise HTTPException(404, "Контрагент не найден")
    await session.delete(counterparty)