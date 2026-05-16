from fastapi import APIRouter, Depends, BackgroundTasks
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.counterparty_sync import sync_counterparties
from app.services.matching_service import match_transactions
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.invoice import Invoice
from app.services.edo_sender import send_approved_invoices, send_invoice_to_edo
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/sync", tags=["Синхронизация"])


@router.post("/counterparties")
async def manual_sync_counterparties(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_user),
):
    """ручной запуск синхронизации контрагентов из АБС.
    Запускается в фоне - сразу возвращает ответ.
    Автоматически запускается раз в день при старте приложения"""
    background_tasks.add_task(sync_counterparties)
    return {
        "status": "started",
        "message": "Синхронизация контрагентов запущена в фоне"
    }

@router.post("/match-transactions")
async def manual_match_transactions(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_user),
):
    """Ручной запуск связывания проводок. Запускается в фоне - сразу возвращает ответ."""
    background_tasks.add_task(match_transactions)
    return {
        "status": "started",
        "message": "Связывание проводок запущено в фоне"
    }

@router.post("/send-approved-invoices")
async def manual_send_approved_invoices(
    limit: int = 100,
    _: User = Depends(get_current_user),
):
    return await send_approved_invoices(limit=limit)


@router.post("/send-invoice/{invoice_id}")
async def manual_send_one_invoice(
    invoice_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Invoice)
        .options(selectinload(Invoice.counterparty), selectinload(Invoice.branch))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    if invoice.status != "approved":
        raise HTTPException(400, f"Invoice status must be approved, got '{invoice.status}'")

    await send_invoice_to_edo(session, invoice)
    await session.flush()
    await session.refresh(invoice)
    return {"status": "ok", "invoice_id": str(invoice.id), "new_status": invoice.status}