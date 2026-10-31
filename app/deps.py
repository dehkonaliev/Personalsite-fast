import secrets

from fastapi import Header, HTTPException

from .config import get_settings

settings = get_settings()


def require_admin(
    x_admin_token: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    expected = settings.admin_api_token
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin API is disabled. Set ADMIN_API_TOKEN.",
        )

    provided = x_admin_token
    if not provided and authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided = value.strip()

    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token.")
