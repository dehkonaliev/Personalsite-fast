from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..i18n import get_lang, language_vary
from ..models import Post
from ..pagination import paginate
from ..presenters import post_detail_out, post_list_out

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("/")
@router.get("", include_in_schema=False)
def list_posts(
    request: Request,
    response: Response,
    page: int = 1,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    stmt = (
        select(Post)
        .where(Post.is_published.is_(True))
        .order_by(Post.created_at.desc(), Post.id.desc())
    )
    return paginate(
        db,
        stmt,
        request,
        page,
        lambda row: post_list_out(row, db, request, lang),
    )


@router.get("/{slug}/")
@router.get("/{slug}", include_in_schema=False)
def get_post(
    slug: str,
    request: Request,
    response: Response,
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
) -> dict:
    response.headers.update(language_vary(lang))
    post = (
        db.execute(
            select(Post).where(Post.slug == slug, Post.is_published.is_(True))
        )
        .scalars()
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return post_detail_out(post, db, request, lang)
