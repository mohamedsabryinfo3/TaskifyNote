# TaskifyNote

Personal AI Tasks, Notes and Knowledge Workspace.

## Monorepo

- `apps/android` — Android client (Kotlin + Jetpack Compose).
- `apps/api` — FastAPI backend for Tasks, Notes, Search, AI and URL ingestion.
- `apps/web` — Next.js dashboard for Vercel.
- `infra/postgres/migrations` — Neon/PostgreSQL schema.
- `infra/docker-compose.yml` — local PostgreSQL + API development stack.
- `openapi/openapi.yaml` — API contract.

## Product

TaskifyNote is a single-owner personal workspace. It combines tasks, notes, web-source capture and an AI assistant. The target flow is:

`Share URL → extract content → analyze → preview → save as note/tasks`

## Deployment

### Vercel Web
Create a Vercel project from this repository and set Root Directory to `apps/web`.

### Vercel API
Create a second Vercel project from the same repository and set Root Directory to `apps/api`.

Required API environment variables:

`DATABASE_URL`
`PERSONAL_API_KEY`
`CORS_ORIGINS`
`GEMINI_API_KEY`

### Neon
Use the pooled Neon PostgreSQL connection string for the API runtime. Keep the connection string only in Vercel Environment Variables or GitHub Actions secrets.

## Android

Open `apps/android` in Android Studio. Configure the production API URL through Gradle properties and build the app from the `app` module.

## Local API

```bash
cd apps/api
python -m venv .venv
# activate the environment
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health endpoint:

`GET /api/v1/health`

## License

Private personal project.
