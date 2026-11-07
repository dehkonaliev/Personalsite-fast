from datetime import date, datetime, timezone
from typing import Any, Callable

from fastapi import Request
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .i18n import DEFAULT_LANG
from .models import (
    Activity,
    Certificates,
    CustomUser,
    Education,
    Experience,
    Post,
    Project,
    Resume,
    Skill,
    SkillType,
    Technology,
)
from .storage import media_url
from .translations import translate

FILE_FIELDS = {
    "photo",
    "resume_file",
    "image",
    "certification",
    "file",
    "photo_overview",
    "preview_image",
}


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _localized(
    db: Session,
    request: Request,
    resource: str,
    object_id: int,
    field: str,
    default: str | None,
    lang: str,
) -> str | None:
    return translate(db, request, resource, object_id, field, default, lang)


def activity_out(activity: Activity, db: Session, request: Request, lang: str) -> dict:
    return {
        "title": _localized(db, request, "activities", activity.id, "title", activity.title, lang),
        "context": _localized(db, request, "activities", activity.id, "context", activity.context, lang),
    }


def home_out(db: Session, request: Request, lang: str = DEFAULT_LANG) -> dict:
    user = db.query(CustomUser).order_by(CustomUser.id).first()
    activities = (
        db.query(Activity).order_by(Activity.order, Activity.id).limit(3).all()
    )
    if user is None:
        return {
            "first_name": "",
            "last_name": "",
            "job_title": "",
            "heading_activity": "",
            "home_context": "",
            "off_board": "",
            "photo": None,
            "activities": [],
        }
    return {
        "first_name": _localized(db, request, "home", 0, "first_name", user.first_name, lang),
        "last_name": _localized(db, request, "home", 0, "last_name", user.last_name, lang),
        "job_title": _localized(db, request, "home", 0, "job_title", user.job_title, lang),
        "heading_activity": _localized(
            db, request, "home", 0, "heading_activity", user.heading_activity, lang
        ),
        "home_context": _localized(
            db, request, "home", 0, "home_context", user.home_context, lang
        ),
        "off_board": _localized(db, request, "home", 0, "off_board", user.off_board, lang),
        "photo": media_url(request, user.photo),
        "activities": [activity_out(activity, db, request, lang) for activity in activities],
    }


