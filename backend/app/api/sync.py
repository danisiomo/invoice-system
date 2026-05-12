from fastapi import APIRouter, Depends, BackgroundTasks
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.counterparty_sync import sync_counterparties
from app.services.matching_service import match_transactions

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