from __future__ import annotations

import re
import uuid
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

from fastapi import HTTPException, Request, UploadFile

from .config import get_settings

settings = get_settings()

_SAFE_FOLDER = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-/]*$")


def _clean_folder(folder: str) -> str:
    folder = (folder or "uploads").strip().strip("/")
    if not folder or not _SAFE_FOLDER.match(folder) or ".." in folder:
        raise HTTPException(status_code=400, detail="Invalid upload folder.")
    return folder


def _extension(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if not suffix or len(suffix) > 10 or not re.fullmatch(r"\.[a-z0-9]+", suffix):
        return ""
    return suffix


def _s3_key(relative_path: str) -> str:
    prefix = settings.s3_prefix.strip("/")
    return f"{prefix}/{relative_path}" if prefix else relative_path


@lru_cache
def _s3_client():
    import boto3
    from botocore.config import Config

    config_kwargs: dict = {"signature_version": "s3v4"}
    if settings.s3_addressing_style != "auto":
        config_kwargs["s3"] = {"addressing_style": settings.s3_addressing_style}

    client_kwargs: dict = {
        "region_name": settings.s3_region,
        "endpoint_url": settings.s3_endpoint_url or None,
        "use_ssl": settings.s3_use_ssl,
        "config": Config(**config_kwargs),
    }
    if settings.s3_access_key_id:
        client_kwargs["aws_access_key_id"] = settings.s3_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key

    return boto3.client("s3", **client_kwargs)


def save_upload(upload: UploadFile, folder: str = "uploads") -> str:
    """Persist an upload and return the path stored in the database."""
    folder = _clean_folder(folder)
    content = upload.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is larger than {settings.max_upload_mb} MB.",
        )

    relative_path = f"{folder}/{uuid.uuid4().hex}{_extension(upload.filename)}"

    if settings.s3_enabled:
        extra_args = {"ContentType": upload.content_type or "application/octet-stream"}
        if settings.s3_acl:
            extra_args["ACL"] = settings.s3_acl
        _s3_client().put_object(
            Bucket=settings.s3_bucket,
            Key=_s3_key(relative_path),
            Body=content,
            **extra_args,
        )
    else:
        target = settings.media_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    return relative_path


def _default_s3_public_url(key: str) -> str:
    if settings.s3_public_base_url:
        return f"{settings.s3_public_base_url.rstrip('/')}/{quote(key)}"

    if settings.s3_endpoint_url:
        endpoint = settings.s3_endpoint_url.rstrip("/")
        if settings.s3_addressing_style == "virtual":
            parts = urlsplit(endpoint)
            return f"{parts.scheme}://{settings.s3_bucket}.{parts.netloc}/{quote(key)}"
        return f"{endpoint}/{settings.s3_bucket}/{quote(key)}"

    region = settings.s3_region or "us-east-1"
    return f"https://{settings.s3_bucket}.s3.{region}.amazonaws.com/{quote(key)}"


def _presigned_url(key: str) -> str:
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=settings.s3_presign_expires,
    )


def _base_url(request: Request | None) -> str:
    if settings.site_base_url:
        return settings.site_base_url.rstrip("/") + "/"
    if request is not None:
        return str(request.base_url)
    return "http://localhost:8000/"


def media_url(request: Request | None, value: str | None) -> str | None:
    """Turn a stored file path into a browser-usable absolute URL."""
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value

    if settings.s3_enabled:
        key = _s3_key(value.lstrip("/"))
        if settings.s3_presigned_urls:
            return _presigned_url(key)
        return _default_s3_public_url(key)

    base = _base_url(request)
    return urljoin(base, settings.media_url.lstrip("/") + value.lstrip("/"))
