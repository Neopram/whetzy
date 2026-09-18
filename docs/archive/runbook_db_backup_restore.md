# Runbook: DB backup / restore

**Acceptance evidence**: `scripts/db_restore_test.sh` ran locally and printed ✅ for all 6 core tables (users×39, questions×1253, tracks×7, modules×49, skills×207, study_sessions×41) — see commit message for full output.

---

## Quick reference

| Script | Purpose |
|---|---|
| `scripts/db_backup.sh [out.dump]` | Dump the DB to a compressed custom-format file |
| `scripts/db_restore.sh <file> [db]` | Restore into an existing (empty) database |
| `scripts/db_restore_test.sh [file]` | Full backup→restore→verify→cleanup smoke test |

All scripts read `PGPASSWORD`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` from the environment; sane defaults ship for the local Docker setup.

---

## Local Docker DB

```
Host: localhost   Port: 5433   User: neurium   DB: neurium
```

### Take a backup

```bash
PGPASSWORD=neurium_dev ./scripts/db_backup.sh
# → backups/neurium_YYYYMMDD_HHMMSS.dump
```

### Restore-test against ephemeral DB

```bash
PGPASSWORD=neurium_dev ./scripts/db_restore_test.sh
```

Expected output (trimmed):
```
[backup] Done — /tmp/neurium_restore_test_NNN.dump (540K)
[restore] Done — neurium_restore_test_NNN restored successfully.
[test]   ✅ users: 39 rows
[test]   ✅ questions: 1253 rows
...
[test] ✅ Restore test PASSED — all tables match.
```

The temp DB and dump file are always cleaned up on exit (via `trap cleanup EXIT`), even on failure.

---

## Production (Railway)

Railway exposes a `DATABASE_PUBLIC_URL` in the service's variable panel. Use a local tunnel or the Railway CLI:

```bash
# Option 1: Railway CLI proxy (recommended — TLS, no port forwarding needed)
railway connect --service whetzy-db
# Then in another terminal:
DB_HOST=localhost DB_PORT=5432 PGPASSWORD=<railway-password> \
  ./scripts/db_backup.sh backups/prod_$(date +%Y%m%d).dump

# Option 2: Direct URL (if Railway exposes a public port)
DB_HOST=<public-host> DB_PORT=<port> DB_USER=postgres \
  PGPASSWORD=<password> DB_NAME=railway \
  ./scripts/db_backup.sh
```

Store production backups off-machine (S3, Backblaze, etc.); never commit them to the repo.

---

## Before a production migration

```bash
# 1. Backup production
PGPASSWORD=<prod-pass> DB_HOST=<prod-host> DB_PORT=5432 DB_USER=postgres DB_NAME=railway \
  ./scripts/db_backup.sh backups/pre_migration_$(date +%Y%m%d_%H%M%S).dump

# 2. Run the migration (Alembic on Railway via railway run, or CI deploy)
# 3. If something goes wrong: restore to a fresh DB (or rollback Alembic)
```

---

## Restore to a new local database

```bash
# Create an empty target database
PGPASSWORD=neurium_dev createdb --host=localhost --port=5433 --username=neurium neurium_recovery

# Restore
PGPASSWORD=neurium_dev ./scripts/db_restore.sh backups/neurium_20260908.dump neurium_recovery
```

The restore script filters the benign `transaction_timeout` warning that `pg_dump ≥ v17` emits when dumping a `pg16` server, then verifies the `users` table exists before reporting success.

---

## Recovery checklist

1. Identify the last clean backup (`ls -lht backups/`).
2. Create a fresh, empty target database (`createdb ...`).
3. Run `db_restore.sh <backup> <target>` — watch for errors.
4. Point `DATABASE_URL` at the restored database and smoke-test: `GET /health/ready`.
5. Run `db_restore_test.sh <backup>` to confirm row parity (skip the backup step by passing the file directly).
6. If satisfied, swap traffic to the restored database.

---

*Last tested: 2026-09-08 — 1253 questions, 7 tracks, 207 skills restored in < 5 s from a 544 KB dump.*
