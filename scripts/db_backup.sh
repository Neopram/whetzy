#!/usr/bin/env bash
# db_backup.sh — Create a compressed PostgreSQL backup.
#
# Usage:
#   ./scripts/db_backup.sh [output_file]
#
# Environment variables (override defaults via .env or export):
#   DB_HOST     default: localhost
#   DB_PORT     default: 5433 (local Docker); set 5432 for Railway tunnel
#   DB_USER     default: neurium
#   DB_NAME     default: neurium
#   PGPASSWORD  required (set it or use a .pgpass file)
#
# Examples:
#   PGPASSWORD=neurium_dev ./scripts/db_backup.sh
#   PGPASSWORD=neurium_dev ./scripts/db_backup.sh backups/before_migration.dump
#
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-neurium}"
DB_NAME="${DB_NAME:-neurium}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEFAULT_OUT="backups/${DB_NAME}_${TIMESTAMP}.dump"
OUTPUT="${1:-$DEFAULT_OUT}"

mkdir -p "$(dirname "$OUTPUT")"

echo "[backup] Dumping $DB_NAME from $DB_HOST:$DB_PORT → $OUTPUT"

pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --format=custom \
  --compress=9 \
  --no-acl \
  --no-owner \
  --file="$OUTPUT"

SIZE=$(du -sh "$OUTPUT" | cut -f1)
echo "[backup] Done — $OUTPUT ($SIZE)"
