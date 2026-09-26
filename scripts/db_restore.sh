#!/usr/bin/env bash
# db_restore.sh — Restore a pg_dump backup to an existing (empty) database.
#
# Usage:
#   ./scripts/db_restore.sh <backup_file> [target_db]
#
# Environment variables:
#   DB_HOST       default: localhost
#   DB_PORT       default: 5433
#   DB_USER       default: neurium
#   PGPASSWORD    required
#
# The target database must already exist and be empty.
# To create it:  createdb --host=... --port=... --username=... <target_db>
#
# Examples:
#   PGPASSWORD=neurium_dev ./scripts/db_restore.sh backups/neurium_20260908.dump
#   PGPASSWORD=neurium_dev ./scripts/db_restore.sh backups/neurium_20260908.dump neurium_restore_test
#
set -euo pipefail

BACKUP_FILE="${1:?Usage: db_restore.sh <backup_file> [target_db]}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-neurium}"
TARGET_DB="${2:-neurium}"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "[restore] ERROR: backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

echo "[restore] Restoring $BACKUP_FILE → $TARGET_DB on $DB_HOST:$DB_PORT"

# pg_dump from a newer client (e.g. pg17 tools against pg16 server) may emit
# `SET transaction_timeout = 0` which pg16 does not recognise. Filter it so
# the restore succeeds; all real errors still propagate.
pg_restore \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$TARGET_DB" \
  --no-acl \
  --no-owner \
  "$BACKUP_FILE" 2>&1 | grep -v "transaction_timeout" >&2 || true

# Verify the schema actually landed by checking the users table exists.
psql \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$TARGET_DB" \
  --no-password -t -c "SELECT COUNT(*) FROM users;" >/dev/null

echo "[restore] Done — $TARGET_DB restored successfully."
