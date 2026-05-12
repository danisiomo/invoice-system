import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.sorting import get_sort_params, apply_sorting
from app.database import get_session
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    TransactionBatchCreate,
    TransactionBatchResponse,
)

router = APIRouter(prefix="/transactions", tags=["Проводки АБС"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    transaction_type: TransactionType | None = None,
    status: TransactionStatus | None = None,
    link_key: str | None = None,
    branch_id: uuid.UUID | None = None,
    counterparty_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("transaction_date", description="Поле для сортировки"),
    sort_order: str = Query("DESC", description="ASC или DESC"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Список проводок с фильтрацией"""
    query = select(Transaction)

    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if status:
        query = query.where(Transaction.status == status)
    if link_key:
        query = query.where(Transaction.link_key == link_key)
    if branch_id:
        query = query.where(Transaction.branch_id == branch_id)
    if counterparty_id:
        query = query.where(Transaction.counterparty_id == counterparty_id)
    if date_from:
        query = query.where(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.where(Transaction.transaction_date <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = apply_sorting(query, Transaction, sort_by, sort_order.upper())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Создать одну проводку. Используется для тестирования пока нет RabbitMQ Consumer"""
    # Проверяем уникальность external_id
    existing = await session.execute(
        select(Transaction).where(Transaction.external_id == data.external_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Проводка с external_id={data.external_id} уже существует")

    transaction = Transaction(**data.model_dump())
    session.add(transaction)
    await session.flush()
    await session.refresh(transaction)
    return transaction


@router.post("/batch", response_model=TransactionBatchResponse, status_code=201)
async def create_transactions_batch(
    data: TransactionBatchCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """
    Создать пачку проводок за один запрос.
    Используется для загрузки тестовых данных.
    Если проводка с таким external_id уже есть — пропускаем.
    """
    created = 0
    skipped = 0
    errors = 0

    for item in data.transactions:
        try:
            existing = await session.execute(
                select(Transaction).where(
                    Transaction.external_id == item.external_id
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            transaction = Transaction(**item.model_dump())
            session.add(transaction)
            created += 1

        except Exception:
            errors += 1
            continue

    await session.flush()

    return TransactionBatchResponse(
        created=created,
        skipped=skipped,
        errors=errors,
        total=created + skipped + errors,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Получить проводку по ID"""
    result = await session.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(404, "Проводка не найдена")
    return transaction


@router.get("/by-link-key/{link_key}", response_model=list[TransactionResponse])
async def get_transactions_by_link_key(
    link_key: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """
    Получить все проводки по ключу связки.
    Используется для проверки - нашлась ли пара (доходная + НДС).
    """
    result = await session.execute(
        select(Transaction).where(Transaction.link_key == link_key)
    )
    transactions = result.scalars().all()
    if not transactions:
        raise HTTPException(404, f"Проводки с link_key={link_key} не найдены")
    return transactions