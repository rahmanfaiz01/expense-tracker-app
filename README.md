# Expense Tracker

A modern full-stack expense tracker: register and sign in, record income and
expenses, organise them with categories, search/filter/sort/paginate the
history, export it to CSV, and review balances, monthly trends and per-category
breakdowns on a responsive dashboard with dark mode.

## Features

- **Auth** — registration, login, logout, JWT access token kept in memory and a
  rotating refresh token in an HttpOnly cookie (silent refresh on start-up and
  on any `401`), protected routes.
- **Transactions** — create, edit, delete, description search, filters by type,
  category and date range, sortable columns, pagination and CSV export that
  honours the active filters.
- **Categories** — per-user income/expense categories with colors; deleting one
  keeps its transactions and marks them uncategorized.
- **Dashboard** — income/expense/balance cards plus Recharts monthly and
  by-category charts, with loading, empty and error states throughout.
- Every endpoint is scoped to the authenticated user; another account's ids
  simply return `404`.

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
│   ├── app/            # source (core, db, models, schemas, crud, services, api, tests)
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

Open http://localhost:5173, create an account and you land on the dashboard.
The dev server proxies nothing — the frontend calls the API at `VITE_API_URL`
(default `http://localhost:8000/api/v1`) with credentials, so keep the backend's
`BACKEND_CORS_ORIGINS` pointing at the Vite origin.

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
| `JWT_SECRET_KEY`       | `python -c "import secrets; print(secrets.token_urlsafe(48))"`     |
| `JWT_ALGORITHM`        | `HS256`                                                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15`                                                        |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `14`                                                        |
| `REFRESH_COOKIE_NAME`  | `refresh_token`                                                    |
| `REFRESH_COOKIE_PATH`  | `/api/v1/auth`                                                     |
| `COOKIE_SECURE`        | `false` locally, `true` in production                              |
| `COOKIE_SAMESITE`      | `lax` locally, `none` for Vercel → Railway                         |
| `COOKIE_DOMAIN`        | unset locally                                                      |
| `RATE_LIMIT_ENABLED`   | `true`                                                             |
| `RATE_LIMIT_REGISTER` / `RATE_LIMIT_LOGIN` / `RATE_LIMIT_REFRESH` | `5/minute` / `10/minute` / `30/minute` |

With `ENVIRONMENT=production` the app refuses to start while `JWT_SECRET_KEY`
is still the placeholder from `.env.example`.

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
| `hashed_password` | `VARCHAR(255)` | not null, Argon2id hash  |
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

### `refresh_tokens`

| Column       | Type            | Notes                                              |
| ------------ | --------------- | -------------------------------------------------- |
| `id`         | `UUID`          | PK                                                  |
| `user_id`    | `UUID`          | FK → `users.id` `ON DELETE CASCADE`                 |
| `family_id`  | `UUID`          | groups a rotation chain                             |
| `token_hash` | `VARCHAR(64)`   | **unique**, SHA-256 of the token — never the token  |
| `expires_at` | `TIMESTAMPTZ`   | absolute expiry                                     |
| `revoked_at` | `TIMESTAMPTZ`   | nullable; set on rotation, logout or reuse          |

Index: `(user_id, family_id)`.

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
| **User**       | Cascades: all of the user's categories, transactions **and** refresh tokens are deleted (`ON DELETE CASCADE`, mirrored by ORM `cascade="all, delete-orphan"` + `passive_deletes=True`). |
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

Revisions:

| Revision              | Contents                                                |
| --------------------- | ------------------------------------------------------- |
| `0001_initial`        | `transaction_type` enum, `users`, `categories`, `transactions` |
| `0002_refresh_tokens` | `refresh_tokens`                                        |

Downgrading to `base` drops every table *and* the shared `transaction_type`
enum, so a subsequent upgrade starts from a truly empty database. To roll back
only the auth revision: `alembic downgrade 0001_initial`.

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

## Authentication

### Flow

1. **Register** (`POST /api/v1/auth/register`) — the email is normalized
   (trimmed, lower-cased) and the password is checked against the policy
   (10–128 characters, at least one letter and one digit) and hashed with
   Argon2id. The account is logged in immediately.
2. **Login** (`POST /api/v1/auth/login`) — verifies the hash and issues a new
   token pair.
3. Both return a **short-lived JWT access token in the response body** (the SPA
   keeps it in memory, never in `localStorage`) and set the **refresh token as
   an HttpOnly cookie**.
4. **Refresh** (`POST /api/v1/auth/refresh`) — reads the cookie, revokes that
   token and issues a successor in the same family (rotation), returning a new
   access token.
5. **Logout** (`POST /api/v1/auth/logout`) — revokes the whole family and
   expires the cookie.
6. **`GET /api/v1/users/me`** — requires `Authorization: Bearer <access token>`.

### Tokens and cookie

| | Access token | Refresh token |
| --- | --- | --- |
| Format   | JWT (`HS256`), claims `sub`, `type`, `iat`, `exp`, `jti` | opaque, 256-bit `secrets.token_urlsafe(32)` |
| Lifetime | `ACCESS_TOKEN_EXPIRE_MINUTES` (15) | `REFRESH_TOKEN_EXPIRE_DAYS` (14) |
| Transport| response body → in-memory on the client | `HttpOnly` cookie, `Path=/api/v1/auth` |
| Storage  | not persisted server-side | only its SHA-256 digest in `refresh_tokens` |

The cookie is always `HttpOnly` and path-scoped so it is not attached to
ordinary API calls; `Secure` and `SameSite` come from `COOKIE_SECURE` /
`COOKIE_SAMESITE` (`false`/`lax` for local http, `true`/`none` for a Vercel
frontend calling a Railway backend).

### Security decisions

- **Argon2id** (`argon2-cffi` defaults) for passwords; unknown-email logins
  still verify against a dummy hash so response time does not reveal whether an
  account exists.
- **Generic errors**: every login failure returns `401 Invalid email or
  password`; every token failure returns `401 Invalid or expired credentials`;
  duplicate registration returns a non-specific `409`.
- **Reuse detection**: presenting an already-revoked refresh token revokes its
  entire family, logging out both the legitimate client and the thief.
- **Inactive users** cannot log in, refresh, or use an already-issued access
  token.
- **Rate limiting** (slowapi, per client IP) on register, login and refresh,
  returning a generic `429`.
- Access tokens are validated for signature, expiry, algorithm and `type`, so a
  refresh token can never be used as a bearer token.

### Endpoint examples

```bash
# register (also logs in) -> 201
curl -i -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -c cookies.txt \
  -d '{"email":"user@example.com","password":"correct-horse-9","full_name":"Ada"}'

