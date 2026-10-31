from datetime import date, datetime, timezone
from typing import Any, Callable

from fastapi import Request
from sqlalchemy import inspect
from sqlalchemy.orm import Session

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

FILE_FIELDS = {"photo", "resume_file", "image", "certification", "file", "photo_overview"}


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def activity_out(activity: Activity) -> dict:
    return {"title": activity.title, "context": activity.context}


def home_out(db: Session, request: Request) -> dict:
    user = db.query(CustomUser).order_by(CustomUser.id).first()
    activities = (
        db.query(Activity).order_by(Activity.order, Activity.id).limit(3).all()
    )
    return {
        "first_name": user.first_name if user else "",
        "last_name": user.last_name if user else "",
        "job_title": user.job_title if user else "",
        "heading_activity": user.heading_activity if user else "",
        "home_context": user.home_context if user else "",
        "off_board": user.off_board if user else "",
        "photo": media_url(request, user.photo) if user else None,
        "activities": [activity_out(activity) for activity in activities],
    }


def resume_out(resume: Resume | None, request: Request) -> dict:
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
        "location": resume.location,
        "summary": resume.summary,
        "email": resume.email,
        "resume_file": media_url(request, resume.resume_file),
        "website_url": resume.website_url,
        "github_url": resume.github_url,
        "linkedin_url": resume.linkedin_url,
        "telegram_url": resume.telegram_url,
        "image": media_url(request, resume.image),
    }


def education_out(education: Education, request: Request) -> dict:
    return {
        "id": education.id,
        "field": education.field,
        "edu_place": education.edu_place,
        "from_date": education.from_date.isoformat(),
        "to_date": education.to_date.isoformat(),
        "what_learnt": education.what_learnt,
        "certification": media_url(request, education.certification),
    }


def experience_out(experience: Experience, request: Request) -> dict:
    return {
        "id": experience.id,
        "job": experience.job,
        "company": experience.company,
        "activity": experience.activity,
        "from_date": experience.from_date.isoformat(),
        "to_date": experience.to_date.isoformat(),
        "location": experience.location,
    }


def skill_out(skill: Skill) -> dict:
    return {"name": skill.name}


def skill_group_out(group: SkillType, request: Request) -> dict:
    skills = sorted(group.skills, key=lambda item: (item.order, item.id))
    return {"name": group.name, "skills": [skill_out(skill) for skill in skills]}


def technology_out(technology: Technology) -> dict:
    return {"id": technology.id, "name": technology.name}


def certificate_out(certificate: Certificates, request: Request) -> dict:
    return {
        "id": certificate.id,
        "name": certificate.name,
        "issued_by": certificate.issued_by,
        "what_learnt": certificate.what_learnt,
        "created_at": iso_z(certificate.created_at),
        "link": certificate.link,
        "file": media_url(request, certificate.file),
        "photo_overview": media_url(request, certificate.photo_overview),
        "technologies": [
            technology_out(technology) for technology in certificate.technologies
        ],
    }


def project_list_out(project: Project, request: Request) -> dict:
    return {
        "id": project.id,
        "title": project.title,
        "slug": project.slug,
        "summary": project.summary,
        "technologies": [
            technology_out(technology) for technology in project.technologies
        ],
        "github_link": project.github_link,
        "created_at": iso_z(project.created_at),
    }


def project_detail_out(project: Project, request: Request) -> dict:
    data = project_list_out(project, request)
    data["context"] = project.context
    return data


def post_list_out(post: Post) -> dict:
    return {
        "id": post.id,
        "slug": post.slug,
        "title": post.title,
        "summary": post.summary,
        "created_at": iso_z(post.created_at),
    }


def post_detail_out(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "created_at": iso_z(post.created_at),
        "is_published": post.is_published,
        "slug": post.slug,
        "body": post.body,
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
    return [technology_out(technology) for technology in technologies]


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
