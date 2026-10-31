from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_admin
from ..models import (
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
from ..presenters import (
    admin_activity_list,
    admin_row,
    admin_skill_list,
    admin_technology_list,
)
from ..schemas import (
    ActivityBase,
    CertificateBase,
    CertificateCreate,
    EducationBase,
    ExperienceBase,
    HomeBase,
    PostBase,
    ProjectBase,
    ProjectCreate,
    ResumeBase,
    SkillBase,
    SkillTypeBase,
    TechnologyBase,
    merge_update,
)
from ..storage import media_url, save_upload

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _get_or_404(db: Session, model: Any, item_id: int) -> Any:
    obj = db.get(model, item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return obj


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Constraint violation.") from exc


def _apply(obj: Any, data: dict[str, Any]) -> None:
    for key, value in data.items():
        setattr(obj, key, value)


def _unique_slug(db: Session, model: Any, title: str, max_length: int) -> str:
    base = slugify(title)[:max_length] or "item"
    slug = base
    counter = 1
    while db.scalar(select(model.id).where(model.slug == slug)) is not None:
        counter += 1
        suffix = f"-{counter}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
    return slug


def _technologies(db: Session, ids: list[int]) -> list[Technology]:
    unique_ids = list(dict.fromkeys(ids))
    if not unique_ids:
        return []
    technologies = db.scalars(
        select(Technology).where(Technology.id.in_(unique_ids))
    ).all()
    found = {technology.id for technology in technologies}
    missing = [technology_id for technology_id in unique_ids if technology_id not in found]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown technology ids: {missing}",
        )
    by_id = {technology.id: technology for technology in technologies}
    return [by_id[technology_id] for technology_id in unique_ids]


def _empty_resume() -> dict:
    return {
        "id": None,
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


def _home_response(db: Session, request: Request) -> dict:
    user = db.query(CustomUser).order_by(CustomUser.id).first()
    if user is None:
        data = {"id": None, **HomeBase().model_dump()}
    else:
        data = admin_row(user, request)
    data["activities"] = admin_activity_list(
        db.query(Activity).order_by(Activity.order, Activity.id).all()
    )
    return data


@router.get("/home")
def get_home(request: Request, db: Session = Depends(get_db)) -> dict:
    return _home_response(db, request)


@router.put("/home")
def put_home(
    request: Request,
    payload: HomeBase,
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(CustomUser).order_by(CustomUser.id).first()
    if user is None:
        user = CustomUser()
        db.add(user)
    _apply(user, payload.model_dump())
    _commit(db)
    return _home_response(db, request)


@router.patch("/home")
def patch_home(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(CustomUser).order_by(CustomUser.id).first()
    if user is None:
        user = CustomUser()
        db.add(user)
        data = HomeBase.model_validate(payload)
    else:
        data = merge_update(HomeBase, user, payload)
    _apply(user, data.model_dump())
    _commit(db)
    return _home_response(db, request)


@router.get("/activities")
def list_activities(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Activity).order_by(Activity.order, Activity.id).all()
    return admin_activity_list(rows)


@router.post("/activities", status_code=201)
def create_activity(
    request: Request,
    payload: ActivityBase,
    db: Session = Depends(get_db),
) -> dict:
    activity = Activity(**payload.model_dump())
    db.add(activity)
    _commit(db)
    return admin_row(activity, request)


@router.get("/activities/{item_id}")
def get_activity(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    return admin_row(_get_or_404(db, Activity, item_id), request)


@router.patch("/activities/{item_id}")
@router.put("/activities/{item_id}", include_in_schema=False)
def update_activity(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    activity = _get_or_404(db, Activity, item_id)
    data = merge_update(ActivityBase, activity, payload)
    _apply(activity, data.model_dump())
    _commit(db)
    return admin_row(activity, request)


@router.delete("/activities/{item_id}")
def delete_activity(item_id: int, db: Session = Depends(get_db)) -> dict:
    activity = _get_or_404(db, Activity, item_id)
    db.delete(activity)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/resume")
def get_resume(request: Request, db: Session = Depends(get_db)) -> dict:
    resume = db.query(Resume).order_by(Resume.id).first()
    if resume is None:
        return _empty_resume()
    return admin_row(resume, request)


@router.put("/resume")
def put_resume(
    request: Request,
    payload: ResumeBase,
    db: Session = Depends(get_db),
) -> dict:
    resume = db.query(Resume).order_by(Resume.id).first()
    if resume is None:
        resume = Resume()
        db.add(resume)
    _apply(resume, payload.model_dump())
    _commit(db)
    return admin_row(resume, request)


@router.patch("/resume")
def patch_resume(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    resume = db.query(Resume).order_by(Resume.id).first()
    if resume is None:
        resume = Resume()
        db.add(resume)
        data = ResumeBase.model_validate(payload)
    else:
        data = merge_update(ResumeBase, resume, payload)
    _apply(resume, data.model_dump())
    _commit(db)
    return admin_row(resume, request)


@router.get("/experiences")
def list_experiences(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Experience).order_by(Experience.order.desc(), Experience.id.desc()).all()
    return [admin_row(row, request) for row in rows]


@router.post("/experiences", status_code=201)
def create_experience(
    request: Request,
    payload: ExperienceBase,
    db: Session = Depends(get_db),
) -> dict:
    experience = Experience(**payload.model_dump())
    db.add(experience)
    _commit(db)
    return admin_row(experience, request)


@router.get("/experiences/{item_id}")
def get_experience(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    return admin_row(_get_or_404(db, Experience, item_id), request)


@router.patch("/experiences/{item_id}")
@router.put("/experiences/{item_id}", include_in_schema=False)
def update_experience(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    experience = _get_or_404(db, Experience, item_id)
    data = merge_update(ExperienceBase, experience, payload)
    _apply(experience, data.model_dump())
    _commit(db)
    return admin_row(experience, request)


@router.delete("/experiences/{item_id}")
def delete_experience(item_id: int, db: Session = Depends(get_db)) -> dict:
    experience = _get_or_404(db, Experience, item_id)
    db.delete(experience)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/educations")
def list_educations(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Education).order_by(Education.order.desc(), Education.id.desc()).all()
    return [admin_row(row, request) for row in rows]


@router.post("/educations", status_code=201)
def create_education(
    request: Request,
    payload: EducationBase,
    db: Session = Depends(get_db),
) -> dict:
    education = Education(**payload.model_dump())
    db.add(education)
    _commit(db)
    return admin_row(education, request)


@router.get("/educations/{item_id}")
def get_education(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    return admin_row(_get_or_404(db, Education, item_id), request)


@router.patch("/educations/{item_id}")
@router.put("/educations/{item_id}", include_in_schema=False)
def update_education(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    education = _get_or_404(db, Education, item_id)
    data = merge_update(EducationBase, education, payload)
    _apply(education, data.model_dump())
    _commit(db)
    return admin_row(education, request)


@router.delete("/educations/{item_id}")
def delete_education(item_id: int, db: Session = Depends(get_db)) -> dict:
    education = _get_or_404(db, Education, item_id)
    db.delete(education)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/skill-types")
def list_skill_types(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(SkillType)
        .options(selectinload(SkillType.skills))
        .order_by(SkillType.order, SkillType.id)
        .all()
    )
    return [
        admin_row(row, request, {"skills": admin_skill_list}) for row in rows
    ]


@router.post("/skill-types", status_code=201)
def create_skill_type(
    request: Request,
    payload: SkillTypeBase,
    db: Session = Depends(get_db),
) -> dict:
    skill_type = SkillType(**payload.model_dump())
    db.add(skill_type)
    _commit(db)
    return admin_row(skill_type, request, {"skills": admin_skill_list})


@router.get("/skill-types/{item_id}")
def get_skill_type(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    row = _get_or_404(db, SkillType, item_id)
    return admin_row(row, request, {"skills": admin_skill_list})


@router.patch("/skill-types/{item_id}")
@router.put("/skill-types/{item_id}", include_in_schema=False)
def update_skill_type(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_or_404(db, SkillType, item_id)
    data = merge_update(SkillTypeBase, row, payload)
    _apply(row, data.model_dump())
    _commit(db)
    return admin_row(row, request, {"skills": admin_skill_list})


@router.delete("/skill-types/{item_id}")
def delete_skill_type(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = _get_or_404(db, SkillType, item_id)
    db.delete(row)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/skills")
def list_skills(
    request: Request,
    type_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(Skill).order_by(Skill.order, Skill.id)
    if type_id is not None:
        stmt = stmt.where(Skill.type_id == type_id)
    return [admin_row(row, request) for row in db.scalars(stmt).all()]


@router.post("/skills", status_code=201)
def create_skill(
    request: Request,
    payload: SkillBase,
    db: Session = Depends(get_db),
) -> dict:
    skill = Skill(**payload.model_dump())
    db.add(skill)
    _commit(db)
    return admin_row(skill, request)


@router.get("/skills/{item_id}")
def get_skill(item_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    return admin_row(_get_or_404(db, Skill, item_id), request)


@router.patch("/skills/{item_id}")
@router.put("/skills/{item_id}", include_in_schema=False)
def update_skill(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    skill = _get_or_404(db, Skill, item_id)
    data = merge_update(SkillBase, skill, payload)
    _apply(skill, data.model_dump())
    _commit(db)
    return admin_row(skill, request)


@router.delete("/skills/{item_id}")
def delete_skill(item_id: int, db: Session = Depends(get_db)) -> dict:
    skill = _get_or_404(db, Skill, item_id)
    db.delete(skill)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/certificates")
def list_certificates(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(Certificates)
        .options(selectinload(Certificates.technologies))
        .order_by(Certificates.id)
        .all()
    )
    return [
        admin_row(row, request, {"technologies": admin_technology_list})
        for row in rows
    ]


@router.post("/certificates", status_code=201)
def create_certificate(
    request: Request,
    payload: CertificateCreate,
    db: Session = Depends(get_db),
) -> dict:
    data = payload.model_dump(exclude={"technologies"})
    certificate = Certificates(**data)
    certificate.technologies = _technologies(db, payload.technologies)
    db.add(certificate)
    _commit(db)
    return admin_row(certificate, request, {"technologies": admin_technology_list})


@router.get("/certificates/{item_id}")
def get_certificate(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    row = _get_or_404(db, Certificates, item_id)
    return admin_row(row, request, {"technologies": admin_technology_list})


@router.patch("/certificates/{item_id}")
@router.put("/certificates/{item_id}", include_in_schema=False)
def update_certificate(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_or_404(db, Certificates, item_id)
    payload = dict(payload)
    technology_ids = payload.pop("technologies", None)
    data = merge_update(CertificateBase, row, payload)
    _apply(row, data.model_dump())
    if technology_ids is not None:
        row.technologies = _technologies(db, technology_ids)
    _commit(db)
    return admin_row(row, request, {"technologies": admin_technology_list})


@router.delete("/certificates/{item_id}")
def delete_certificate(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = _get_or_404(db, Certificates, item_id)
    db.delete(row)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/projects")
def list_projects(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(Project)
        .options(selectinload(Project.technologies))
        .order_by(Project.created_at.desc(), Project.id.desc())
        .all()
    )
    return [
        admin_row(row, request, {"technologies": admin_technology_list})
        for row in rows
    ]


@router.post("/projects", status_code=201)
def create_project(
    request: Request,
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> dict:
    data = payload.model_dump(exclude={"technologies"})
    if not data["slug"].strip():
        data["slug"] = _unique_slug(db, Project, payload.title, 500)
    project = Project(**data)
    project.technologies = _technologies(db, payload.technologies)
    db.add(project)
    _commit(db)
    return admin_row(project, request, {"technologies": admin_technology_list})


@router.get("/projects/{item_id}")
def get_project(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    row = _get_or_404(db, Project, item_id)
    return admin_row(row, request, {"technologies": admin_technology_list})


@router.patch("/projects/{item_id}")
@router.put("/projects/{item_id}", include_in_schema=False)
def update_project(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_or_404(db, Project, item_id)
    payload = dict(payload)
    technology_ids = payload.pop("technologies", None)
    if "slug" in payload and not str(payload["slug"]).strip():
        payload.pop("slug")
    data = merge_update(ProjectBase, row, payload)
    _apply(row, data.model_dump())
    if technology_ids is not None:
        row.technologies = _technologies(db, technology_ids)
    _commit(db)
    return admin_row(row, request, {"technologies": admin_technology_list})


@router.delete("/projects/{item_id}")
def delete_project(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = _get_or_404(db, Project, item_id)
    db.delete(row)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/posts")
def list_posts(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Post).order_by(Post.created_at.desc(), Post.id.desc()).all()
    return [admin_row(row, request) for row in rows]


@router.post("/posts", status_code=201)
def create_post(
    request: Request,
    payload: PostBase,
    db: Session = Depends(get_db),
) -> dict:
    data = payload.model_dump()
    if not data["slug"].strip():
        data["slug"] = _unique_slug(db, Post, payload.title, 1000)
    post = Post(**data)
    db.add(post)
    _commit(db)
    return admin_row(post, request)


@router.get("/posts/{item_id}")
def get_post(item_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    return admin_row(_get_or_404(db, Post, item_id), request)


@router.patch("/posts/{item_id}")
@router.put("/posts/{item_id}", include_in_schema=False)
def update_post(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_or_404(db, Post, item_id)
    payload = dict(payload)
    if "slug" in payload and not str(payload["slug"]).strip():
        payload.pop("slug")
    data = merge_update(PostBase, row, payload)
    _apply(row, data.model_dump())
    _commit(db)
    return admin_row(row, request)


@router.delete("/posts/{item_id}")
def delete_post(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = _get_or_404(db, Post, item_id)
    db.delete(row)
    _commit(db)
    return {"detail": "Deleted."}


@router.get("/technologies")
def list_technologies(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Technology).order_by(Technology.id).all()
    return [admin_row(row, request) for row in rows]


@router.post("/technologies", status_code=201)
def create_technology(
    request: Request,
    payload: TechnologyBase,
    db: Session = Depends(get_db),
) -> dict:
    technology = Technology(**payload.model_dump())
    db.add(technology)
    _commit(db)
    return admin_row(technology, request)


@router.get("/technologies/{item_id}")
def get_technology(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> dict:
    return admin_row(_get_or_404(db, Technology, item_id), request)


@router.patch("/technologies/{item_id}")
@router.put("/technologies/{item_id}", include_in_schema=False)
def update_technology(
    item_id: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    row = _get_or_404(db, Technology, item_id)
    data = merge_update(TechnologyBase, row, payload)
    _apply(row, data.model_dump())
    _commit(db)
    return admin_row(row, request)


@router.delete("/technologies/{item_id}")
def delete_technology(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = _get_or_404(db, Technology, item_id)
    db.delete(row)
    _commit(db)
    return {"detail": "Deleted."}


@router.post("/uploads", status_code=201)
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Query(default="uploads", max_length=100),
) -> dict:
    path = save_upload(file, folder)
    return {"path": path, "url": media_url(request, path)}
