from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from .i18n import DEFAULT_LANG, SUPPORTED_LANGS
from .models import Translation

# Resources and the fields that may be translated, keyed the same way the
# admin API exposes them.
TRANSLATABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "home": ("first_name", "last_name", "job_title", "heading_activity",
             "home_context", "off_board"),
    "resume": ("location", "summary"),
    "activities": ("title", "context"),
    "experiences": ("job", "company", "activity", "location"),
    "educations": ("field", "edu_place", "what_learnt"),
    "skill-types": ("name",),
    "skills": ("name",),
    "certificates": ("name", "issued_by", "what_learnt"),
    "projects": ("title", "summary", "context"),
    "posts": ("title", "summary", "body"),
    "technologies": ("name",),
}


def _cache(request: Request) -> dict[tuple[str, int, str, str], str | None]:
    cache = getattr(request.state, "translation_cache", None)
    if cache is None:
        cache = {}
        request.state.translation_cache = cache
    return cache


def translate(
    db: Session,
    request: Request,
    resource: str,
    object_id: int,
    field: str,
    default: str | None,
    lang: str,
) -> str | None:
    """Return the localized value or fall back to the stored base value."""
    if not default or lang == DEFAULT_LANG:
        return default
    fields = TRANSLATABLE_FIELDS.get(resource)
    if not fields or field not in fields:
        return default

    cache = _cache(request)
    key = (resource, object_id, field, lang)
    if key not in cache:
        row = (
            db.query(Translation)
            .filter(
                Translation.resource == resource,
                Translation.object_id == object_id,
                Translation.field == field,
                Translation.lang == lang,
            )
            .first()
        )
        cache[key] = row.value if row else None
    value = cache[key]
    return value if value else default


def get_translations(db: Session, resource: str, object_id: int) -> dict[str, dict[str, str]]:
    fields = TRANSLATABLE_FIELDS.get(resource)
    if fields is None:
        raise HTTPException(status_code=404, detail="Unknown translation resource.")
    rows = (
        db.query(Translation)
        .filter(
            Translation.resource == resource,
            Translation.object_id == object_id,
        )
        .all()
    )
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        result.setdefault(row.field, {})[row.lang] = row.value
    return result


def list_translations(db: Session, resource: str) -> list[dict[str, Any]]:
    if resource not in TRANSLATABLE_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown translation resource.")
    rows = (
        db.query(Translation)
        .filter(Translation.resource == resource)
        .order_by(Translation.object_id, Translation.field, Translation.lang)
        .all()
    )
    return [
        {
            "object_id": row.object_id,
            "field": row.field,
            "lang": row.lang,
            "value": row.value,
        }
        for row in rows
    ]


def save_translations(
    db: Session,
    resource: str,
    object_id: int,
    payload: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    fields = TRANSLATABLE_FIELDS.get(resource)
    if fields is None:
        raise HTTPException(status_code=404, detail="Unknown translation resource.")

    for field, by_lang in payload.items():
        if field not in fields or not isinstance(by_lang, dict):
            continue
        for lang, value in by_lang.items():
            if lang not in SUPPORTED_LANGS or lang == DEFAULT_LANG:
                continue
            text = (value or "").strip()
            existing = (
                db.query(Translation)
                .filter(
                    Translation.resource == resource,
                    Translation.object_id == object_id,
                    Translation.field == field,
                    Translation.lang == lang,
                )
                .first()
            )
            if text:
                if existing is None:
                    db.add(
                        Translation(
                            resource=resource,
                            object_id=object_id,
                            field=field,
                            lang=lang,
                            value=text,
                        )
                    )
                else:
                    existing.value = text
            elif existing is not None:
                db.delete(existing)
    db.commit()
    return get_translations(db, resource, object_id)


def delete_translations(db: Session, resource: str, object_id: int) -> None:
    db.query(Translation).filter(
        Translation.resource == resource,
        Translation.object_id == object_id,
    ).delete(synchronize_session=False)