# login -> 200 {"access_token": "...", "token_type": "bearer", "expires_in": 900, "user": {...}}
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' -c cookies.txt \
  -d '{"email":"user@example.com","password":"correct-horse-9"}'

# current user -> 200
curl http://localhost:8000/api/v1/users/me -H "Authorization: Bearer $ACCESS_TOKEN"

# rotate the refresh cookie -> 200 (new access token + new cookie)
curl -X POST http://localhost:8000/api/v1/auth/refresh -b cookies.txt -c cookies.txt

# logout -> 204 (family revoked, cookie cleared)
curl -i -X POST http://localhost:8000/api/v1/auth/logout -b cookies.txt
```

## Application API

All routes below require `Authorization: Bearer <access token>` and only ever
touch the authenticated user's own rows.

| Method                 | Path                                | Notes                                                              |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| `GET`                  | `/api/v1/categories`                | optional `type=income\|expense`                                     |
| `POST`                 | `/api/v1/categories`                | `409` on a duplicate `(name, type)`                                  |
| `GET/PATCH/DELETE`     | `/api/v1/categories/{id}`           | delete keeps transactions (`category_id → NULL`)                     |
| `GET`                  | `/api/v1/transactions`              | `q`, `type`, `category_id`, `date_from`, `date_to`, `sort`, `order`, `page`, `page_size` |
| `POST`                 | `/api/v1/transactions`              | category must be owned and match the entry type                      |
| `GET/PATCH/DELETE`     | `/api/v1/transactions/{id}`         |                                                                      |
| `GET`                  | `/api/v1/transactions/export.csv`   | same filters as the list endpoint                                    |
| `GET`                  | `/api/v1/reports/summary`           | totals + balance, optional date range                                |
| `GET`                  | `/api/v1/reports/monthly`           | `months` (default 6), zero-filled series                             |
| `GET`                  | `/api/v1/reports/by-category`       | `type` (default `expense`), optional date range                      |

```bash
# filtered, sorted, paginated list
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  'http://localhost:8000/api/v1/transactions?q=coffee&type=expense&date_from=2026-01-01&sort=amount&order=desc&page=1&page_size=20'

