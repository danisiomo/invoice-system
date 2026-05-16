import json
import logging

import aio_pika
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate

logger = logging.getLogger(__name__)


async def process_message(message: aio_pika.IncomingMessage) -> None:
    # requeue=False, иначе при любой ошибке можно уйти в бесконечный цикл
    async with message.process(requeue=False, reject_on_redelivered=True):
        data = json.loads(message.body.decode("utf-8"))
        external_id = data.get("external_id")
        logger.info("RabbitMQ: got transaction external_id=%s", external_id)
        #Валидируем и парсим типы (date/Decimal/enum)
        tx_in = TransactionCreate.model_validate(data)
        tx_dict = tx_in.model_dump()
        #Нормализуем под нашу модель (в БД храним строки)
        tt = tx_dict["transaction_type"]
        tx_dict["transaction_type"] = tt.value if hasattr(tt, "value") else str(tt).lower()
        tx_dict["status"] = "new"
        async with async_session() as session:
            exists = await session.execute(
                select(Transaction.id).where(Transaction.external_id == tx_dict["external_id"])
            )
            if exists.scalar_one_or_none():
                logger.warning("RabbitMQ: duplicate external_id=%s (skip)", tx_dict["external_id"])
                return
            session.add(Transaction(**tx_dict))
            await session.commit()
            logger.info("RabbitMQ: saved external_id=%s", tx_dict["external_id"])


async def start_consumer() -> aio_pika.RobustConnection:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=50)
    queue = await channel.declare_queue(
        settings.QUEUE_INCOMING_TRANSACTIONS,
        durable=True,
    )

    await queue.consume(process_message)
    logger.info("RabbitMQ consumer started. Queue=%s", settings.QUEUE_INCOMING_TRANSACTIONS)
    return connection