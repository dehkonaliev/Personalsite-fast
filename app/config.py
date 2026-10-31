from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CORS_ORIGINS = (
    "https://dehkonaliev.uz,"
    "https://www.dehkonaliev.uz,"
    "https://personal-site-frontend-sepia.vercel.app,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)


def _normalize_database_url(url: str) -> str:
    """Return a SQLAlchemy URL that works with psycopg 3."""
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Personal Site API"
    debug: bool = False
    api_prefix: str = "/api"

    database_url: str = ""
    postgres_url: str = ""
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 300
    auto_create_tables: bool = True

    public_base_url: str = ""
    fastapi_public_url: str = ""
    media_url: str = "/media/"
    media_root: Path = BASE_DIR / "media"

    cors_origins: str = DEFAULT_CORS_ORIGINS
    admin_api_token: str = ""
    max_upload_mb: int = 25
    page_size: int = 10

    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str = ""
    s3_public_base_url: str = ""
    s3_prefix: str = "media"
    s3_use_ssl: bool = True
    s3_addressing_style: str = "auto"
    s3_acl: str = ""
    s3_presigned_urls: bool = False
    s3_presign_expires: int = 3600

    @field_validator("media_url")
    @classmethod
    def _ensure_media_url(cls, value: str) -> str:
        value = value.strip() or "/media/"
        if not value.startswith("/"):
            value = "/" + value
        if not value.endswith("/"):
            value += "/"
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def raw_database_url(self) -> str:
        return self.database_url or self.postgres_url

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.raw_database_url:
            return _normalize_database_url(self.raw_database_url)
        return f"sqlite:///{(BASE_DIR / 'personal_site.db').as_posix()}"

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_database_url.startswith("sqlite")

    @property
    def s3_enabled(self) -> bool:
        return bool(self.s3_bucket)

    @property
    def site_base_url(self) -> str:
        return self.public_base_url or self.fastapi_public_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
