# Hotel Cash Management System

This repo contains a FastAPI backend and a React (Vite) frontend scaffold.

## Structure

- backend/ - FastAPI app
- frontend/ - React SPA

## Quick Start

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Production

See `/Users/vinodmodukuri/Downloads/Image_Inputs/HOTEL_Expense_Tracker/PRODUCTION.md`.

Heroku guide:
`/Users/vinodmodukuri/Downloads/Image_Inputs/HOTEL_Expense_Tracker/HEROKU.md`
