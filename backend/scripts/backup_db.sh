#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is required (PostgreSQL client tools)." >&2
  exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

STAMP=$(date +"%Y%m%d_%H%M%S")
OUT_FILE="$BACKUP_DIR/hotel_cash_$STAMP.dump"

pg_dump "$DATABASE_URL" -Fc -f "$OUT_FILE"

echo "Backup created: $OUT_FILE"
