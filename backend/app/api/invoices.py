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
    _: User = Depends(get_current_user),
):
    """Редактирование с/ф (только черновик/на проверке)"""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт‑фактура не найдена")

    # Редактируем только пока документ не подтверждён/не отправлен/не отменён
    if invoice.status in ("approved", "sent", "cancelled"):
        raise HTTPException(
            400,
            "Нельзя редактировать эту СФ. Если нужно исправить — верните в черновик отдельной операцией.",
        )

    # Статусы через патч не меняются
    update_data = data.model_dump(exclude_unset=True, exclude={"status"})

    # Список полей для редактирования
    allowed_fields = {
        "service_name",
        "service_code",
        "unit_name",
        "quantity",
        "price",
        "vat_rate",
        "special_sales_book",
        "inter_price_difference",
        "correction_number",
        "payment_document_number",
        "payment_date",
        "counterparty_id",
        "branch_id",
        "regional_center_id",
        "currency_code",
        "country_code",
    }
    changed_fields = set()
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(invoice, field, value)
            changed_fields.add(field)
    # Пересчёт сумм
    if changed_fields.intersection({"quantity", "price", "vat_rate"}):
        from app.services.invoice_calc import recalc_invoice_amounts
        recalc_invoice_amounts(invoice)
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

@router.post("/{invoice_id}/return-to-draft", response_model=InvoiceResponse)
async def return_invoice_to_draft(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Счёт-фактура не найдена")
    if invoice.status == "sent":
        raise HTTPException(400, "Нельзя вернуть в черновик отправленную СФ")
    if invoice.status != "approved":
        raise HTTPException(400, f"Вернуть в черновик можно только approved, сейчас статус '{invoice.status}'")

    invoice.status = "draft"
    invoice.confirmed_by_id = None
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