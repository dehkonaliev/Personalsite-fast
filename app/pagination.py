from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .config import get_settings

settings = get_settings()


def paginate(
    db: Session,
    stmt: Select,
    request: Request,
    page: int,
    serialize: Callable[[Any], dict],
    page_size: int | None = None,
) -> dict:
    """DRF PageNumberPagination-compatible response."""
    page_size = page_size or settings.page_size
    if page < 1:
        raise HTTPException(status_code=404, detail="Invalid page.")

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Invalid page.")

    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all()

    def link(number: int) -> str:
        return str(request.url.include_query_params(page=number))

    return {
        "count": total,
        "next": link(page + 1) if page < total_pages else None,
        "previous": link(page - 1) if page > 1 else None,
        "results": [serialize(row) for row in rows],
    }
