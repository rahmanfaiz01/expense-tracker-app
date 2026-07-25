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
│   ├── app/            # source (core, db, models, schemas, api, tests)
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

# create the schema
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
| `alembic downgrade base`   | Roll back to an empty schema |
| `alembic current`          | Show the applied revision   |
| `alembic history`          | List revisions              |

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
| `TEST_DATABASE_URL`    | `postgresql+psycopg://postgres:postgres@localhost:5432/expense_tracker_test` |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173`                                            |

### Frontend (`frontend/.env`)

| Variable       | Example                          |
| -------------- | -------------------------------- |
| `VITE_API_URL` | `http://localhost:8000/api/v1`   |

## Database schema

All tables use **UUID** primary keys (generated application-side) and
timezone-aware `created_at` / `updated_at` (`TIMESTAMPTZ`, defaulting to
`now()`; `updated_at` is bumped on update).

### `users`

| Column            | Type           | Notes                    |
| ----------------- | -------------- | ------------------------ |
| `id`              | `UUID`         | PK                       |
| `email`           | `VARCHAR(320)` | **unique**, not null     |
| `hashed_password` | `VARCHAR(255)` | not null (unused until Phase 2) |
| `full_name`       | `VARCHAR(255)` | nullable                 |
| `is_active`       | `BOOLEAN`      | not null, default `true` |

### `categories`

| Column    | Type               | Notes                                     |
| --------- | ------------------ | ----------------------------------------- |
| `id`      | `UUID`             | PK                                        |
| `user_id` | `UUID`             | FK → `users.id` `ON DELETE CASCADE`, indexed |
| `name`    | `VARCHAR(100)`     | not null                                  |
| `type`    | `transaction_type` | enum `income` \| `expense`                |
| `color`   | `VARCHAR(7)`       | nullable, hex e.g. `#1A2B3C`              |

Constraint: `UNIQUE (user_id, name, type)` — the same name may be reused for an
income and an expense category, but not twice within one type.

### `transactions`

| Column        | Type               | Notes                                          |
| ------------- | ------------------ | ---------------------------------------------- |
| `id`          | `UUID`             | PK                                             |
| `user_id`     | `UUID`             | FK → `users.id` `ON DELETE CASCADE`, not null  |
| `category_id` | `UUID`             | FK → `categories.id` `ON DELETE SET NULL`, **nullable** |
| `type`        | `transaction_type` | enum `income` \| `expense`                     |
| `amount`      | `NUMERIC(12,2)`    | Python `Decimal`, never float                  |
| `currency`    | `VARCHAR(3)`       | uppercase ISO-4217-style code, default `USD`   |
| `description` | `VARCHAR(255)`     | nullable                                       |
| `occurred_on` | `DATE`             | not null                                       |

Indexes: `(user_id, occurred_on)` and `(user_id, category_id)`.

Check constraints:

- `ck_transactions_amount_positive` — `amount > 0` (direction is carried by
  `type`, so amounts are always stored positive)
- `ck_transactions_currency_format` — `currency ~ '^[A-Z]{3}$'`

Pydantic schemas (`app/schemas/`) mirror these rules at the edge: they reject
non-positive amounts and more than two decimal places, and normalize currency
(`" usd "` → `"USD"`) before it reaches the database.

### Enum

`income` / `expense` is a single PostgreSQL enum type named `transaction_type`,
shared by `categories.type` and `transactions.type`, so a category can only be
used for the kind of entry it was created for. The migration creates and drops
the type explicitly.

### Deletion behavior

| Deleted entity | Effect                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------- |
| **User**       | Cascades: all of the user's categories **and** transactions are deleted (`ON DELETE CASCADE`, mirrored by ORM `cascade="all, delete-orphan"` + `passive_deletes=True`). |
| **Category**   | Transactions are **kept**; their `category_id` becomes `NULL` (`ON DELETE SET NULL`). Financial history is never lost by re-organising categories. |
| **Transaction**| Only that row is removed; the user and category are untouched.                              |

## Migrations

```bash
cd backend
source .venv/bin/activate

alembic upgrade head        # empty database -> full schema
alembic downgrade base      # full schema -> empty database
alembic upgrade head        # re-apply
alembic current             # show the applied revision
```

The initial revision is `0001_initial`
(`migrations/versions/0001_initial_data_layer.py`). Downgrading to `base` drops
the three tables *and* the shared `transaction_type` enum, so a subsequent
upgrade starts from a truly empty database.

To add a migration after changing models:

```bash
alembic revision --autogenerate -m "describe the change"
```

A test asserts that autogenerate produces **no** diff against the models, so
forgetting a migration fails CI.

## Testing

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`

Backend tests need a running PostgreSQL (`docker compose up -d db`). The suite
drops and recreates the database in `TEST_DATABASE_URL`
(`expense_tracker_test` by default), applies the migrations once per session,
and wraps each test in a transaction that is rolled back afterwards.

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

Phase 0: scaffold. Phase 1 (this): data layer — models, initial migration and
validation schemas (no endpoints yet). Next: **Phase 2** authentication. See
the architecture document for the full plan.
