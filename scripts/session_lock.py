"""
Session lock for the Whetzy orchestrator.

The lock file lives at <repo_root>/.session.lock and is gitignored.
If a session finds an existing lock newer than MAX_AGE_HOURS (6h), it exits
with code 3 and logs one line — no other output.

Usage:
    python scripts/session_lock.py acquire <session_id> <model>
    python scripts/session_lock.py release
    python scripts/session_lock.py status

Exit codes:
    0 — success (acquired / released / free)
    3 — lock is held by another session (< 6h old)
    1 — unexpected error
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOCK_FILENAME = ".session.lock"
MAX_AGE_HOURS = 6


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _lock_path() -> Path:
    import os
    override = os.environ.get("WHETZY_LOCK_PATH")
    if override:
        return Path(override)
    return _repo_root() / LOCK_FILENAME


def acquire(session_id: str, model: str) -> bool:
    """
    Write .session.lock.  Returns True on success, False if another
    session holds a fresh lock (< MAX_AGE_HOURS).  Exits with code 3
    when the lock is held and this is called from the CLI.
    """
    path = _lock_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            started = datetime.fromisoformat(data.get("startedAt", ""))
            age = datetime.now(timezone.utc) - started
            if age < timedelta(hours=MAX_AGE_HOURS):
                holder = data.get("sessionId", "unknown")
                return False  # caller decides whether to exit(3)
        except Exception:
            pass  # stale / corrupt lock — overwrite it

    payload = {
        "sessionId": session_id,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return True


def release() -> None:
    """Delete .session.lock if it exists."""
    _lock_path().unlink(missing_ok=True)


def status() -> dict | None:
    """Return lock data dict, or None if no lock exists."""
    path = _lock_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cmd = args[0]

    if cmd == "acquire":
        if len(args) < 3:
            print("Usage: session_lock.py acquire <session_id> <model>", file=sys.stderr)
            sys.exit(1)
        ok = acquire(args[1], args[2])
        if not ok:
            data = status()
            holder = data.get("sessionId", "unknown") if data else "unknown"
            print(f"sesión {holder}: cerrojo ocupado, salgo (exit 3)", file=sys.stderr)
            sys.exit(3)
        print(f"Lock acquired: {args[1]}")

    elif cmd == "release":
        release()
        print("Lock released")

    elif cmd == "status":
        data = status()
        if data:
            print(json.dumps(data, indent=2))
        else:
            print("No lock")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main()
