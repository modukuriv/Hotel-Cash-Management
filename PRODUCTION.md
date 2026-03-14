# Production Deployment Guide

**Goal**
Deploy the Hotel Cash Management System securely with repeatable migrations, safe secrets, and operational monitoring.

**Pre‑Deploy Checklist**
1. Set `ENV=production`.
2. Set a strong `JWT_SECRET` (32+ chars).
3. Set `ALLOWED_ORIGINS` to your frontend domain(s).
4. Ensure `ALLOW_ADMIN_NO_TOTP=false`.
5. Configure a production database (`DATABASE_URL`).
6. Apply migrations with Alembic.
7. Disable dev seeding in production.

**Required Environment Variables**
```bash
ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/hotel_cash
JWT_SECRET=replace-with-strong-secret
ALLOWED_ORIGINS=https://your-frontend.com
ALLOW_ADMIN_NO_TOTP=false
```

**Database Migrations**
```bash
cd backend
python3 -m alembic upgrade head
```

**Run (Docker Compose)**
```bash
docker compose up --build
```

**Reverse Proxy + TLS**
Use a reverse proxy (Nginx, Traefik, or your cloud load balancer) to terminate TLS.
Configure it to forward `X-Forwarded-For` and `X-Forwarded-Proto`.

**Health & Readiness**
- `GET /api/health` returns `ok` when the API is up.
- `GET /api/ready` checks DB connectivity.

**Backups**
1. Daily database backups (pg_dump or managed DB snapshots).
2. Periodic restore test.

**Observability**
1. Centralized logs (structured logs already include `X-Request-Id`).
2. Error tracking (Sentry or similar).
3. Alerts on 5xx spikes, DB errors, and latency.

**Security**
1. Enforce Google Authenticator (TOTP) for non‑admin users.
2. Disable admin TOTP bypass in production.
3. Rotate JWT secrets on schedule.
4. Ensure CORS is restricted to known domains.

**Scaling**
1. Increase API workers in Dockerfile or switch to Gunicorn with Uvicorn workers.
2. Add Redis if you need shared rate‑limiting or background tasks at scale.
3. Move static frontend to CDN for faster delivery.

# Backups & Restore

**Backup (PostgreSQL)**
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/hotel_cash
./backend/scripts/backup_db.sh
```

**Restore**
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/hotel_cash
./backend/scripts/restore_db.sh ./backups/hotel_cash_YYYYMMDD_HHMMSS.dump
```

**Recommendations**
- Run backups daily (cron or scheduler).
- Keep 7–30 days of rolling backups.
- Test restore monthly.

# Monitoring (Sentry)

Set the Sentry DSN to enable error tracking:
```bash
SENTRY_DSN=https://<key>@sentry.io/<project>
SENTRY_TRACES_SAMPLE_RATE=0.1
```

If `SENTRY_DSN` is empty, Sentry is disabled.
