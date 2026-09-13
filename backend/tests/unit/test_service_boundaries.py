"""Service boundary tests (task 6.7).

Verifies that the three service groups — engine, gamification, content —
expose explicit public interfaces via __all__ and do not import across
group boundaries.

Rules enforced:
  - engine/*    must not import from gamification.* or content services
  - gamification/* must not import from engine.* or content services
  - content services must not import from engine.* or gamification.*
  - engine/__init__.py and gamification/__init__.py must define __all__
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).parent.parent.parent  # backend/

ENGINE_FILES = list((BACKEND / "app/services/engine").glob("*.py"))
GAMIFICATION_FILES = list((BACKEND / "app/services/gamification").glob("*.py"))
CONTENT_FILES = [
    BACKEND / "app/services/content_agent.py",
    BACKEND / "app/services/content_qa.py",
    BACKEND / "app/services/content_loader.py",
    BACKEND / "app/services/duplicate_detector.py",
]


def _imports(path: Path) -> list[str]:
    """Return all module names that `path` imports from."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def _any_import_matches(mods: list[str], prefixes: list[str]) -> list[str]:
    return [m for m in mods for p in prefixes if m.startswith(p)]


# ── engine group must not cross-import ────────────────────────────────────────

@pytest.mark.parametrize("path", ENGINE_FILES, ids=[p.name for p in ENGINE_FILES])
def test_engine_no_gamification_imports(path: Path) -> None:
    bad = _any_import_matches(_imports(path), ["app.services.gamification"])
    assert not bad, f"{path.name} imports gamification: {bad}"


@pytest.mark.parametrize("path", ENGINE_FILES, ids=[p.name for p in ENGINE_FILES])
def test_engine_no_content_imports(path: Path) -> None:
    content_prefixes = [
        "app.services.content_agent",
        "app.services.content_qa",
        "app.services.content_loader",
        "app.services.duplicate_detector",
    ]
    bad = _any_import_matches(_imports(path), content_prefixes)
    assert not bad, f"{path.name} imports content service: {bad}"


# ── gamification group must not cross-import ──────────────────────────────────

@pytest.mark.parametrize("path", GAMIFICATION_FILES, ids=[p.name for p in GAMIFICATION_FILES])
def test_gamification_no_engine_imports(path: Path) -> None:
    bad = _any_import_matches(_imports(path), ["app.services.engine"])
    assert not bad, f"{path.name} imports engine: {bad}"


@pytest.mark.parametrize("path", GAMIFICATION_FILES, ids=[p.name for p in GAMIFICATION_FILES])
def test_gamification_no_content_imports(path: Path) -> None:
    content_prefixes = [
        "app.services.content_agent",
        "app.services.content_qa",
        "app.services.content_loader",
        "app.services.duplicate_detector",
    ]
    bad = _any_import_matches(_imports(path), content_prefixes)
    assert not bad, f"{path.name} imports content service: {bad}"


# ── content group must not cross-import ───────────────────────────────────────

@pytest.mark.parametrize("path", CONTENT_FILES, ids=[p.name for p in CONTENT_FILES])
def test_content_no_engine_imports(path: Path) -> None:
    bad = _any_import_matches(_imports(path), ["app.services.engine"])
    assert not bad, f"{path.name} imports engine: {bad}"


@pytest.mark.parametrize("path", CONTENT_FILES, ids=[p.name for p in CONTENT_FILES])
def test_content_no_gamification_imports(path: Path) -> None:
    bad = _any_import_matches(_imports(path), ["app.services.gamification"])
    assert not bad, f"{path.name} imports gamification: {bad}"


# ── explicit __all__ interfaces exist ─────────────────────────────────────────

def test_engine_package_exports_all() -> None:
    import app.services.engine as engine_pkg
    assert hasattr(engine_pkg, "__all__"), "engine/__init__.py must define __all__"
    assert len(engine_pkg.__all__) >= 5, "engine __all__ should export ≥5 symbols"


def test_gamification_package_exports_all() -> None:
    import app.services.gamification as gam_pkg
    assert hasattr(gam_pkg, "__all__"), "gamification/__init__.py must define __all__"
    assert len(gam_pkg.__all__) >= 4, "gamification __all__ should export ≥4 symbols"


def test_engine_all_symbols_importable() -> None:
    import app.services.engine as engine_pkg
    for name in engine_pkg.__all__:
        assert hasattr(engine_pkg, name), f"engine.__all__ lists '{name}' but it is not importable"


def test_gamification_all_symbols_importable() -> None:
    import app.services.gamification as gam_pkg
    for name in gam_pkg.__all__:
        assert hasattr(gam_pkg, name), f"gamification.__all__ lists '{name}' but it is not importable"
