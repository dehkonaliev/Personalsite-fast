from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

BigIntPK = BigInteger().with_variant(Integer, "sqlite")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


project_technologies = Table(
    "projects_project_technologies",
    Base.metadata,
    Column(
        "id",
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    Column(
        "project_id",
        BigInteger,
        ForeignKey("projects_project.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "technology_id",
        BigInteger,
        ForeignKey("projects_technology.id", ondelete="CASCADE"),
        nullable=False,
    ),
)

certificate_technologies = Table(
    "users_certificates_technologies",
    Base.metadata,
    Column(
        "id",
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
    Column(
        "certificates_id",
        BigInteger,
        ForeignKey("users_certificates.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "technology_id",
        BigInteger,
        ForeignKey("projects_technology.id", ondelete="CASCADE"),
        nullable=False,
    ),
)


class Technology(Base):
    __tablename__ = "projects_technology"
    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    projects: Mapped[list["Project"]] = relationship(
        secondary=project_technologies, back_populates="technologies"
    )
    certificates: Mapped[list["Certificates"]] = relationship(
        secondary=certificate_technologies, back_populates="technologies"
    )


class Project(Base):
    __tablename__ = "projects_project"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    github_link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")

    technologies: Mapped[list["Technology"]] = relationship(
        secondary=project_technologies,
        back_populates="projects",
        order_by="Technology.id",
    )


class Post(Base):
    __tablename__ = "blog_post"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    summary: Mapped[str] = mapped_column(String(3000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    slug: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)


class CustomUser(Base):
    __tablename__ = "users_customuser"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    heading_activity: Mapped[str] = mapped_column(String(2000), nullable=False)
    home_context: Mapped[str] = mapped_column(String(2000), nullable=False)
    off_board: Mapped[str] = mapped_column(String(2000), nullable=False)
    photo: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Activity(Base):
    __tablename__ = "users_activity"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    context: Mapped[str] = mapped_column(String(2000), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Resume(Base):
    __tablename__ = "users_resume"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(String(3000), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    resume_file: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telegram_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Experience(Base):
    __tablename__ = "users_experience"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    job: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    activity: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SkillType(Base):
    __tablename__ = "users_skilltype"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    skills: Mapped[list["Skill"]] = relationship(
        back_populates="skill_type",
        cascade="all, delete-orphan",
        order_by="Skill.order",
    )


class Skill(Base):
    __tablename__ = "users_skill"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users_skilltype.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    skill_type: Mapped["SkillType"] = relationship(back_populates="skills")


class Education(Base):
    __tablename__ = "users_education"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    edu_place: Mapped[str] = mapped_column(String(200), nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    what_learnt: Mapped[str] = mapped_column(String(2000), nullable=False)
    certification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Certificates(Base):
    __tablename__ = "users_certificates"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    issued_by: Mapped[str | None] = mapped_column(String(500), nullable=True)
    what_learnt: Mapped[str] = mapped_column(String(3000), nullable=False)
    link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    file: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_overview: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, server_default=func.now()
    )

    technologies: Mapped[list["Technology"]] = relationship(
        secondary=certificate_technologies,
        back_populates="certificates",
        order_by="Technology.id",
    )


class Translation(Base):
    __tablename__ = "content_translation"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    object_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")

    __table_args__ = (
        UniqueConstraint(
            "resource", "object_id", "field", "lang", name="uq_translation_slot"
        ),
    )
