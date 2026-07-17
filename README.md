# Expense Tracker

A modern full-stack expense tracker. **Phase 0** delivers the project scaffold:
a runnable FastAPI backend with a health endpoint, a React + Vite + MUI
frontend that verifies backend connectivity, local tooling, tests, and CI.

Authentication, categories, and transactions are intentionally **not** included
yet — see the roadmap in the architecture doc.

## Tech stack

| Layer     | Technology                                        |
| --------- | ------------------------------------------------- |
| Frontend  | React, Vite, TypeScript, Material UI, Recharts    |
| Backend   | FastAPI, SQLAlchemy 2, Alembic, Pydantic          |
| Database  | PostgreSQL (Docker Compose for local dev)         |
| Auth      | JWT (access in memory + refresh HttpOnly cookie)  |
| Deploy    | Railway (backend), Vercel (frontend)              |

## Repository layout

```
expense-tracker-app/
├── backend/            # FastAPI application
│   ├── app/            # source (core, db, api, tests)
│   ├── migrations/     # Alembic
│   ├── pyproject.toml  # deps + ruff/mypy/pytest config
│   ├── Dockerfile      # Railway container build
│   └── Procfile        # Railway process + release (migrations)
├── frontend/           # React + Vite + MUI app
│   └── src/            # source (api, features, theme, tests)
├── docker-compose.yml  # local PostgreSQL only
├── vercel.json         # Vercel build config
└── .github/workflows/  # CI (lint, typecheck, test, build)
```

## Prerequisites

- Python **3.10+** (3.11 recommended)
- Node.js **20+**
- Docker + Docker Compose (for the local database)

## Local setup

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

This runs Postgres on `localhost:5432` with database `expense_tracker`
(user/password `postgres`/`postgres`).

### 2. Backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# apply migrations (none exist yet in Phase 0, this is a no-op scaffold check)
alembic upgrade head

# run the API
uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Health:   http://localhost:8000/api/v1/health
- Docs:     http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 — the page shows a **Backend connectivity** panel
that calls `/api/v1/health` and reports success/failure.

## Common commands

### Backend (`cd backend`)

| Command                    | Description                 |
| -------------------------- | --------------------------- |
| `uvicorn app.main:app --reload` | Run the dev server     |
| `pytest`                   | Run tests                   |
| `ruff check .`             | Lint                        |
| `ruff format .`            | Format                      |
| `mypy`                     | Type-check                  |
| `alembic revision --autogenerate -m "msg"` | New migration |
| `alembic upgrade head`     | Apply migrations            |

### Frontend (`cd frontend`)

| Command             | Description            |
| ------------------- | ---------------------- |
| `npm run dev`       | Run the dev server     |
| `npm run build`     | Type-check + build     |
| `npm run test`      | Run unit tests         |
| `npm run lint`      | ESLint                 |
| `npm run format`    | Prettier (write)       |
| `npm run format:check` | Prettier (check)    |

## Environment variables

### Backend (`backend/.env`)

| Variable               | Example                                                            |
| ---------------------- | ----------------------------------------------------------------- |
| `PROJECT_NAME`         | `Expense Tracker API`                                             |
| `ENVIRONMENT`          | `development`                                                      |
| `API_V1_PREFIX`        | `/api/v1`                                                          |
| `DATABASE_URL`         | `postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker` |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173`                                            |

### Frontend (`frontend/.env`)

| Variable       | Example                          |
| -------------- | -------------------------------- |
| `VITE_API_URL` | `http://localhost:8000/api/v1`   |

## Testing

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`

CI (`.github/workflows/ci.yml`) runs lint, type-checks, tests, and the frontend
build on every push to `main` and every pull request.

## Deployment (configured, deployed in a later phase)

- **Backend → Railway:** deploy the `backend/` directory. Uses `Dockerfile`
  (or the `Procfile`). Add a PostgreSQL plugin and set `DATABASE_URL`,
  `BACKEND_CORS_ORIGINS` (your Vercel URL), and other env vars. The `release`
  process runs `alembic upgrade head`.
- **Frontend → Vercel:** import the repo; `vercel.json` builds `frontend/`.
  Set `VITE_API_URL` to the Railway API URL (including `/api/v1`).

## Roadmap

Phase 0 (this): scaffold. Next: **Phase 1** data layer (models + migrations),
then **Phase 2** authentication. See the architecture document for the full
plan.
