# Heroku Deployment

This project can be deployed as a single Heroku app (FastAPI + React static build).

## Prerequisites
- Heroku CLI installed
- Heroku account

## Create app + database

```bash
heroku login
heroku create <your-app-name>
heroku addons:create heroku-postgresql:essential-0 -a <your-app-name>
```

## Add buildpacks (Node first, then Python)

```bash
heroku buildpacks:set heroku/nodejs -a <your-app-name>
heroku buildpacks:add --index 2 heroku/python -a <your-app-name>
```

## Configure environment variables

```bash
heroku config:set ENV=production -a <your-app-name>
heroku config:set JWT_SECRET="<long-random-32+chars>" -a <your-app-name>
heroku config:set ALLOWED_ORIGINS="https://<your-app-name>.herokuapp.com" -a <your-app-name>
```

Optional:

```bash
heroku config:set SENTRY_DSN="" -a <your-app-name>
```

## Deploy

```bash
git push heroku main
```

## Run migrations + seed admin

```bash
heroku run bash -a <your-app-name> -c "cd backend && python -m alembic upgrade head"
heroku run bash -a <your-app-name> -c "python backend/scripts/bootstrap_seed.py"
```

The bootstrap prints a Google Authenticator provisioning URI for the admin account.

## CI/CD (GitHub Actions)

This repo includes a GitHub Actions workflow to deploy on every push to `main`.
Set these GitHub repository secrets:

- `HEROKU_API_KEY`
- `HEROKU_APP_NAME`

Workflow file:
`/Users/vinodmodukuri/Downloads/Image_Inputs/HOTEL_Expense_Tracker/.github/workflows/deploy-heroku.yml`

Bootstrap config (optional env vars):

- `BOOTSTRAP_TENANT_NAME` (default: Wingate)
- `BOOTSTRAP_TENANT_ADDRESS`
- `BOOTSTRAP_TENANT_TIMEZONE`
- `BOOTSTRAP_ADMIN_EMAIL` (default: vmodukuri@outlook.com)
- `BOOTSTRAP_ADMIN_FIRST_NAME`
- `BOOTSTRAP_ADMIN_LAST_NAME`

## Login
- Email: `vmodukuri@outlook.com`
- Code: Google Authenticator 6‑digit code

## Notes
- The React app is built during deploy and served by FastAPI from `/`.
- API is available at `/api/*`.
- Update `ALLOWED_ORIGINS` if you use a custom domain.
