# Personal Site API

Backend API and content management service for **[dehkonaliev.uz](https://dehkonaliev.uz)** — a personal portfolio and blog platform.

Built with FastAPI, SQLAlchemy 2, and Pydantic v2, the service exposes a public read API for the frontend and a token-protected admin API for managing site content. It works out of the box with SQLite for local development and PostgreSQL (Neon) in production, and can store media on the local filesystem or any S3-compatible bucket.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red)

---

## Features

- **Public content API** for home/profile data, resume, experience, education, skills, certificates, projects, and blog posts.
- **Admin CMS API** with full CRUD for every content type, protected by a shared admin token.
- **Pagination** with a Django REST Framework–compatible response envelope (`count`, `next`, `previous`, `results`).
- **Flexible storage** — local disk (`/media/`) or S3-compatible object storage (AWS S3, Cloudflare R2, DigitalOcean Spaces, MinIO), with optional presigned URLs.
- **Automatic slugs** generated from titles for projects and posts.
- **Database portability** — SQLite for development, PostgreSQL for production, with automatic `postgres://` → `postgresql+psycopg://` URL normalization.
- **Health check** endpoint that verifies database connectivity.
- **Interactive docs** at `/docs` and `/redoc`.

---

## Tech Stack

| Layer       | Technology                              |
| ----------- | --------------------------------------- |
| Framework   | FastAPI                                 |
| ASGI server | Uvicorn                                 |
| ORM         | SQLAlchemy 2.0                          |
| Validation  | Pydantic v2 / pydantic-settings         |
| Database    | PostgreSQL (psycopg 3) / SQLite         |
| Storage     | Local filesystem / boto3 (S3-compatible)|
| Packaging   | uv + `pyproject.toml`                   |
| Deployment  | FastAPI Cloud                           |

---

## Project Structure

```
fast-api/
├── app/
│   ├── main.py          # Application factory, CORS, lifespan, media mount
│   ├── config.py        # Pydantic settings and derived properties
│   ├── database.py      # Engine, session factory, DB dependency
│   ├── models.py        # SQLAlchemy models and relationship tables
│   ├── schemas.py       # Request schemas and partial-update helpers
│   ├── presenters.py    # Response serializers (public and admin)
│   ├── pagination.py    # DRF-compatible paginator
│   ├── deps.py          # Admin token authentication dependency
│   ├── storage.py       # Upload handling (local + S3)
│   └── routers/
│       ├── main.py      # Profile, resume, experience, education, skills, certificates
│       ├── projects.py  # Public projects
│       ├── posts.py     # Public blog posts
│       └── admin.py     # Protected CMS endpoints and uploads
├── media/               # Local upload directory (gitignored)
├── main.py              # ASGI entrypoint (`app`)
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- PostgreSQL (optional — SQLite is used by default)

### Installation

```bash
git clone <repository-url>
cd fast-api

uv sync            # installs runtime + dev dependencies
```

Or with pip:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and adjust the values:

```bash
cp .env.example .env
```

At minimum, set a strong `ADMIN_API_TOKEN`. All other values have sensible defaults.

### Run

```bash
uv run fastapi dev main.py
# or
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

---

## Configuration

Settings are read from environment variables or `.env` via `pydantic-settings` (`app/config.py`).

| Variable                | Default                | Description                                                        |
| ----------------------- | ---------------------- | ------------------------------------------------------------------ |
| `APP_NAME`              | `Personal Site API`    | Application title shown in docs.                                   |
| `DEBUG`                 | `false`                | Enable debug mode.                                                 |
| `DATABASE_URL`          | *(empty)*              | SQLAlchemy database URL. Falls back to SQLite when empty.          |
| `POSTGRES_URL`          | *(empty)*              | Alternative PostgreSQL URL variable.                               |
| `DB_ECHO`               | `false`                | Log SQL statements.                                                |
| `AUTO_CREATE_TABLES`    | `true`                 | Create tables automatically on startup.                            |
| `ADMIN_API_TOKEN`       | *(empty)*              | Admin token. When empty, the entire `/api/admin` API is disabled.  |
| `CORS_ORIGINS`          | site origins           | Comma-separated allowed origins.                                   |
| `PUBLIC_BASE_URL`       | *(empty)*              | Canonical site URL used to build media links.                      |
| `FASTAPI_PUBLIC_URL`    | *(empty)*              | Set automatically by FastAPI Cloud; used as a fallback base URL.   |
| `PAGE_SIZE`             | `10`                   | Default number of items per page.                                  |
| `MAX_UPLOAD_MB`         | `25`                   | Maximum upload size in megabytes.                                  |
| `MEDIA_URL`             | `/media/`              | URL path where local media is served.                              |
| `MEDIA_ROOT`            | `./media`              | Local directory for uploaded files.                                |
| `S3_BUCKET`             | *(empty)*              | S3 bucket name. Leave empty to use local storage.                  |
| `S3_REGION`             | `us-east-1`            | Bucket region.                                                     |
| `S3_ACCESS_KEY_ID`      | *(empty)*              | S3 access key.                                                     |
| `S3_SECRET_ACCESS_KEY`  | *(empty)*              | S3 secret key.                                                     |
| `S3_ENDPOINT_URL`       | *(empty)*              | Custom endpoint for R2 / Spaces / MinIO.                           |
| `S3_PUBLIC_BASE_URL`    | *(empty)*              | Public CDN/bucket root for media URLs.                             |
| `S3_PREFIX`             | `media`                | Key prefix for uploaded objects.                                   |
| `S3_PRESIGNED_URLS`     | `false`                | Generate presigned URLs instead of public URLs (private buckets).  |
| `S3_PRESIGN_EXPIRES`    | `3600`                 | Presigned URL lifetime in seconds.                                 |

---

## API Reference

Base path: `/api`. All public endpoints are unauthenticated and return JSON.

### Public endpoints

| Method | Path                          | Description                                    |
| ------ | ----------------------------- | ---------------------------------------------- |
| `GET`  | `/`                           | Service metadata.                              |
| `GET`  | `/health`                     | Health check (verifies DB connectivity).       |
| `GET`  | `/api/main/homedata`          | Profile and featured activities for the home page. |
| `GET`  | `/api/main/resume`            | Resume summary and links.                      |
| `GET`  | `/api/main/educations`        | Paginated education history.                   |
| `GET`  | `/api/main/experiences`       | Paginated work experience.                     |
| `GET`  | `/api/main/skills`            | Skill groups with nested skills.               |
| `GET`  | `/api/main/certificates`      | Paginated certificates with technologies.      |
| `GET`  | `/api/projects`               | Paginated published projects.                  |
| `GET`  | `/api/projects/{slug}`        | Project detail by slug.                        |
| `GET`  | `/api/posts`                  | Paginated published blog posts.                |
| `GET`  | `/api/posts/{slug}`           | Blog post detail by slug.                      |

List endpoints accept a `?page=` query parameter (1-based).

### Pagination envelope

```json
{
  "count": 42,
  "next": "https://api.example.com/api/projects/?page=2",
  "previous": null,
  "results": []
}
```

Requesting an out-of-range page returns `404`.

### Admin endpoints

All routes under `/api/admin` require authentication. Provide the token either as:

```
X-Admin-Token: <ADMIN_API_TOKEN>
```

or:

```
Authorization: Bearer <ADMIN_API_TOKEN>
```

If `ADMIN_API_TOKEN` is unset, every admin route returns `503`; invalid tokens return `401`.

| Resource       | Path                              | Methods                          |
| -------------- | --------------------------------- | -------------------------------- |
| Home profile   | `/api/admin/home`                 | `GET`, `PUT`, `PATCH`            |
| Activities     | `/api/admin/activities`           | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Resume         | `/api/admin/resume`               | `GET`, `PUT`, `PATCH`            |
| Experiences    | `/api/admin/experiences`          | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Educations     | `/api/admin/educations`           | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Skill types    | `/api/admin/skill-types`          | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Skills         | `/api/admin/skills`               | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Certificates   | `/api/admin/certificates`         | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Projects       | `/api/admin/projects`             | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Posts          | `/api/admin/posts`                | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Technologies   | `/api/admin/technologies`         | `GET`, `POST`; `GET`/`PATCH`/`DELETE` by `{id}` |
| Uploads        | `/api/admin/uploads`              | `POST` (`multipart/form-data`: `file`, optional `folder`) |

`PATCH` performs a partial update (validated against the current record). `PUT` replaces the resource. Uploads return `{ "path": "...", "url": "..." }`, where `url` is a browser-usable media URL.

---

## Storage

Uploads are written to S3 when `S3_BUCKET` is set; otherwise they are stored under `MEDIA_ROOT` and served from `MEDIA_URL`.

For S3-compatible providers, configure `S3_ENDPOINT_URL` and the appropriate `S3_ADDRESSING_STYLE`. For private buckets, set `S3_PRESIGNED_URLS=true` so responses contain time-limited signed URLs. Upload folder names are validated and generated filenames are random UUIDs.

---

## Database

- **Development:** with no `DATABASE_URL`, the app uses `personal_site.db` (SQLite).
- **Production:** set `DATABASE_URL` (PostgreSQL). `postgres://` and `postgresql+psycopg2://` URLs are normalized to the psycopg 3 driver automatically.
- Tables are created on startup when `AUTO_CREATE_TABLES=true`. For schema changes, use a migration tool (e.g. Alembic) and disable automatic creation.

---

## Deployment

The project is linked to **FastAPI Cloud** (`.fastapicloud/`), with a Neon PostgreSQL database managed through the integration. Deploy with:

```bash
fastapi cloud deploy
```

Set `ADMIN_API_TOKEN`, `DATABASE_URL`, CORS origins, and any S3 credentials as environment variables in the deployment environment. Never commit `.env` or real credentials.

---

## Development

- API documentation: `/docs` (Swagger UI) and `/redoc`.
- The database session dependency is defined in `app/database.py`; route handlers receive it via `Depends(get_db)`.
- Public responses are shaped by functions in `app/presenters.py`, keeping database models decoupled from the API contract.
- Tests (pytest, httpx) are declared as dev dependencies; run with `uv run pytest`.

```bash
uv sync --extra dev
uv run pytest
```
