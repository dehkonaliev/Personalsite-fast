from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..i18n import get_lang, language_vary
from ..models import Certificates, Education, Experience, Resume, SkillType
from ..pagination import paginate
from ..presenters import (
    certificate_out,
    education_out,
    experience_out,
    home_out,
    resume_out,
    skill_group_out,
)

router = APIRouter(prefix="/api/main", tags=["main"])


@router.get("/homedata")
@router.get("/homedata/", include_in_schema=False)
def homedata(request: Request, response: Response, lang: str = Depends(get_lang), db: Session = Depends(get_db)) -> dict:
    response.headers.update(language_vary(lang))
    return home_out(db, request, lang)


@router.get("/resume/")
@router.get("/resume", include_in_schema=False)
def resume(request: Request, response: Response, lang: str = Depends(get_lang), db: Session = Depends(get_db)) -> dict:
    response.headers.update(language_vary(lang))
    row = db.query(Resume).order_by(Resume.id).first()
    return resume_out(db, row, request, lang)


@router.get("/educations/")
@router.get("/educations", include_in_schema=False)
def educations(
    request: Request,
    response: Response,
    page: int = 1,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    stmt = select(Education).order_by(Education.order.desc(), Education.id.desc())
    return paginate(
        db,
        stmt,
        request,
        page,
        lambda row: education_out(row, db, request, lang),
    )


@router.get("/experiences/")
@router.get("/experiences", include_in_schema=False)
def experiences(
    request: Request,
    response: Response,
    page: int = 1,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    stmt = select(Experience).order_by(Experience.order.desc(), Experience.id.desc())
    return paginate(
        db,
        stmt,
        request,
        page,
        lambda row: experience_out(row, db, request, lang),
    )


@router.get("/skills/")
@router.get("/skills", include_in_schema=False)
def skills(
    request: Request,
    response: Response,
    page: int = 1,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    stmt = (
        select(SkillType)
        .options(selectinload(SkillType.skills))
        .order_by(SkillType.order, SkillType.id)
    )
    return paginate(db, stmt, request, page, lambda row: skill_group_out(row, db, request, lang))


@router.get("/certificates/")
@router.get("/certificates", include_in_schema=False)
def certificates(
    request: Request,
    response: Response,
    page: int = 1,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    stmt = (
        select(Certificates)
        .options(selectinload(Certificates.technologies))
        .order_by(Certificates.id)
    )
    return paginate(
        db,
        stmt,
        request,
        page,
        lambda row: certificate_out(row, db, request, lang),
    )
