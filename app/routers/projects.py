from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Project
from ..pagination import paginate
from ..presenters import project_detail_out, project_list_out

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/")
@router.get("", include_in_schema=False)
def list_projects(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
) -> dict:
    stmt = (
        select(Project)
        .where(Project.is_published.is_(True))
        .options(selectinload(Project.technologies))
        .order_by(Project.created_at.desc(), Project.id.desc())
    )
    return paginate(db, stmt, request, page, lambda row: project_list_out(row, request))


@router.get("/{slug}/")
@router.get("/{slug}", include_in_schema=False)
def get_project(slug: str, request: Request, db: Session = Depends(get_db)) -> dict:
    project = (
        db.execute(
            select(Project)
            .where(Project.slug == slug, Project.is_published.is_(True))
            .options(selectinload(Project.technologies))
        )
        .scalars()
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return project_detail_out(project, request)
