from fastapi import Query, HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import DeclarativeBase


def get_sort_params(
        sort_by: str = Query("created_at", description="Поле для сортировки"),
        sort_order: str = Query("DESC", description="Направление: ASC или DESC"),
):
    """Универсальные параметры сортировки"""
    if sort_order.upper() not in ("ASC", "DESC"):
        raise HTTPException(400, "sort_order должен быть ASC или DESC")
    return {"sort_by": sort_by, "sort_order": sort_order.upper()}


def apply_sorting(query, model, sort_by: str, sort_order: str):
    """Применяет сортировку к запросу"""
    if not hasattr(model, sort_by):
        raise HTTPException(
            400,
            f"Поле '{sort_by}' не существует. "
            f"Доступные поля: {[c.key for c in model.__table__.columns]}"
        )

    column = getattr(model, sort_by)
    return query.order_by(asc(column) if sort_order == "ASC" else desc(column))