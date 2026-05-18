import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.invoice import Invoice
from app.mq.producer import publish_invoice_to_edo

logger = logging.getLogger(__name__)


def build_edo_message(invoice: Invoice) -> dict:
    """MVP-сообщение. Потом расширим под реальный контракт ЭДО"""
    cp = invoice.counterparty
    br = invoice.branch

    return {
        "id": str(invoice.id),
        "number": invoice.number,
        "invoice_date": invoice.invoice_date,
        "status": invoice.status,
        "currency_code": invoice.currency_code,
        "total_amount": invoice.total_amount,
        "vat_amount": invoice.vat_amount,
        "total_with_vat": invoice.total_with_vat,
        "service_code": invoice.service_code,
        "service_name": invoice.service_name,
        "vat_rate": invoice.vat_rate,
        "special_sales_book": invoice.special_sales_book,
        "inter_price_difference": invoice.inter_price_difference,
        "counterparty": (
            {
                "id": str(cp.id),
                "inn": cp.inn,
                "kpp": cp.kpp,
                "full_name": cp.full_name,
                "short_name": cp.short_name,
                "address": cp.address,
                "phone": cp.phone,
            }
            if cp
            else None
        ),
        "branch": (
            {"id": str(br.id), "code": br.code, "name": br.name, "kpp": br.kpp, "inn": br.inn}
            if br
            else None
        ),
        "sent_at": invoice.sent_at,
    }


async def send_invoice_to_edo(session: AsyncSession, invoice: Invoice) -> None:
    """Отправляет одну СФ. При успехе: status=sent, sent_at=now()"""
    msg = build_edo_message(invoice)
    await publish_invoice_to_edo(msg)

    invoice.status = "sent"
    invoice.sent_at = datetime.now(timezone.utc)


async def send_approved_invoices(limit: int = 100) -> dict:
    """Отправка пачки approved → sent"""
    sent = 0
    errors = 0

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Invoice)
                .options(selectinload(Invoice.counterparty), selectinload(Invoice.branch))
                .where(Invoice.status == "approved")
                .order_by(Invoice.created_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            invoices = result.scalars().all()

            if not invoices:
                return {"status": "ok", "sent": 0, "errors": 0, "total": 0}

            # Готовим сообщения один раз
            messages = [build_edo_message(inv) for inv in invoices]

            try:
                # Публикация пачкой одним соединением
                from app.mq.producer import publish_invoices_to_edo
                await publish_invoices_to_edo(messages)

                now = datetime.now(timezone.utc)
                for inv in invoices:
                    inv.status = "sent"
                    inv.sent_at = now
                    sent += 1

            except Exception as e:
                logger.exception("Ошибка отправки пачки СФ в ЭДО: %s", e)
                for inv in invoices:
                    inv.status = "error"
                    errors += 1

    return {"status": "ok", "sent": sent, "errors": errors, "total": sent + errors}