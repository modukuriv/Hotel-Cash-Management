#!/usr/bin/env bash
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup_file.dump>" >&2
  exit 1
fi

BACKUP_FILE="$1"

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore is required (PostgreSQL client tools)." >&2
  exit 1
fi

pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "$BACKUP_FILE"

echo "Restore completed: $BACKUP_FILE"
