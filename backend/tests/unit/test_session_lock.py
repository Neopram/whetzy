"""Tests for scripts/session_lock.py (20.0)."""
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Locate the script relative to this test file
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "session_lock.py"
assert SCRIPT.exists(), f"session_lock.py not found at {SCRIPT}"


def _run(args: list[str], env_lock_path: Path | None = None) -> subprocess.CompletedProcess:
    """Run the script via subprocess, optionally overriding the lock path."""
    import os
    env = os.environ.copy()
    if env_lock_path is not None:
        env["WHETZY_LOCK_PATH"] = str(env_lock_path)
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, env=env
    )


def _acquire_direct(session_id: str, model: str, lock_path: Path) -> bool:
    """Call acquire() directly, patching the lock path."""
    # Import the module dynamically so tests are isolated
    import importlib.util
    spec = importlib.util.spec_from_file_location("session_lock", SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    # Monkey-patch _lock_path for this call
    original = mod._lock_path
    mod._lock_path = lambda: lock_path  # type: ignore[assignment]
    try:
        return mod.acquire(session_id, model)
    finally:
        mod._lock_path = original  # type: ignore[assignment]


def _release_direct(lock_path: Path) -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location("session_lock", SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod._lock_path = lambda: lock_path  # type: ignore[assignment]
    mod.release()


class TestSessionLock:
    def test_first_acquire_succeeds(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".session.lock"
        ok = _acquire_direct("session-A", "sonnet", lock_file)
        assert ok is True
        assert lock_file.exists()
        data = json.loads(lock_file.read_text())
        assert data["sessionId"] == "session-A"
        assert data["model"] == "sonnet"

    def test_second_acquire_blocked_within_6h(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".session.lock"
        # First session acquires
        ok1 = _acquire_direct("session-A", "sonnet", lock_file)
        assert ok1 is True
        # Second session (different ID) tries to acquire while lock is fresh
        ok2 = _acquire_direct("session-B", "haiku", lock_file)
        assert ok2 is False
        # Lock still belongs to session-A
        data = json.loads(lock_file.read_text())
        assert data["sessionId"] == "session-A"

    def test_stale_lock_overwritten(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".session.lock"
        # Write a lock older than 6 hours
        old_time = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
        lock_file.write_text(json.dumps({
            "sessionId": "session-old",
            "startedAt": old_time,
            "model": "sonnet",
        }), encoding="utf-8")
        # New session should succeed (stale lock)
        ok = _acquire_direct("session-new", "haiku", lock_file)
        assert ok is True
        data = json.loads(lock_file.read_text())
        assert data["sessionId"] == "session-new"

    def test_release_removes_lock(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".session.lock"
        _acquire_direct("session-A", "sonnet", lock_file)
        assert lock_file.exists()
        _release_direct(lock_file)
        assert not lock_file.exists()

    def test_release_is_idempotent(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".session.lock"
        # Release when no lock exists — no error
        _release_direct(lock_file)
        _release_direct(lock_file)

    def test_simulated_two_runs_second_exits_3(self, tmp_path: Path) -> None:
        """
        Criterion §20.0: la segunda ejecución sale con exit 3 y una línea en stderr.
        Uses the CLI interface to verify the exit code is exactly 3.
        """
        lock_file = tmp_path / ".session.lock"
        import os
        env = os.environ.copy()
        env["WHETZY_LOCK_PATH"] = str(lock_file)

        # First run: acquire
        r1 = subprocess.run(
            [sys.executable, str(SCRIPT), "acquire", "session-first", "sonnet"],
            capture_output=True, text=True, env=env
        )
        assert r1.returncode == 0, f"First run failed: {r1.stderr}"
        assert lock_file.exists()

        # Second run: should exit 3
        r2 = subprocess.run(
            [sys.executable, str(SCRIPT), "acquire", "session-second", "sonnet"],
            capture_output=True, text=True, env=env
        )
        assert r2.returncode == 3, f"Expected exit 3, got {r2.returncode}. stderr={r2.stderr}"
        # One line in stderr naming the holder
        assert "cerrojo" in r2.stderr or "session-first" in r2.stderr, (
            f"Expected 'cerrojo' or holder name in stderr: {r2.stderr!r}"
        )
