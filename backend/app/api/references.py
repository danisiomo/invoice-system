import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_session
from app.models.regional_center import RegionalCenter
from app.models.branch import Branch
from app.models.vat_account import VatAccount
from app.models.user import User
from app.schemas.regional_center import RegionalCenterCreate, RegionalCenterResponse
from app.schemas.branch import BranchCreate, BranchResponse
from app.schemas.vat_account import (
    VatAccountCreate, VatAccountUpdate,
    VatAccountResponse, VatAccountListResponse,
)

router = APIRouter(prefix="/references", tags=["Справочники"])

#  Рег. центры

@router.get("/regional-centers", response_model=list[RegionalCenterResponse])
async def list_regional_centers(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Список р/ц"""
    result = await session.execute(
        select(RegionalCenter).order_by(RegionalCenter.code)
    )
    return result.scalars().all()


@router.post("/regional-centers", response_model=RegionalCenterResponse, status_code=201)
async def create_regional_center(
    data: RegionalCenterCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Создать р/ц"""
    existing = await session.execute(
        select(RegionalCenter).where(RegionalCenter.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Региональный центр с кодом {data.code} уже существует")

    rc = RegionalCenter(**data.model_dump())
    session.add(rc)
    await session.flush()
    await session.refresh(rc)
    return rc

#  Отделения
@router.get("/branches", response_model=list[BranchResponse])
async def list_branches(
    regional_center_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Список отделений. Фильтр по р/ц"""
    query = select(Branch).order_by(Branch.code)
    if regional_center_id:
        query = query.where(Branch.regional_center_id == regional_center_id)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/branches", response_model=BranchResponse, status_code=201)
async def create_branch(
    data: BranchCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Создать отделение"""
    # Проверяем что р/ц сущесьвует
    rc = await session.execute(
        select(RegionalCenter).where(RegionalCenter.id == data.regional_center_id)
    )
    if not rc.scalar_one_or_none():
        raise HTTPException(404, "Региональный центр не найден")

    existing = await session.execute(
        select(Branch).where(Branch.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Отделение с кодом {data.code} уже существует")

    branch = Branch(**data.model_dump())
    session.add(branch)
    await session.flush()
    await session.refresh(branch)
    return branch

#  Справочник счетов ндс

@router.get("/vat-accounts", response_model=VatAccountListResponse)
async def list_vat_accounts(
    regional_center_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
    account_number: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    query = select(VatAccount)
    if regional_center_id:
        query = query.where(VatAccount.regional_center_id == regional_center_id)
    if branch_id:
        query = query.where(VatAccount.branch_id == branch_id)
    if account_number:
        query = query.where(VatAccount.account_number.ilike(f"%{account_number}%"))

    # Общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Пагинация, сортировка по н/с
    query = (
        query
        .order_by(VatAccount.account_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await session.execute(query)
    accounts = result.scalars().all()

    return VatAccountListResponse(
        items=[VatAccountResponse.model_validate(a) for a in accounts],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/vat-accounts", response_model=VatAccountResponse, status_code=201)
async def create_vat_account(
    data: VatAccountCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Добавить новый счет НДС"""
    # Проверяем р/ц
    rc = await session.execute(
        select(RegionalCenter).where(RegionalCenter.id == data.regional_center_id)
    )
    if not rc.scalar_one_or_none():
        raise HTTPException(404, "Региональный центр не найден")

    # Проверяем отделение
    branch = await session.execute(
        select(Branch).where(Branch.id == data.branch_id)
    )
    if not branch.scalar_one_or_none():
        raise HTTPException(404, "Отделение не найдено")

    account = VatAccount(**data.model_dump())
    session.add(account)
    await session.flush()
    await session.refresh(account)
    return account


@router.get("/vat-accounts/{account_id}", response_model=VatAccountResponse)
async def get_vat_account(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Получить счет НДС по ID"""
    result = await session.execute(
        select(VatAccount).where(VatAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "Счет НДС не найден")
    return account


@router.patch("/vat-accounts/{account_id}", response_model=VatAccountResponse)
async def update_vat_account(
    account_id: uuid.UUID,
    data: VatAccountUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Редактировать счет НДС"""
    result = await session.execute(
        select(VatAccount).where(VatAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "Счет НДС не найден")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    await session.flush()
    await session.refresh(account)
    return account


@router.delete("/vat-accounts/{account_id}", status_code=204)
async def delete_vat_account(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    """Удалить счет НДС"""
    result = await session.execute(
        select(VatAccount).where(VatAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "Счет НДС не найден")

    await session.delete(account)