def resume_out(
    db: Session, resume: Resume | None, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    if resume is None:
        return {
            "location": "",
            "summary": "",
            "email": "",
            "resume_file": None,
            "website_url": None,
            "github_url": None,
            "linkedin_url": None,
            "telegram_url": None,
            "image": None,
        }
    return {
        "location": _localized(db, request, "resume", 0, "location", resume.location, lang),
        "summary": _localized(db, request, "resume", 0, "summary", resume.summary, lang),
        "email": resume.email,
        "resume_file": media_url(request, resume.resume_file),
        "website_url": resume.website_url,
        "github_url": resume.github_url,
        "linkedin_url": resume.linkedin_url,
        "telegram_url": resume.telegram_url,
        "image": media_url(request, resume.image),
    }


def education_out(
    education: Education, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": education.id,
        "field": _localized(db, request, "educations", education.id, "field", education.field, lang),
        "edu_place": _localized(
            db, request, "educations", education.id, "edu_place", education.edu_place, lang
        ),
        "from_date": education.from_date.isoformat(),
        "to_date": education.to_date.isoformat(),
        "what_learnt": _localized(
            db, request, "educations", education.id, "what_learnt", education.what_learnt, lang
        ),
        "certification": media_url(request, education.certification),
    }


def experience_out(
    experience: Experience, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": experience.id,
        "job": _localized(db, request, "experiences", experience.id, "job", experience.job, lang),
        "company": _localized(
            db, request, "experiences", experience.id, "company", experience.company, lang
        ),
        "activity": _localized(
            db, request, "experiences", experience.id, "activity", experience.activity, lang
        ),
        "from_date": experience.from_date.isoformat(),
        "to_date": experience.to_date.isoformat(),
        "location": _localized(
            db, request, "experiences", experience.id, "location", experience.location, lang
        ),
    }


def skill_out(skill: Skill, db: Session, request: Request, lang: str = DEFAULT_LANG) -> dict:
    return {
        "name": _localized(db, request, "skills", skill.id, "name", skill.name, lang),
    }


def skill_group_out(
    group: SkillType, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    skills = sorted(group.skills, key=lambda item: (item.order, item.id))
    return {
        "name": _localized(db, request, "skill-types", group.id, "name", group.name, lang),
        "skills": [skill_out(skill, db, request, lang) for skill in skills],
    }


def technology_out(technology: Technology, db: Session, request: Request, lang: str = DEFAULT_LANG) -> dict:
    return {"id": technology.id, "name": _localized(db, request, "technologies", technology.id, "name", technology.name, lang)}


def certificate_out(
    certificate: Certificates, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": certificate.id,
        "name": _localized(
            db, request, "certificates", certificate.id, "name", certificate.name, lang
        ),
        "issued_by": _localized(
            db, request, "certificates", certificate.id, "issued_by", certificate.issued_by, lang
        ),
        "what_learnt": _localized(
            db, request, "certificates", certificate.id, "what_learnt", certificate.what_learnt, lang
        ),
        "created_at": iso_z(certificate.created_at),
        "link": certificate.link,
        "file": media_url(request, certificate.file),
        "photo_overview": media_url(request, certificate.photo_overview),
        "technologies": [
            technology_out(technology, db, request, lang) for technology in certificate.technologies
        ],
    }


def project_list_out(
    project: Project, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": project.id,
        "title": _localized(db, request, "projects", project.id, "title", project.title, lang),
        "slug": project.slug,
        "summary": _localized(
            db, request, "projects", project.id, "summary", project.summary, lang
        ),
        "technologies": [
            technology_out(technology, db, request, lang) for technology in project.technologies
        ],
        "github_link": project.github_link,
        "live_link": project.live_link,
        "preview_image": media_url(request, project.preview_image),
        "created_at": iso_z(project.created_at),
    }


def project_detail_out(
    project: Project, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    data = project_list_out(project, db, request, lang)
    data["context"] = _localized(
        db, request, "projects", project.id, "context", project.context, lang
    )
    return data


def post_list_out(
    post: Post, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": post.id,
        "slug": post.slug,
        "title": _localized(db, request, "posts", post.id, "title", post.title, lang),
        "summary": _localized(db, request, "posts", post.id, "summary", post.summary, lang),
        "created_at": iso_z(post.created_at),
    }


def post_detail_out(
    post: Post, db: Session, request: Request, lang: str = DEFAULT_LANG
) -> dict:
    return {
        "id": post.id,
        "title": _localized(db, request, "posts", post.id, "title", post.title, lang),
        "summary": _localized(db, request, "posts", post.id, "summary", post.summary, lang),
        "created_at": iso_z(post.created_at),
        "is_published": post.is_published,
        "slug": post.slug,
        "body": _localized(db, request, "posts", post.id, "body", post.body, lang),
    }


def _admin_scalar(name: str, value: Any, request: Request) -> Any:
    if name in FILE_FIELDS:
        return media_url(request, value)
    if isinstance(value, datetime):
        return iso_z(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def admin_row(
    obj: Any,
    request: Request,
    relationships: dict[str, Callable[[Any], Any]] | None = None,
) -> dict:
    data: dict[str, Any] = {}
    for attribute in inspect(obj).mapper.column_attrs:
        data[attribute.key] = _admin_scalar(
            attribute.key, getattr(obj, attribute.key), request
        )
    if relationships:
        for name, serializer in relationships.items():
            data[name] = serializer(getattr(obj, name))
    return data


def admin_technology_list(technologies: list[Technology]) -> list[dict]:
    return [{"id": technology.id, "name": technology.name} for technology in technologies]


def admin_skill_list(skills: list[Skill]) -> list[dict]:
    return [
        {"id": skill.id, "type_id": skill.type_id, "name": skill.name, "order": skill.order}
        for skill in sorted(skills, key=lambda item: (item.order, item.id))
    ]


def admin_activity_list(activities: list[Activity]) -> list[dict]:
    return [
        {"id": activity.id, "title": activity.title, "context": activity.context, "order": activity.order}
        for activity in activities
    ]
