import asyncio
import logging

from app.services.counterparty_sync import sync_counterparties
from app.services.matching_service import match_transactions
from app.services.edo_sender import send_approved_invoices

logger = logging.getLogger(__name__)


async def job_sync_counterparties(interval_sec: int = 86400):
    """Фоновая задача: синхронизация контрагентов (раз в сутки)."""
    try:
        while True:
            logger.info("Джоба: синхронизация контрагентов")
            await sync_counterparties()
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("Джоба: синхронизация контрагентов остановлена")
        raise


async def job_matching(interval_sec: int = 5, batch_size: int = 200):
    """Фоновая задача: связывание проводок и сборка СФ."""
    try:
        while True:
            logger.info("Джоба: связывание проводок (batch=%s)", batch_size)
            await match_transactions(limit=batch_size)
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("Джоба: связывание проводок остановлено")
        raise


async def job_send_edo(interval_sec: int = 5, batch_size: int = 100):
    """Фоновая задача: отправка approved СФ в ЭДО."""
    try:
        while True:
            logger.info("Джоба: отправка approved СФ в ЭДО (batch=%s)", batch_size)
            await send_approved_invoices(limit=batch_size)
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("Джоба: отправка в ЭДО остановлена")
        raise