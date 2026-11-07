from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ORM_CONFIG = ConfigDict(from_attributes=True, populate_by_name=True)


class HomeBase(BaseModel):
    model_config = ORM_CONFIG

    first_name: str = Field(default="", max_length=30)
    last_name: str = Field(default="", max_length=30)
    job_title: str = Field(default="", max_length=500)
    heading_activity: str = Field(default="", max_length=2000)
    home_context: str = Field(default="", max_length=2000)
    off_board: str = Field(default="", max_length=2000)
    photo: str | None = Field(default=None, max_length=100)


class ActivityBase(BaseModel):
    model_config = ORM_CONFIG

    title: str = Field(max_length=200)
    context: str = Field(max_length=2000)
    order: int = Field(default=0, ge=0)


class ResumeBase(BaseModel):
    model_config = ORM_CONFIG

    location: str = Field(max_length=300)
    summary: str = Field(max_length=3000)
    email: EmailStr
    resume_file: str | None = Field(default=None, max_length=100)
    website_url: str | None = Field(default=None, max_length=200)
    github_url: str | None = Field(default=None, max_length=200)
    linkedin_url: str | None = Field(default=None, max_length=200)
    telegram_url: str | None = Field(default=None, max_length=200)
    image: str | None = Field(default=None, max_length=100)


class ExperienceBase(BaseModel):
    model_config = ORM_CONFIG

    job: str = Field(max_length=200)
    company: str = Field(max_length=200)
    activity: str | None = Field(default=None, max_length=2000)
    from_date: date
    to_date: date
    location: str | None = Field(default=None, max_length=300)
    order: int = Field(default=0, ge=0)


class SkillTypeBase(BaseModel):
    model_config = ORM_CONFIG

    name: str = Field(max_length=100)
    order: int = Field(default=0, ge=0)


class SkillBase(BaseModel):
    model_config = ORM_CONFIG

    type_id: int = Field(alias="type")
    name: str = Field(max_length=50)
    order: int = Field(default=0, ge=0)


class EducationBase(BaseModel):
    model_config = ORM_CONFIG

    field: str = Field(max_length=100)
    edu_place: str = Field(max_length=200)
    from_date: date
    to_date: date
    what_learnt: str = Field(max_length=2000)
    certification: str | None = Field(default=None, max_length=100)
    order: int = Field(default=0, ge=0)


class CertificateBase(BaseModel):
    model_config = ORM_CONFIG

    name: str = Field(max_length=500)
    issued_by: str | None = Field(default=None, max_length=500)
    what_learnt: str = Field(max_length=3000)
    link: str | None = Field(default=None, max_length=200)
    file: str | None = Field(default=None, max_length=100)
    photo_overview: str | None = Field(default=None, max_length=100)


class CertificateCreate(CertificateBase):
    technologies: list[int] = Field(default_factory=list)


class ProjectBase(BaseModel):
    model_config = ORM_CONFIG

    title: str = Field(max_length=500)
    summary: str = Field(max_length=500)
    github_link: str | None = Field(default=None, max_length=200)
    live_link: str | None = Field(default=None, max_length=200)
    preview_image: str | None = Field(default=None, max_length=100)
    is_published: bool = False
    slug: str = Field(default="", max_length=500)
    context: str = ""


class ProjectCreate(ProjectBase):
    technologies: list[int] = Field(default_factory=list)


class PostBase(BaseModel):
    model_config = ORM_CONFIG

    title: str = Field(max_length=1000)
    summary: str = Field(max_length=3000)
    is_published: bool = False
    slug: str = Field(default="", max_length=1000)
    body: str | None = None


class TechnologyBase(BaseModel):
    model_config = ORM_CONFIG

    name: str = Field(max_length=50)


def merge_update(schema: type[BaseModel], obj: Any, payload: dict[str, Any]) -> BaseModel:
    """Validate a partial payload against the current values of an ORM object."""
    current = schema.model_validate(obj).model_dump()
    current.update(payload)
    return schema.model_validate(current)
