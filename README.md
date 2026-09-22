# Authentication Security Lab

Vaulta is a fictional financial-management SaaS built as a local authentication security laboratory. The vulnerable release is developed as one coherent application; vulnerabilities are implementation decisions inside normal product features, not independent demo pages.

> **WARNING: This application is intentionally vulnerable. Run it only in an isolated/local environment. Do not expose it to the Internet.**

The project foundation, registration, authentication, recovery, organizations, sessions, MFA/TOTP, financial dashboard, account preferences and system administration are available. All 15 intentional scenarios are tracked only in the internal threat model and characterization tests.

## Quick start with Docker

Requirements: Docker Engine with Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

Open <http://127.0.0.1:8000>. Both the web service and database are bound to loopback only.

Useful commands:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_dev
docker compose exec web python manage.py test ../tests --settings=config.settings.test
docker compose down
```

Do not reuse any `.env` value or seeded credential outside this lab. The development email backend writes messages to the application console. If port 8000 is occupied, set `WEB_PORT=18000` (or another loopback port) in `.env`.

## Local development without Docker

See [docs/setup.md](docs/setup.md). PostgreSQL is the normal development database; the isolated test settings use SQLite for fast, dependency-light tests.

## Documentation

- [Architecture](docs/architecture.md)
- [Setup and operations](docs/setup.md)
- [Development accounts](docs/development-accounts.md)
- [Threat model and internal vulnerability matrix](docs/threat-model.md)
- [Implementation phases](docs/implementation-plan.md)
- [Vulnerability workspace](vulnerabilities/README.md)

## Git strategy

Feature branches represent product capabilities (`feat/project-setup`, `feat/user-registration`, `feat/authentication-flow`, and so on). Intentional flaws are built into those capabilities. The stable vulnerable application will later be tagged `v1.0-vulnerable`. Finding-specific `fix/AUTH-*` branches belong only to the later remediation stage.

No public deployment configuration is provided or supported.
