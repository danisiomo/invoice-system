import json
import logging
from datetime import date, datetime
from decimal import Decimal
import aio_pika
from app.config import settings

logger = logging.getLogger(__name__)


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    return str(obj)


async def publish_invoice_to_edo(message: dict) -> None:
    """Публикует подготовленное сообщение в очередь ЭДО"""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        await channel.declare_queue(settings.QUEUE_OUTGOING_INVOICES, durable=True)

        body = json.dumps(message, ensure_ascii=False, default=_json_default).encode("utf-8")
        amqp_message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await channel.default_exchange.publish(
            amqp_message,
            routing_key=settings.QUEUE_OUTGOING_INVOICES,
        )
        logger.info("Producer: invoice published to EDO queue number=%s", message.get("number"))
    finally:
        await connection.close()