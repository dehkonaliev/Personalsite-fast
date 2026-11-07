from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from . import models  # noqa: F401
from .config import get_settings
from .database import Base, engine, get_db
from .routers import admin, main, posts, projects

settings = get_settings()
settings.media_root.mkdir(parents=True, exist_ok=True)


def _sync_project_columns() -> None:
    inspector = inspect(engine)
    if "projects_project" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("projects_project")}
    additions = {
        "live_link": "VARCHAR(200)",
        "preview_image": "VARCHAR(100)",
    }
    missing = {name: ddl for name, ddl in additions.items() if name not in existing}
    if not missing:
        return
    with engine.begin() as connection:
        for name, ddl in missing.items():
            connection.execute(
                text(f"ALTER TABLE projects_project ADD COLUMN {name} {ddl}")
            )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
        _sync_project_columns()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

allow_all_origins = "*" in settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else settings.cors_origin_list,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    settings.media_url,
    StaticFiles(directory=str(settings.media_root)),
    name="media",
)

app.include_router(main.router)
app.include_router(projects.router)
app.include_router(posts.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
