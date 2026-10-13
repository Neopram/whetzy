"""D-4 (dueño, 2026-10-12): las tareas de arranque pasan al pre-deploy de Railway.

`start.sh` las sigue corriendo salvo que el dueño haya activado el pre-deploy
(`BOOT_TASKS_IN_PREDEPLOY=1`) **y** el esquema ya esté en la cabeza. Así este
cambio se puede fusionar antes que el ajuste del panel, y una variable puesta
sin el pre-deploy nunca arranca el servidor sobre un esquema viejo.

Se ejecuta el script real con `alembic`, `python` y `gunicorn` falsos en el
PATH, que solo apuntan en un log que se les llamó.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _fake_bin(tmp: Path, alembic_current: str) -> Path:
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    log = tmp / "calls.log"
    for name in ("python", "gunicorn"):
        (bin_dir / name).write_text(f'#!/bin/sh\necho "{name} $*" >> {log}\n')
    (bin_dir / "alembic").write_text(
        f'#!/bin/sh\necho "alembic $*" >> {log}\n'
        f'[ "$1" = current ] && echo "{alembic_current}"\nexit 0\n'
    )
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    return bin_dir


def _run(tmp: Path, *, predeploy: str | None, current: str) -> list[str]:
    bin_dir = _fake_bin(tmp, current)
    env = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "DATABASE_URL": "postgresql://x",
        "ENVIRONMENT": "production",
    }
    if predeploy is not None:
        env["BOOT_TASKS_IN_PREDEPLOY"] = predeploy
    r = subprocess.run(
        ["bash", str(SCRIPTS / "start.sh")], env=env, capture_output=True, text=True, timeout=30, check=False
    )
    assert r.returncode == 0, r.stderr
    return (tmp / "calls.log").read_text().splitlines()


def test_without_predeploy_start_runs_every_boot_task(tmp_path: Path) -> None:
    calls = _run(tmp_path, predeploy=None, current="20261010_tutor_tokens (head)")
    assert "alembic upgrade head" in calls
    assert "python -m app.services.content_loader" in calls
    assert "python -m app.services.bootstrap_owner" in calls
    assert calls[-1].startswith("gunicorn app.main:app")


def test_with_predeploy_and_schema_at_head_start_only_serves(tmp_path: Path) -> None:
    calls = _run(tmp_path, predeploy="1", current="20261010_tutor_tokens (head)")
    assert "alembic upgrade head" not in calls
    assert not any("content_loader" in c for c in calls)
    assert calls[-1].startswith("gunicorn app.main:app")


def test_flag_without_a_migrated_schema_still_migrates(tmp_path: Path) -> None:
    """La variable puesta sin el pre-deploy: el esquema no está en la cabeza."""
    calls = _run(tmp_path, predeploy="1", current="20261004_current_question_id")
    assert "alembic upgrade head" in calls
    assert calls[-1].startswith("gunicorn app.main:app")


@pytest.mark.parametrize("missing", ["DATABASE_URL", "ENVIRONMENT"])
def test_boot_tasks_refuse_to_run_without_their_environment(tmp_path: Path, missing: str) -> None:
    env = {"PATH": os.environ["PATH"], "DATABASE_URL": "x", "ENVIRONMENT": "production"}
    del env[missing]
    r = subprocess.run(
        ["bash", str(SCRIPTS / "boot_tasks.sh")], env=env, capture_output=True, text=True, timeout=30, check=False
    )
    assert r.returncode == 1
    assert missing in r.stderr
