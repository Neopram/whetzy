#!/usr/bin/env bash
# db_restore_test.sh — Smoke-test the full backup→restore cycle.
#
# Creates an ephemeral database, restores a fresh backup into it, verifies
# that core tables and row counts match the source, then drops the temp DB.
#
# Usage:
#   PGPASSWORD=<pass> ./scripts/db_restore_test.sh
#   PGPASSWORD=<pass> ./scripts/db_restore_test.sh backups/my.dump   # use existing dump
#
# Exits 0 on success, non-zero on any failure.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-neurium}"
DB_NAME="${DB_NAME:-neurium}"

TEMP_DB="neurium_restore_test_$$"
BACKUP_FILE="${1:-}"
CREATED_BACKUP=false

PSQL() {
  psql --host="$DB_HOST" --port="$DB_PORT" --username="$DB_USER" --no-password -t -c "$@"
}

cleanup() {
  echo
  echo "[test] Cleaning up ephemeral database: $TEMP_DB"
  PSQL "DROP DATABASE IF EXISTS $TEMP_DB;" postgres 2>/dev/null || true
  if [[ "$CREATED_BACKUP" == "true" && -f "$BACKUP_FILE" ]]; then
    rm -f "$BACKUP_FILE"
    echo "[test] Removed temporary backup: $BACKUP_FILE"
  fi
}
trap cleanup EXIT

# ── Step 1: take a fresh backup if none was provided ────────────────────────
if [[ -z "$BACKUP_FILE" ]]; then
  BACKUP_FILE="/tmp/neurium_restore_test_$$.dump"
  CREATED_BACKUP=true
  echo "[test] Taking fresh backup from $DB_NAME …"
  "$SCRIPT_DIR/db_backup.sh" "$BACKUP_FILE"
else
  echo "[test] Using provided backup: $BACKUP_FILE"
fi

# ── Step 2: create the ephemeral DB ─────────────────────────────────────────
echo "[test] Creating ephemeral database: $TEMP_DB"
PSQL "CREATE DATABASE $TEMP_DB;" postgres

# ── Step 3: restore ─────────────────────────────────────────────────────────
echo "[test] Restoring into $TEMP_DB …"
"$SCRIPT_DIR/db_restore.sh" "$BACKUP_FILE" "$TEMP_DB"

# ── Step 4: verify core tables and row parity ────────────────────────────────
echo "[test] Verifying tables …"
TABLES=(users questions tracks modules skills study_sessions)
PASS=true

for TABLE in "${TABLES[@]}"; do
  SRC_COUNT=$(PSQL "SELECT COUNT(*) FROM $TABLE;" "$DB_NAME" | tr -d '[:space:]')
  DST_COUNT=$(PSQL "SELECT COUNT(*) FROM $TABLE;" "$TEMP_DB" | tr -d '[:space:]')
  if [[ "$SRC_COUNT" == "$DST_COUNT" ]]; then
    echo "[test]   ✅ $TABLE: $SRC_COUNT rows"
  else
    echo "[test]   ❌ $TABLE: source=$SRC_COUNT, restored=$DST_COUNT"
    PASS=false
  fi
done

if [[ "$PASS" == "true" ]]; then
  echo
  echo "[test] ✅ Restore test PASSED — all tables match."
else
  echo
  echo "[test] ❌ Restore test FAILED — row count mismatch."
  exit 1
fi

# ── Step 5: truncated dump must fail ────────────────────────────────────────
echo
echo "[test] Verifying that a truncated dump is detected …"
TRUNC_FILE="/tmp/neurium_truncated_$$.dump"
head -c 512 "$BACKUP_FILE" > "$TRUNC_FILE"
TRUNC_DB="neurium_trunc_test_$$"
PSQL "CREATE DATABASE $TRUNC_DB;" postgres 2>/dev/null || true

if "$SCRIPT_DIR/db_restore.sh" "$TRUNC_FILE" "$TRUNC_DB" >/dev/null 2>&1; then
  TRUNC_COUNT=$(PSQL "SELECT COUNT(*) FROM users;" "$TRUNC_DB" 2>/dev/null | tr -d '[:space:]')
  if [[ "${TRUNC_COUNT:-0}" -gt 0 ]]; then
    echo "[test]   ❌ Truncated dump restored with data — guard failed"
    PSQL "DROP DATABASE IF EXISTS $TRUNC_DB;" postgres 2>/dev/null || true
    rm -f "$TRUNC_FILE"
    exit 1
  fi
fi
echo "[test]   ✅ Truncated dump correctly rejected"
PSQL "DROP DATABASE IF EXISTS $TRUNC_DB;" postgres 2>/dev/null || true
rm -f "$TRUNC_FILE"

# ── Step 6: log result ──────────────────────────────────────────────────────
LOG_FILE="$SCRIPT_DIR/../docs/restore_log.md"
if [[ ! -f "$LOG_FILE" ]]; then
  echo "# Restore drill log" > "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  echo "| Date | Tables OK | Truncated rejected | Notes |" >> "$LOG_FILE"
  echo "|------|-----------|-------------------|-------|" >> "$LOG_FILE"
fi
echo "| $(date -u '+%Y-%m-%d') | ${#TABLES[@]}/${#TABLES[@]} | yes | automated drill |" >> "$LOG_FILE"
echo "[test] Logged to docs/restore_log.md"

exit 0
