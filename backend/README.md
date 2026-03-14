# Backend (FastAPI)

Quick start:

1. Create and activate a virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```bash
   cp .env.example .env
   ```
4. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

Default dev database is SQLite at `./dev.db` (see `.env`).

Role-based access (dev):
Pass `X-Role` header with values `GLOBAL_ADMIN`, `ADMIN`, or `USER`.
Only `GLOBAL_ADMIN` can delete; `ADMIN` can create/update; `USER` is view-only.

Login (seeded users):
- Email + Google Authenticator code: `vmodukuri@outlook.com`

After seeding, the console prints a TOTP provisioning URI for the admin account.
Scan that URI in Google Authenticator to generate codes.

Dev seed (requires migrations applied first):

```bash
python3 -m alembic upgrade head
python3 scripts/seed_dev.py
```

Migrations (Alembic)

Initialize DB schema (dev):

```bash
python3 -m alembic revision --autogenerate -m "initial schema"
python3 -m alembic upgrade head
```

Note: Alembic reads `DATABASE_URL` from `.env` via `app.core.config`.

Production hardening (required):
1. Set `ENV=production`
2. Set a strong `JWT_SECRET` (32+ chars)
3. Set `ALLOWED_ORIGINS` to your frontend domain(s)
4. Ensure `ALLOW_ADMIN_NO_TOTP=false`

The API will refuse to start in production if these are not set correctly.

Rate limiting:
Login is limited by IP using a sliding window. Configure with:
- `LOGIN_RATE_LIMIT` (default 5)
- `LOGIN_RATE_WINDOW_SECONDS` (default 60)

Logging & Monitoring:
- Request IDs are generated for every request (`X-Request-Id` header).
- Structured logs include the request ID.
- Optional Sentry integration via `SENTRY_DSN`.

Tests:
```bash
python3 -m pip install pytest
pytest
```

Deployment (Docker)
```bash
docker compose up --build
```

Notes:
- Set `JWT_SECRET` to a strong value in production.
- Use a real domain in `ALLOWED_ORIGINS`.
