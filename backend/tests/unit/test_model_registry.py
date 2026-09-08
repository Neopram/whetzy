"""Unit tests for the DKT model registry."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ml.registry import _Registry


@pytest.fixture
def tmp_registry(tmp_path: Path) -> _Registry:
    """Registry pointing at a temp directory with fake checkpoints."""
    reg = _Registry()
    # Patch the base dir to the tmp directory
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        # Create v1 checkpoint (fake files)
        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "metadata.json").write_text(
            json.dumps({"n_skills": 2, "hidden": 16, "val_auc": 0.55, "epochs": 5})
        )
        (v1 / "model.pt").write_bytes(b"\x00" * 16)  # placeholder bytes

        # Create v2 checkpoint
        v2 = tmp_path / "v2"
        v2.mkdir()
        (v2 / "metadata.json").write_text(
            json.dumps({"n_skills": 2, "hidden": 16, "val_auc": 0.62, "epochs": 10})
        )
        (v2 / "model.pt").write_bytes(b"\x00" * 16)

        yield reg


def test_list_versions_finds_both(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        for v in (1, 2, 5):
            ckpt = tmp_path / f"v{v}"
            ckpt.mkdir()
            (ckpt / "model.pt").write_bytes(b"")
            (ckpt / "metadata.json").write_text("{}")
        versions = reg.list_versions()
    assert versions == [1, 2, 5]


def test_latest_version_returns_highest(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        for v in (1, 3):
            ckpt = tmp_path / f"v{v}"
            ckpt.mkdir()
            (ckpt / "model.pt").write_bytes(b"")
            (ckpt / "metadata.json").write_text("{}")
        assert reg.latest_version() == 3


def test_latest_version_empty_dir(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        assert reg.latest_version() is None


def test_list_versions_ignores_incomplete(tmp_path: Path) -> None:
    """Directories without model.pt or metadata.json are not listed."""
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        bad = tmp_path / "v99"
        bad.mkdir()
        (bad / "model.pt").write_bytes(b"")
        # metadata.json missing
        assert reg.list_versions() == []


def test_current_info_before_load() -> None:
    reg = _Registry()
    info = reg.current_info()
    assert info["version"] is None
    assert info["checkpoint"] is None


def test_current_info_includes_available_versions(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "model.pt").write_bytes(b"")
        (v1 / "metadata.json").write_text("{}")
        info = reg.current_info()
    assert 1 in info["available_versions"]


@pytest.mark.asyncio
async def test_load_no_checkpoint_is_noop(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        await reg.load()  # no checkpoints — should not raise
    assert reg.get_model() is None


@pytest.mark.asyncio
async def test_rollback_raises_for_missing_version(tmp_path: Path) -> None:
    reg = _Registry()
    with patch("app.ml.registry._BASE_DIR", tmp_path):
        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "model.pt").write_bytes(b"")
        (v1 / "metadata.json").write_text("{}")
        with pytest.raises(ValueError, match="not found"):
            await reg.rollback(99)
