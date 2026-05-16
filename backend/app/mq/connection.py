import aio_pika
from app.config import settings

_connection = None


async def get_rabbitmq_connection():
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def close_rabbitmq():
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = None