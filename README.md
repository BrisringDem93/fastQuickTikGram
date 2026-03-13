# FastQuickTikGram

> **AI-powered video content creator SaaS** — upload a video, generate scroll-stopping hooks with GPT-4, auto-edit the clip, then publish to YouTube, TikTok, Instagram, and Facebook in one workflow.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [ContentJob State Machine](#contentjob-state-machine)
5. [Tech Stack](#tech-stack)
6. [Prerequisites](#prerequisites)
7. [Setup Instructions](#setup-instructions)
8. [Local Development](#local-development)
9. [Environment Variables](#environment-variables)
10. [API Endpoints Reference](#api-endpoints-reference)
11. [Social Platform Setup](#social-platform-setup)
12. [Production Readiness TODO](#production-readiness-todo)

---

## Project Overview

FastQuickTikGram is a multi-tenant SaaS platform that automates short-form video content creation and cross-platform publishing. Users upload a raw video, the AI generates engaging hook text, the video is automatically edited to feature the hook, and the result is published to one or more connected social media accounts — either immediately or on a schedule.

---

## Features

- 🎬 **Video upload** via presigned S3 URLs (up to 500 MB, avoids routing large files through the API server)
- 🤖 **AI hook generation** powered by OpenAI GPT-4 — multiple options generated asynchronously
- ✂️ **Automated video editing** via FFmpeg — overlays approved hook text onto the video
- 📅 **Scheduled publishing** with timezone support (Celery beat picks up scheduled jobs)
- 📡 **Multi-platform publishing** — YouTube, TikTok, Instagram, Facebook
- 🔗 **OAuth 2.0 social account management** — connect/disconnect accounts per user
- 🔒 **JWT authentication** — access + refresh token pair, bcrypt password hashing
- 🧮 **16-state content job state machine** with full retry / recovery paths
- 🗂️ **Per-platform publish targets** with individual status tracking

---

## Architecture

```
                          ┌─────────────────────────────────────────────────────┐
                          │                    Docker Compose                    │
                          │                                                       │
 Browser ──HTTP/HTTPS──► │    Frontend (Next.js :3000, internal only)         │
 via Coolify/Traefik     │             │                                        │
 (external reverse proxy)│             │ /api/* rewrite                          │
                         │             ▼                                        │
                         │      Backend (FastAPI :8000, internal only)         │
                         │             │                     │                   │
                         │        PostgreSQL :5432       Redis :6379            │
                         │                                  │ broker             │
                         │                    ┌─────────────▼─────────────┐     │
                         │                    │      Celery worker/beat    │     │
                         │                    └────────────────────────────┘     │
                         └─────────────────────────────────────────────────────┘
```

**Request flow:**
1. Browser → external reverse proxy (Coolify/Traefik)
2. Reverse proxy routes traffic to the Next.js frontend service (`:3000`) on the Docker network
3. Frontend `/api/*` requests are rewritten to FastAPI backend (`http://backend:8000`)
4. Next.js server-side calls backend via internal Docker DNS (`http://backend:8000`)
5. Long-running tasks (video processing, publishing) dispatched to Celery via Redis

---

## ContentJob State Machine

Every piece of content is tracked as a `ContentJob` with 16 states:

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                      ContentJob State Machine                            │
  └─────────────────────────────────────────────────────────────────────────┘

                            ┌──────────┐
                            │  DRAFT   │◄─────────────────────────┐
                            └────┬─────┘                          │
                                 │ confirm-upload                  │
                                 ▼                                 │
                       ┌─────────────────┐                        │
                       │ VIDEO_UPLOADED  │                        │
                       └────────┬────────┘                        │
                                │ generate-hooks                   │
                                ▼                                  │
                       ┌─────────────────┐                        │
                       │ HOOK_GENERATING │                        │
                       └────────┬────────┘                        │
                                │ (Celery: hook_tasks)             │
                                ▼                                  │
                  ┌──────────────────────────┐                    │
                  │  HOOK_PENDING_APPROVAL   │                    │
                  └──────┬──────────┬────────┘                    │
              approve    │          │ reject                       │
                         ▼          ▼                              │
               ┌──────────────┐  ┌───────────────┐               │
               │ HOOK_APPROVED│  │ HOOK_REJECTED │──generate──►  │
               └──────┬───────┘  └───────────────┘  (loop)       │
                      │ (Celery: video_tasks)                      │
                      ▼                                            │
               ┌──────────────┐                                   │
               │ VIDEO_EDITING│                                   │
               └──────┬───────┘                                   │
                      │ (FFmpeg overlay)                           │
                      ▼                                            │
               ┌──────────────┐    no social     ┌───────────────────────────────┐
               │  VIDEO_READY │──── accounts ───►│ WAITING_FOR_SOCIAL_CONNECTION │
               └──────┬───────┘    connected      └──────────────┬────────────────┘
                      │ select-destinations               select  │
                      │◄──────────────────────────────────────────┘
                      ▼
               ┌────────────────────────┐
               │  DESTINATIONS_SELECTED │
               └──────────┬─────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │   READY_TO_PUBLISH   │◄─── un-schedule ──┐
                └──────┬───────────────┘                    │
            publish    │           │ schedule               │
            now        │           ▼                        │
                       │      ┌──────────┐                  │
                       │      │ SCHEDULED├──────────────────┘
                       │      └────┬─────┘
                       │           │ (Celery beat fires at scheduled_at_utc)
                       ▼           ▼
                    ┌────────────────┐
                    │   PUBLISHING   │
                    └───┬────────────┘
                        │
              ┌─────────┴─────────────┐
              ▼                       ▼
      ┌──────────────┐   ┌─────────────────────┐
      │  PUBLISHED   │   │  PARTIALLY_PUBLISHED │──retry──► PUBLISHING
      │  (terminal)  │   └─────────────────────┘
      └──────────────┘

  Any state ──────────────────────────────────────────────────► FAILED
                                                                   │
                          (manual recovery / retry)                │
                          ◄──────────────────────────────────────-─┘
```

**State descriptions:**

| State | Description |
|---|---|
| `DRAFT` | Job created, no video yet |
| `VIDEO_UPLOADED` | Video stored in S3, ready for hook generation |
| `HOOK_GENERATING` | Celery task calling OpenAI to generate hook options |
| `HOOK_PENDING_APPROVAL` | Hook options ready, waiting for user selection |
| `HOOK_REJECTED` | User rejected all options; can regenerate |
| `HOOK_APPROVED` | User selected/customised a hook; video editing queued |
| `VIDEO_EDITING` | Celery task running FFmpeg to overlay hook text |
| `VIDEO_READY` | Edited video stored in S3 |
| `WAITING_FOR_SOCIAL_CONNECTION` | No social accounts connected yet |
| `DESTINATIONS_SELECTED` | User picked target social accounts |
| `READY_TO_PUBLISH` | All pre-conditions met; awaiting publish trigger |
| `SCHEDULED` | Publish scheduled for a future `scheduled_at_utc` |
| `PUBLISHING` | Celery task actively uploading to all platforms |
| `PARTIALLY_PUBLISHED` | At least one platform succeeded, at least one failed |
| `PUBLISHED` | Successfully published to all selected platforms ✅ |
| `FAILED` | Terminal error — manual intervention or retry possible |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI 0.111 + Python 3.12, Uvicorn |
| **ORM / DB** | SQLAlchemy 2 (async), Alembic migrations |
| **Database** | PostgreSQL 15 |
| **Task queue** | Celery 5 + Redis 7 (broker & result backend) |
| **Object storage** | AWS S3 / MinIO (S3-compatible) |
| **AI** | OpenAI Python SDK (GPT-4) |
| **Video processing** | FFmpeg (via subprocess) |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| **Reverse proxy** | Coolify / Traefik (external to this compose stack) |
| **Containerisation** | Docker, Docker Compose |
| **Local email** | MailHog (dev only) |
| **Local storage** | MinIO (dev only) |

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Docker | 24.x | Required |
| Docker Compose | 2.x (plugin) | `docker compose` (v2) |
| Node.js | 20.x | Optional – only for frontend development outside Docker |
| Python | 3.12 | Optional – only for backend development outside Docker |
| `make` | any | Optional – convenience targets |

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-org/fastQuickTikGram.git
cd fastQuickTikGram
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

- Generate `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- Generate `ENCRYPTION_KEY` (Fernet):
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- Add your `OPENAI_API_KEY`
- Add OAuth credentials for any social platforms you want to test (see [Social Platform Setup](#social-platform-setup))

### 3. Build and start services

```bash
# Production stack (for Coolify/Traefik deployment; no host ports published)
# API and beat now reuse the same lean backend image; only the worker image includes FFmpeg.
docker compose up --build -d

# Check everything is healthy
docker compose ps
docker compose logs -f backend
```

### 4. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Verify locally (development override)

Start with the development override when you need localhost access:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

| Service | URL |
|---|---|
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |
| Frontend | http://localhost:3550 |
| Health check | http://localhost:8000/health |

### 6. Create your first user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"changeme","full_name":"Your Name"}'
```

---

## Local Development

Use the development override file for hot-reload, MinIO, and MailHog:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This adds:

| Service | URL | Purpose |
|---|---|---|
| MinIO API | http://localhost:9000 | S3-compatible storage (replaces real AWS S3) |
| MinIO Console | http://localhost:9001 | Web UI to browse buckets (`minioadmin` / `minioadmin`) |
| MailHog SMTP | localhost:1025 | Catches outbound email |
| MailHog Web | http://localhost:8025 | Inspect caught emails |

And mounts source code into running containers so changes are reflected without rebuilding:

- **Backend** runs `uvicorn --reload` — Python changes reload automatically
- **Frontend** runs `next dev` — HMR active in the browser
- **Worker/Beat** mounts source; restart containers after worker code changes:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml restart worker beat
  ```

### Creating a MinIO bucket on first run

```bash
# Via the MinIO web console (http://localhost:9001), or:
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc mb local/fastquicktikgram
docker compose exec minio mc anonymous set public local/fastquicktikgram
```

### Running backend tests

```bash
docker compose exec backend python -m pytest -v
```

### Running Alembic migrations in dev

```bash
# Apply
docker compose exec backend alembic upgrade head

# Create a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "add_my_column"

# Downgrade one step
docker compose exec backend alembic downgrade -1
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values before starting the stack.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | FastAPI JWT signing secret. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | ✅ | — | Fernet key for encrypting OAuth tokens at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `DATABASE_URL` | — | `postgresql+asyncpg://user:password@localhost/fastquicktikgram` | asyncpg connection string, e.g. `postgresql+asyncpg://user:pass@host/db` |
| `S3_BUCKET` | — | `fastquicktikgram` | S3/MinIO bucket name |
| `S3_ACCESS_KEY` | — | `s3-access-key` | S3 / MinIO access key ID |
| `S3_SECRET_KEY` | — | `s3-secret-key` | S3 / MinIO secret access key |
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key for AI hook generation |
| `NEXT_PUBLIC_API_URL` | — | `/api` | Legacy frontend API prefix (kept for backward compatibility) |
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | `/api/v1` | Frontend base URL used by Axios (`/api/v1` via Next.js rewrite, or `https://api.yourdomain.com/api/v1` for direct backend calls) |
| `POSTGRES_USER` | — | `postgres` | PostgreSQL username (used by the postgres Docker service) |
| `POSTGRES_PASSWORD` | — | `postgres` | PostgreSQL password (used by the postgres Docker service) |
| `POSTGRES_DB` | — | `fastquicktikgram` | PostgreSQL database name (used by the postgres Docker service) |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Redis connection string |
| `CELERY_BROKER_URL` | — | `redis://localhost:6379/0` | Redis URL for Celery task messages |
| `CELERY_RESULT_BACKEND` | — | `redis://localhost:6379/1` | Redis URL for Celery task results |
| `JWT_ALGORITHM` | — | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `30` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | — | `30` | Refresh token lifetime in days |
| `S3_ENDPOINT_URL` | — | _(AWS default)_ | Override S3 endpoint for MinIO in dev (`http://minio:9000`); omit for AWS |
| `S3_REGION` | — | `us-east-1` | AWS region (or any value when using MinIO) |
| `MAX_VIDEO_SIZE_MB` | — | `500` | Maximum video upload size in megabytes |
| `BACKEND_URL` | — | `http://backend:8000` | Internal Docker URL used by Next.js server-side rendering to reach the backend |
| `YOUTUBE_CLIENT_ID` | ⚠️ | — | Google OAuth client ID |
| `YOUTUBE_CLIENT_SECRET` | ⚠️ | — | Google OAuth client secret |
| `YOUTUBE_REDIRECT_URI` | ⚠️ | — | Must match the redirect URI configured in Google Cloud Console |
| `TIKTOK_CLIENT_KEY` | ⚠️ | — | TikTok developer app client key |
| `TIKTOK_CLIENT_SECRET` | ⚠️ | — | TikTok developer app client secret |
| `TIKTOK_REDIRECT_URI` | ⚠️ | — | Must match the redirect URI configured in TikTok for Developers |
| `INSTAGRAM_CLIENT_ID` | ⚠️ | — | Facebook/Instagram app client ID |
| `INSTAGRAM_CLIENT_SECRET` | ⚠️ | — | Facebook/Instagram app client secret |
| `INSTAGRAM_REDIRECT_URI` | ⚠️ | — | Must match the redirect URI configured in Meta for Developers |
| `FACEBOOK_APP_ID` | ⚠️ | — | Facebook app ID |
| `FACEBOOK_APP_SECRET` | ⚠️ | — | Facebook app secret |
| `FACEBOOK_REDIRECT_URI` | ⚠️ | — | Must match the redirect URI configured in Meta for Developers |

✅ = required — the app will not start without this value  
⚠️ = required only when you want to use that specific social platform  
— = optional, falls back to the default shown

---

## API Endpoints Reference

All backend routes are mounted under `/api/v1`. The full interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### API Routing Convention

- **Canonical API prefix:** `/api/v1`
- **Backend router structure:** each domain router defines its own resource prefix (for example, `APIRouter(prefix="/auth")`) and is mounted in `backend/app/main.py` with `prefix="/api/v1"`.
- **Final endpoint example:** `POST /api/v1/auth/register`
- **Frontend call example:** `fetch("/api/v1/auth/register", { method: "POST", ... })`
- **Frontend API base config:** set `NEXT_PUBLIC_API_BASE_URL` to `/api/v1` when using Next.js rewrite, or to `https://api.yourdomain.com/api/v1` when backend is exposed on a separate domain.
- **Next.js rewrite convention:** `/api/*` on the frontend proxies to backend `/api/*`, so `/api/v1/*` remains unchanged end-to-end.
- **Warning:** if frontend and backend prefixes do not match (for example `/api/auth/*` vs `/api/v1/auth/*`), requests will return `404 Not Found`.

### Troubleshooting 404 Errors

Common causes:

- Frontend calling `/api/auth/*` instead of `/api/v1/auth/*`.
- Next.js rewrite missing the `/api` segment in the destination path.
- Routers mounted under a different prefix in `backend/app/main.py`.

### Authentication (`/api/v1/auth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | ❌ | Register a new user account |
| `POST` | `/api/v1/auth/login` | ❌ | Login and receive JWT access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | ❌ | Exchange refresh token for new access token |
| `GET` | `/api/v1/auth/me` | ✅ | Get current user profile |

### Content Jobs (`/api/v1/jobs`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/jobs` | ✅ | Create a new content job (→ `DRAFT`) |
| `GET` | `/api/v1/jobs` | ✅ | List jobs (paginated) |
| `GET` | `/api/v1/jobs/{job_id}` | ✅ | Get a single job |
| `POST` | `/api/v1/jobs/{job_id}/upload-video` | ✅ | Get presigned S3 upload URL |
| `POST` | `/api/v1/jobs/{job_id}/confirm-upload` | ✅ | Confirm upload complete (→ `VIDEO_UPLOADED`) |
| `POST` | `/api/v1/jobs/{job_id}/generate-hooks` | ✅ | Trigger Celery hook generation (→ `HOOK_GENERATING`) |
| `GET` | `/api/v1/jobs/{job_id}/hooks` | ✅ | List generated hooks |
| `POST` | `/api/v1/jobs/{job_id}/approve-hook` | ✅ | Approve a hook + trigger video editing (→ `HOOK_APPROVED`) |
| `POST` | `/api/v1/jobs/{job_id}/select-destinations` | ✅ | Select social accounts to publish to |
| `POST` | `/api/v1/jobs/{job_id}/publish-now` | ✅ | Publish immediately (→ `PUBLISHING`) |
| `POST` | `/api/v1/jobs/{job_id}/schedule` | ✅ | Schedule for future publish (→ `SCHEDULED`) |
| `POST` | `/api/v1/jobs/{job_id}/resume` | ✅ | Get state so the wizard can resume |

### Social Accounts (`/api/v1/social`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/social/accounts` | ✅ | List connected social accounts |
| `GET` | `/api/v1/social/connect/{platform}` | ✅ | Get OAuth authorization URL |
| `GET` | `/api/v1/social/callback/{platform}` | ✅ | Handle OAuth redirect callback |
| `DELETE` | `/api/v1/social/accounts/{account_id}` | ✅ | Disconnect a social account |

Supported `{platform}` values: `youtube`, `tiktok`, `instagram`, `facebook`

### Publishing (`/api/v1/publishing`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/publishing/{job_id}/status` | ✅ | Aggregated publish status across all platforms |
| `GET` | `/api/v1/publishing/{job_id}/targets` | ✅ | Per-platform publish target list with individual status |

### Utility

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | ❌ | Service health check |
| `GET` | `/docs` | ❌ | Swagger UI |
| `GET` | `/redoc` | ❌ | ReDoc UI |

---

## Social Platform Setup

### YouTube / Google

> **TODO:** Create a Google Cloud project, enable the YouTube Data API v3, create OAuth 2.0 credentials (Web application), and add `http://localhost:3000/api/social/callback/youtube` as an authorised redirect URI.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → APIs & Services → Enable **YouTube Data API v3**
3. Credentials → Create Credentials → **OAuth client ID** → Web application
4. Add authorised redirect URI: `http://localhost:3000/api/social/callback/youtube`
5. Copy **Client ID** → `YOUTUBE_CLIENT_ID` and **Client Secret** → `YOUTUBE_CLIENT_SECRET`

---

### TikTok

> **TODO:** Register a developer app on TikTok for Developers, request the `video.upload` and `video.publish` scopes, and configure the redirect URI.

1. Go to [TikTok for Developers](https://developers.tiktok.com/)
2. Create an app → enable **Login Kit** and **Content Posting API**
3. Add redirect URI: `http://localhost:3000/api/social/callback/tiktok`
4. Copy **Client Key** → `TIKTOK_CLIENT_KEY` and **Client Secret** → `TIKTOK_CLIENT_SECRET`

> **Note:** TikTok requires app review to access the Content Posting API in production. For development, use a sandbox/test account.

---

### Instagram (via Meta)

> **TODO:** Create a Meta app with Instagram Basic Display API (personal accounts) or Instagram Graph API (business accounts), and configure the redirect URI.

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create an app → Add **Instagram** product
3. For business publishing use **Instagram Graph API** (requires a Facebook Page linked to an Instagram Business account)
4. Add redirect URI: `http://localhost:3000/api/social/callback/instagram`
5. Copy **App ID** → `INSTAGRAM_CLIENT_ID` and **App Secret** → `INSTAGRAM_CLIENT_SECRET`

---

### Facebook

> **TODO:** Create a Meta app with the Pages API, request `pages_manage_posts` and `pages_read_engagement` permissions, and configure the redirect URI.

1. In the same Meta app (or a separate one), add the **Facebook Login** product
2. Enable **pages_manage_posts**, **pages_read_engagement** permissions
3. Add redirect URI: `http://localhost:3000/api/social/callback/facebook`
4. Copy **App ID** → `FACEBOOK_APP_ID` and **App Secret** → `FACEBOOK_APP_SECRET`

> **Note:** Publishing to Pages requires Business Verification and App Review for the `pages_manage_posts` permission in production.

---

## Production Readiness TODO

The following items should be addressed before deploying to production:

### Security
- [ ] Set strong, unique `SECRET_KEY` and `ENCRYPTION_KEY` — never reuse dev values
- [ ] Add allowed CORS origins in `backend/app/main.py` (remove `localhost` entries)
- [ ] Enable HTTPS in Nginx (use Let's Encrypt / Certbot or a load-balancer terminator)
- [ ] Restrict `client_max_body_size` to match `MAX_VIDEO_SIZE_MB`
- [ ] Add rate limiting in Nginx or at API layer for auth endpoints
- [ ] Rotate OAuth tokens and store with encryption at rest (verify `ENCRYPTION_KEY` in use)
- [ ] Enable PostgreSQL SSL connections (`?ssl=require` in `DATABASE_URL`)
- [ ] Audit and remove debug endpoints (Swagger/ReDoc) or protect behind auth

### Infrastructure
- [ ] Replace MinIO with AWS S3 (update `S3_ENDPOINT_URL`, credentials, bucket policy)
- [ ] Use a managed PostgreSQL service (RDS, Cloud SQL, Supabase) for HA and backups
- [ ] Use a managed Redis service (ElastiCache, Upstash) for HA
- [ ] Configure Celery worker concurrency and autoscaling based on load
- [ ] Add `--beat-scheduler=django_celery_beat.schedulers:DatabaseScheduler` or persistent beat storage to avoid losing scheduled jobs on restart
- [ ] Set up persistent Celery beat schedule storage (not in-memory)

### Observability
- [ ] Integrate structured logging (JSON) and ship to a log aggregator (Loki, Datadog, CloudWatch)
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Set up health-check alerting for all services
- [ ] Add Sentry (or equivalent) for error tracking in both backend and frontend
- [ ] Expose Prometheus metrics from FastAPI and Celery

### CI/CD
- [ ] Add GitHub Actions workflow for lint, test, build, and push Docker images
- [ ] Set up staging environment with separate database and secrets
- [ ] Add automated Alembic migration step to deploy pipeline
- [ ] Tag Docker images with git SHA or semantic version

### Scalability
- [ ] Move Nginx to a CDN-backed load balancer in production
- [ ] Store uploaded video presigned-URL size limit server-side to prevent abuse
- [ ] Add S3 lifecycle policy to expire `tmp/` prefixed objects
- [ ] Implement job retry limits and dead-letter queue for Celery tasks
- [ ] Shard Celery queues by task type (video processing vs. publishing vs. hooks)

### Social Platform
- [ ] Complete OAuth token refresh logic for all four platforms
- [ ] Handle platform-specific upload size / duration limits per platform API rules
- [ ] Add webhook handlers for platform async upload status callbacks (TikTok, YouTube)
- [ ] Implement re-authentication flow when tokens expire or are revoked by the user
