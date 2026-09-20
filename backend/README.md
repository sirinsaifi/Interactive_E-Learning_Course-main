# LearnSphere Backend

FastAPI backend for the LearnSphere LMS.

## Authentication

LearnSphere uses **simple email-based access** — no passwords, no OAuth.

| Email | Role |
|-------|------|
| Value of `INSTRUCTOR_EMAIL` env var | Instructor |
| Any other email | Learner |

**Flow:**
1. User enters their email on the login page.
2. `POST /api/v1/auth/login` → server finds or creates the user, assigns role based on `INSTRUCTOR_EMAIL`, and returns an opaque session token.
3. The token is stored in `localStorage` and sent as `Authorization: Bearer <token>` on every subsequent request.
4. `POST /api/v1/auth/logout` invalidates the token server-side.

No Google OAuth. No JWT. No passwords. No signup form.

## Setup

```bash
cd backend
cp .env.example .env
# Edit .env — set DATABASE_URL and INSTRUCTOR_EMAIL at minimum.

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes (or set `DB_*`) | MySQL connection string |
| `INSTRUCTOR_EMAIL` | Yes | Email that gets the instructor role |
| `SESSION_SECRET` | Prod | Secret for session token signing |
| `STORAGE_BACKEND` | No | `local` (default) or `cloudinary` |
| `CLOUDINARY_*` | If cloudinary | Cloudinary credentials |

## Running with Docker Compose

```bash
docker compose up --build
```
