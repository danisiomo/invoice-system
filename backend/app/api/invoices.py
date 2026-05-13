import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.core.sorting import get_sort_params, apply_sorting
from app.database import get_session
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.invoice import (
    InvoiceResponse,
    InvoiceListPaginated,
    InvoiceUpdate,
)

router = APIRouter(prefix="/invoices", tags=["Счета-фактуры"])


@router.get("", response_model=InvoiceListPaginated)
async def list_invoices(
    status: str | None = None,
    counterparty_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    sort_by: str = Query("invoice_date", description="Поле для сортировки"),
    sort_order: str = Query("DESC", description="ASC или DESC"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Реестр с/ф с фильтрацией"""
    query = select(Invoice)
    if status:
        query = query.where(Invoice.status == status)
    if counterparty_id:
        query = query.where(Invoice.counterparty_id == counterparty_id)
    if branch_id:
        query = query.where(Invoice.branch_id == branch_id)
    if date_from:
        query = query.where(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    if sort_order.upper() not in ("ASC", "DESC"):
        raise HTTPException(400, "sort_order должен быть ASC или DESC")

    query = apply_sorting(query, Invoice, sort_by, sort_order.upper())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    invoices = result.scalars().all()

    return InvoiceListPaginated(
        items=invoices,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Детальная карточка с/ф"""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт-фактура не найдена")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Редактирование с/ф бухгалтером"""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт-фактура не найдена")

    if invoice.status in ("sent", "cancelled"):
        raise HTTPException(400, "Нельзя редактировать эту СФ")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(invoice, field, value)

    await session.flush()
    await session.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/approve", response_model=InvoiceResponse)
async def approve_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Утвердить с/ф"""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт-фактура не найдена")

    if invoice.status not in ("draft", "review"):
        raise HTTPException(400, f"Нельзя утвердить СФ со статусом '{invoice.status}'")

    invoice.status = "approved"
    invoice.confirmed_by_id = current_user.id
    await session.flush()
    await session.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Отменить с/ф"""
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт-фактура не найдена")

    if invoice.status == "sent":
        raise HTTPException(400, "Нельзя отменить отправленную СФ")
    # Возвращаем проводки в статус new
    await session.execute(
        select(Transaction).where(Transaction.invoice_id == invoice_id)
    )
    transactions_result = await session.execute(
        select(Transaction).where(Transaction.invoice_id == invoice_id)
    )
    for tx in transactions_result.scalars().all():
        tx.status = "new"
        tx.invoice_id = None

    invoice.status = "cancelled"
    await session.flush()
    await session.refresh(invoice)
    return invoice