# CSV export of the same selection
curl -H "Authorization: Bearer $ACCESS_TOKEN" -OJ \
  'http://localhost:8000/api/v1/transactions/export.csv?type=expense&date_from=2026-01-01'
```

Errors are always `{"detail": "..."}`: `400` for a broken business rule (bad
date range, category/type mismatch), `404` for a missing or foreign resource,
`409` for a duplicate category and `422` for schema validation.

## Deployment

Backend and database on **Railway**, frontend on **Vercel**. The two are on
different sites, so the refresh cookie must be cross-site (`Secure` +
`SameSite=None`) and the API must allow the Vercel origin with credentials.

### 1. Railway PostgreSQL

In a Railway project: **New → Database → PostgreSQL**. Nothing else to
configure; the service publishes `DATABASE_URL`.

### 2. Railway backend

**New → GitHub Repo →** this repository, then in the service settings set
**Root Directory** to `backend`. `backend/railway.json` supplies the rest:
Docker build, `alembic upgrade head` as the pre-deploy command, the start
command bound to Railway's `$PORT`, and `/api/v1/health` as the healthcheck.
Generate a public domain under **Settings → Networking**.

Required variables (**Variables** tab):

| Variable               | Value                                              |
| ---------------------- | -------------------------------------------------- |
| `DATABASE_URL`         | `${{Postgres.DATABASE_URL}}` (reference the DB service) |
| `ENVIRONMENT`          | `production`                                        |
| `JWT_SECRET_KEY`       | 32+ chars, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `BACKEND_CORS_ORIGINS` | `https://<your-app>.vercel.app` (comma-separated list) |
| `COOKIE_SECURE`        | `true`                                              |
| `COOKIE_SAMESITE`      | `none`                                              |

The app rewrites Railway's driverless `postgres://` URL to
`postgresql+psycopg://` itself, refuses to boot in production with a weak
`JWT_SECRET_KEY`, and rejects `SameSite=None` without `Secure`.

Migrations run automatically before each deploy; to run them by hand:

```bash
railway run --service <backend-service> alembic upgrade head
```

Verify: `curl https://<backend>.up.railway.app/api/v1/health` → `{"status":"ok", ...}`.

### 3. Vercel frontend

Import the repository (root of the repo — `vercel.json` builds `frontend/` and
rewrites every path to `index.html` so client-side routes survive a refresh).

| Variable       | Value                                                   |
| -------------- | ------------------------------------------------------- |
| `VITE_API_URL` | `https://<backend>.up.railway.app/api/v1` (include `/api/v1`) |

Vite inlines the value at build time, so **redeploy after changing it**.

### 4. Point the backend at the final Vercel domain

Once Vercel gives you the production domain, set `BACKEND_CORS_ORIGINS` on
Railway to exactly that origin (scheme + host, no trailing slash) and redeploy
the backend. Preview deployments have their own domains — add them to the same
comma-separated list if you want them to reach the API:

```
BACKEND_CORS_ORIGINS=https://expense-tracker.vercel.app,https://expense-tracker-git-main-you.vercel.app
```

Symptoms of a mismatch: login works but the session is gone after a refresh
(cookie blocked → check `COOKIE_SECURE`/`COOKIE_SAMESITE`), or requests fail in
the browser with a CORS error while `curl` succeeds (origin not in the list).

## Roadmap

Phase 0 scaffold → Phase 1 data layer → Phase 2 authentication → MVP (category
and transaction APIs, reports, CSV export, React frontend) → **deployment
(this)**. Future enhancements are listed in the architecture document.
