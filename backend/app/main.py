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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def daily_sync_job():
    """
    Джоба синхронизации контрагентов.
    Запускается раз в день (86400 секунд).
    """
    while True:
        logger.info("Автоджоба: запуск синхронизации контрагентов")
        await sync_counterparties()
        await asyncio.sleep(86400)  # 24 часа


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")

    # Запускаем джобу синхронизации в фоне
    asyncio.create_task(daily_sync_job())
    logger.info("Джоба синхронизации контрагентов запущена")

    yield

    logger.info("Остановка приложения...")


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

@app.get("/")
async def root():
    return {"message": "Invoice System MVP", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}