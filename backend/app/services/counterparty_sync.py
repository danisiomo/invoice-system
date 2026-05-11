"""
Сервис синхронизации контрагентов из АБС.
Джоба запускается раз в день автоматически.
Дёргает мок-эндпоинт АБС и синхронизирует данные в нашу БД.
"""
import logging
import httpx
from sqlalchemy import select
from app.database import async_session
from app.models.counterparty import Counterparty

logger = logging.getLogger(__name__)

# URL мок-эндпоинта АБС
# В реальности заменить на URL реальной АБС
ABS_COUNTERPARTIES_URL = "http://localhost:8000/api/v1/mock/abs/counterparties"


async def sync_counterparties():
    """Синхронизация контрагентов из АБС.
    Если контрагент с таким ИНН уже есть - обновляем данные
    Если нет - создаём новый"""
    logger.info("Запуск синхронизации контрагентов из АБС...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(ABS_COUNTERPARTIES_URL, timeout=30)
            response.raise_for_status()
            abs_counterparties = response.json()
    except Exception as e:
        logger.error(f"Ошибка получения данных из АБС: {e}")
        return {"status": "error", "message": str(e)}

    created = 0
    updated = 0

    async with async_session() as session:
        for item in abs_counterparties:
            result = await session.execute(
                select(Counterparty).where(Counterparty.inn == item["inn"])
            )
            counterparty = result.scalar_one_or_none()

            if counterparty:
                # Обновляем существующего
                counterparty.kpp = item.get("kpp")
                counterparty.full_name = item["full_name"]
                counterparty.short_name = item.get("short_name")
                counterparty.address = item.get("address")
                counterparty.phone = item.get("phone")
                updated += 1
                logger.info(f"Обновлён контрагент: {item['inn']}")
            else:
                # Создаём нового
                counterparty = Counterparty(
                    inn=item["inn"],
                    kpp=item.get("kpp"),
                    full_name=item["full_name"],
                    short_name=item.get("short_name"),
                    address=item.get("address"),
                    phone=item.get("phone"),
                )
                session.add(counterparty)
                created += 1
                logger.info(f"Создан контрагент: {item['inn']}")

        await session.commit()

    result = {
        "status": "success",
        "created": created,
        "updated": updated,
        "total": created + updated,
    }
    logger.info(f"Синхронизация завершена: {result}")
    return result