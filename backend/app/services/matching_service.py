"""
Сервис связывания проводок.
Логика:
1. Берём все проводки со статусом NEW
2. Для каждой ищем парную по link_key и противоположному типу
3. Если пара найдена - меняем статус обеих на MATCHED
4. Создаём черновик счёта-фактуры из пары
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)


async def generate_invoice_number(session: AsyncSession) -> str:
    """Генерация номера счёта-фактуры. Формат: СФ-2026-0001"""
    now = datetime.now(timezone.utc)
    year = now.year

    # Считаем сколько СФ уже есть в этом году
    from sqlalchemy import func, extract
    result = await session.execute(
        select(func.count(Invoice.id)).where(
            extract("year", Invoice.created_at) == year
        )
    )
    count = result.scalar() or 0
    return f"СФ-{year}-{str(count + 1).zfill(4)}"


async def create_invoice_from_pair(
    session: AsyncSession,
    income_transaction: Transaction,
    vat_transaction: Transaction,
) -> Invoice:
    number = await generate_invoice_number(session)
    total_amount = income_transaction.amount
    vat_amount = vat_transaction.amount
    total_with_vat = total_amount + vat_amount

    invoice = Invoice(
        number=number,
        invoice_date=income_transaction.transaction_date,
        status="draft",
        total_amount=total_amount,
        vat_amount=vat_amount,
        total_with_vat=total_with_vat,
        service_code=income_transaction.service_code,
        service_name=income_transaction.service_name,
        vat_rate=vat_transaction.vat_rate,
        country_code=income_transaction.country_code,
        branch_id=income_transaction.branch_id,
        counterparty_id=income_transaction.counterparty_id,
    )
    session.add(invoice)
    await session.flush()

    income_transaction.invoice_id = invoice.id
    income_transaction.status = "invoiced"
    vat_transaction.invoice_id = invoice.id
    vat_transaction.status = "invoiced"

    logger.info(
        f"Создана СФ {number} из проводок "
        f"{income_transaction.external_id} + {vat_transaction.external_id}"
    )
    return invoice


async def match_transactions() -> dict:
    logger.info("Запуск сервиса связывания проводок...")
    matched_pairs = 0
    created_invoices = 0
    errors = 0

    async with async_session() as session:
        result = await session.execute(
            select(Transaction).where(
                Transaction.status == "new",
                Transaction.transaction_type == "income",
            )
        )
        income_transactions = result.scalars().all()
        logger.info(f"Найдено новых доходных проводок: {len(income_transactions)}")

        for income_tx in income_transactions:
            try:
                vat_result = await session.execute(
                    select(Transaction).where(
                        Transaction.link_key == income_tx.link_key,
                        Transaction.transaction_type == "vat",
                        Transaction.status == "new",
                    )
                )
                vat_tx = vat_result.scalar_one_or_none()

                if not vat_tx:
                    logger.debug(
                        f"Парная НДС проводка не найдена для {income_tx.external_id}"
                    )
                    continue

                income_tx.status = "matched"
                vat_tx.status = "matched"
                matched_pairs += 1

                await create_invoice_from_pair(session, income_tx, vat_tx)
                created_invoices += 1

            except Exception as e:
                logger.error(f"Ошибка обработки проводки {income_tx.external_id}: {e}")
                income_tx.status = "error"
                errors += 1
                continue

        await session.commit()

    result = {
        "status": "success",
        "matched_pairs": matched_pairs,
        "created_invoices": created_invoices,
        "errors": errors,
    }
    logger.info(f"Связывание завершено: {result}")
    return result