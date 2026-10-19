"""45.4: buzón de prueba para el e2e de la serie 45.

La puerta de cierre (registro → correo en español → verificar) necesita leer
el enlace del correo que el backend de prueba «manda». Con el proveedor `log`
solo quedaba en el log el asunto y el tamaño. `EMAIL_OUTBOX_DIR` (vacío por
defecto) guarda cada correo como JSON en esa carpeta; en producción nunca, y
sin la variable, tampoco.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.services import email as email_service


def _files(d: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]


def test_writes_each_email_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_OUTBOX_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    email_service._send_log("ana@example.com", "Verifica tu email en Whetzy", "<a href='x'>x</a>")
    email_service._send_log("ana@example.com", "Bienvenido/a", "<p>hola</p>")
    got = _files(tmp_path)
    assert [g["subject"] for g in got] == ["Verifica tu email en Whetzy", "Bienvenido/a"]
    assert got[0]["to"] == "ana@example.com"
    assert got[0]["html"] == "<a href='x'>x</a>"


def test_never_in_production(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_OUTBOX_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    email_service._send_log("ana@example.com", "s", "<p>h</p>")
    assert _files(tmp_path) == []


def test_off_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert settings.model_fields["EMAIL_OUTBOX_DIR"].default == ""
    monkeypatch.setattr(settings, "EMAIL_OUTBOX_DIR", "", raising=False)
    monkeypatch.chdir(tmp_path)
    email_service._send_log("ana@example.com", "s", "<p>h</p>")
    assert list(tmp_path.rglob("*.json")) == []
