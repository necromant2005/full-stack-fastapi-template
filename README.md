# Full Stack FastAPI Template

[![Test Docker Compose](../../actions/workflows/test-docker-compose.yml/badge.svg)](../../actions/workflows/test-docker-compose.yml)
[![Test Backend](../../actions/workflows/test-backend.yml/badge.svg)](../../actions/workflows/test-backend.yml)

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
  - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
  - 🧩 Built into the backend application and served by FastAPI on the same domain as the API.
  - 💃 Using TypeScript, hooks, [Vite](https://vitejs.dev), and other parts of a modern frontend stack.
  - 🎨 [Tailwind CSS](https://tailwindcss.com) and [shadcn/ui](https://ui.shadcn.com) for the frontend components.
  - 🤖 An automatically generated frontend client.
  - 🧪 [Playwright](https://playwright.dev) for end-to-end testing.
  - 🦇 Dark mode support.
- ☁️ [FastAPI Cloud](https://fastapicloud.com) for deployment.
- 🐋 [Docker Compose](https://www.docker.com) for local services and self-hosted deployment.
  - 📞 [Traefik](https://traefik.io) as a reverse proxy with automatic HTTPS.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email-based password recovery.
- 📬 [Mailcatcher](https://mailcatcher.me) for local email testing during development.
- ✅ Tests with [Pytest](https://pytest.org).
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Dashboard Login

![Dashboard login screenshot](img/login.png)

### Dashboard - Admin

![Admin dashboard screenshot](img/dashboard.png)

### Dashboard - Items

![Items dashboard screenshot](img/dashboard-items.png)

### Dashboard - Dark Mode

![Dark mode dashboard screenshot](img/dashboard-dark.png)

### Interactive API Documentation

![API docs](img/docs.png)

## How to Use It

Click the **Use this template** button at the top of this page to create a new repository.

## Run the Assignment Locally

The primary setup requires Git, Docker, and Docker Compose v2. Python, uv, Bun,
PostgreSQL, and application dependencies are installed inside the project images.

Prepare local configuration after cloning:

```bash
cp .env.example .env
openssl rand -hex 32
```

Edit `.env` and replace every `changethis` value. Use the generated value for
`SECRET_KEY`, choose a local PostgreSQL password, and set the bootstrap admin email
and temporary password. `.env` is ignored by Git and must not contain deployment
credentials.

Apply migrations, create the first administrator, and start the application:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d --build --wait backend mailcatcher adminer proxy
```

Open the application at <http://localhost:8000> and API documentation at
<http://localhost:8000/docs>. The first administrator must replace the configured
temporary password immediately after login. Stop the stack without deleting the
database with `docker compose down`; add `-v` only when intentionally resetting all
local data.

Host-based development with uv and Bun is optional and documented in
[development.md](./development.md).

## Role-Based Access Control

Users have one constrained database role: `admin`, `manager`, or `member`. A small
backend role-permission map is the single policy definition. FastAPI dependencies
enforce permissions before handlers run, while resource handlers retain explicit
ownership checks where object identity matters.

JWTs contain only the user ID. The backend loads the current user and role from
PostgreSQL on each request, so deactivation and permission changes take effect
immediately. Authentication failures return `401`; authenticated users without a
required capability receive `403`.

The frontend reads capabilities from `GET /api/v1/users/me`. It uses them to hide
unavailable navigation and actions and to show a friendly Access Denied page for
direct navigation. These UI checks improve usability; backend dependencies remain
the security boundary.

| Action | admin | manager | member |
|---|:---:|:---:|:---:|
| List users | ✓ | ✓ | — |
| Create and manage users | ✓ | — | — |
| View metrics | ✓ | ✓ | — |
| View and update own profile | ✓ | ✓ | ✓ |

The complete contract and edge cases are in [docs/rbac.md](./docs/rbac.md).
Architectural decisions are recorded in
[ADR 0001](./docs/adr/0001-authorization-pattern.md) and
[ADR 0002](./docs/adr/0002-bootstrap-admin-safety.md).

### First Administrator

Set a one-time administrator email and temporary password in `.env`:

```env
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_TEMPORARY_PASSWORD=<secure-temporary-password>
```

On a fresh database, `backend/scripts/prestart.sh` applies migrations and creates
the administrator. The first login is restricted to the password-change screen.
After changing the password, the temporary password variable may be removed.
Restarting the application never resets an existing account. Administrators may
change their email normally because startup detects them by role, not by the
original bootstrap email.

If direct database changes leave no active administrator, startup fails safely.
Run the interactive recovery command; it will prompt for a temporary password and
require its replacement at login:

```bash
docker compose run --rm backend \
  python scripts/recover_admin.py --email admin@example.com
```

### Seed Test Users

The bootstrap step above creates the administrator. Create development-only manager
and member accounts explicitly:

```bash
docker compose run --rm backend python scripts/seed_demo_users.py \
  --temporary-password '<temporary-password>'
```

Seeded accounts are `manager@example.com` and `member@example.com`. Existing
accounts and passwords are left unchanged, and each new account must replace its
temporary password.

### Run Tests

Run backend tests against a disposable PostgreSQL database. This command builds the
image, applies migrations, runs the suite, and removes the isolated containers and
volume without touching the development database:

```bash
bash scripts/test.sh
```

Run browser tests with the same disposable-database guarantee:

```bash
bash scripts/test-e2e.sh
```

For optional host-side frontend development, install Bun and run:

```bash
bun install
bun run --filter frontend build
```

### Database Migrations

`scripts/prestart.sh` automatically applies all committed migrations. Inspect or
apply them manually with:

```bash
docker compose run --rm backend alembic current
docker compose run --rm backend alembic upgrade head
```

Verify a downgrade and re-upgrade only against a disposable database:

```bash
docker compose -f compose.test.yml run --rm --build backend-tests \
  bash -c 'alembic upgrade head && alembic downgrade -1 && alembic upgrade head'
docker compose -f compose.test.yml down -v --remove-orphans
```

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

FastAPI Cloud deployment: [deployment.md](./deployment.md).

Self-hosted deployment with Docker Compose: [deployment-docker-compose.md](./deployment-docker-compose.md).

## Development

General development docs: [development.md](./development.md).

This includes the local FastAPI and Vite workflow, Docker Compose services, `.env` configuration, and more.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
