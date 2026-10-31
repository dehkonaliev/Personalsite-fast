from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Post
from ..pagination import paginate
from ..presenters import post_detail_out, post_list_out

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("/")
@router.get("", include_in_schema=False)
def list_posts(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
) -> dict:
    stmt = (
        select(Post)
        .where(Post.is_published.is_(True))
        .order_by(Post.created_at.desc(), Post.id.desc())
    )
    return paginate(db, stmt, request, page, post_list_out)


@router.get("/{slug}/")
@router.get("/{slug}", include_in_schema=False)
def get_post(slug: str, db: Session = Depends(get_db)) -> dict:
    post = (
        db.execute(
            select(Post).where(Post.slug == slug, Post.is_published.is_(True))
        )
        .scalars()
        .first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return post_detail_out(post)
