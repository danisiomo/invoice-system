import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router
from app.api.data_load import router as data_load_router
from app.api.references import router as references_router
from app.api.counterparties import router as counterparties_router
from app.api.mock_abs import router as mock_abs_router
from app.api.sync import router as sync_router
from app.services.counterparty_sync import sync_counterparties
from app.api.transactions import router as transactions_router
from app.services.matching_service import match_transactions
from app.api.invoices import router as invoices_router
from app.mq.consumer import start_consumer
from app.mq.connection import close_rabbitmq
from app.services.edo_sender import send_approved_invoices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def daily_sync_job():
    """Джоба синхронизации контрагентов (раз в сутки)."""
    try:
        while True:
            logger.info("Автоджоба: запуск синхронизации контрагентов")
            await sync_counterparties()
            await asyncio.sleep(86400)
    except asyncio.CancelledError:
        logger.info("Автоджоба: синхронизация контрагентов остановлена")
        raise

async def matching_job():
    """Джоба связывания проводок (каждые 5 минут)"""
    try:
        while True:
            logger.info("Автоджоба: запуск связывания проводок")
            await match_transactions(limit=200)
            await asyncio.sleep(300)
    except asyncio.CancelledError:
        logger.info("Автоджоба: связывание проводок остановлено")
        raise

async def edo_send_job():
    """Джоба отправки подтверждённых СФ в ЭДО. Запускается каждые 5 секунд"""
    try:
        while True:
            logger.info("Автоджоба: отправка подтверждённых СФ в ЭДО")
            await send_approved_invoices(limit=100)
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info("Автоджоба: отправка в ЭДО остановлена")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    #Запускаем фоновые задачи и сохраняем ссылки (важно для shutdown)
    app.state.tasks = [
        asyncio.create_task(daily_sync_job(), name="job_sync_counterparties"),
        asyncio.create_task(matching_job(), name="job_matching"),
        asyncio.create_task(edo_send_job(), name="job_send_edo"),
    ]
    #Запускаем RabbitMQ consumer (вход)
    app.state.rmq_connection = await start_consumer()
    logger.info("Джобы и consumer запущены")
    try:
        yield
    finally:
        logger.info("Остановка приложения...")
        #Останавливаем фоновые задачи
        tasks = getattr(app.state, "tasks", [])
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        #Закрываем RabbitMQ соединение
        conn = getattr(app.state, "rmq_connection", None)
        if conn:
            await conn.close()
        logger.info("Приложение остановлено")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(data_load_router, prefix=settings.API_V1_PREFIX)
app.include_router(references_router, prefix=settings.API_V1_PREFIX)
app.include_router(counterparties_router, prefix=settings.API_V1_PREFIX)
app.include_router(mock_abs_router, prefix=settings.API_V1_PREFIX)
app.include_router(sync_router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions_router, prefix=settings.API_V1_PREFIX)
app.include_router(invoices_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {"message": "Invoice System MVP", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}