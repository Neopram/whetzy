"""DKT Model Registry — versioned checkpoint management.

Public API
----------
    registry.load()                      async load latest (or pinned) version
    registry.get_model()                 DKT inference model or None
    registry.rollback(version: int)      load a specific checkpoint version
    registry.current_info()              dict with version, metadata, path

Models are stored as:
    ~/.whetzy/models/dkt/v{N}/model.pt
    ~/.whetzy/models/dkt/v{N}/metadata.json

The registry is a module-level singleton.  Call `await registry.load()` once
during app startup; subsequent calls to `get_model()` are synchronous and
safe to call from any thread.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("whetzy.registry")

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

_BASE_DIR = Path.home() / ".whetzy" / "models" / "dkt"


# ── Model class (mirrors train_dkt._Net) ──────────────────────────────────────

class _Net:
    """Loaded inference wrapper around the LSTM."""

    def __init__(self, state: Any, n_skills: int, hidden: int) -> None:
        import torch
        from torch import nn

        class _LSTMNet(nn.Module):
            def __init__(self, n: int, h: int) -> None:
                super().__init__()
                self.embed = nn.Embedding(n * 2, h)
                self.lstm = nn.LSTM(h, h, batch_first=True)
                self.out = nn.Linear(h, n)

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                e = self.embed(x)
                h, _ = self.lstm(e)
                return torch.sigmoid(self.out(h))

        self.n_skills = n_skills
        self._net = _LSTMNet(n_skills, hidden)
        self._net.load_state_dict(state)
        self._net.eval()

    def predict(self, indices: list[int]) -> list[float]:
        import torch
        with torch.no_grad():
            x = torch.tensor([indices], dtype=torch.long)
            out = self._net(x)
            return out[0, -1].tolist()  # type: ignore[no-any-return]


# ── Registry ──────────────────────────────────────────────────────────────────

class _Registry:
    def __init__(self) -> None:
        self._model: _Net | None = None
        self._version: int | None = None
        self._metadata: dict[str, Any] = {}
        self._checkpoint_dir: Path | None = None
        self._lock = asyncio.Lock()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_versions(self) -> list[int]:
        """Return available DKT checkpoint version numbers, sorted ascending."""
        if not _BASE_DIR.exists():
            return []
        return sorted(
            int(p.name[1:])
            for p in _BASE_DIR.iterdir()
            if p.is_dir()
            and p.name.startswith("v")
            and p.name[1:].isdigit()
            and (p / "model.pt").exists()
            and (p / "metadata.json").exists()
        )

    def latest_version(self) -> int | None:
        vs = self.list_versions()
        return vs[-1] if vs else None

    def _checkpoint_path(self, version: int) -> Path:
        return _BASE_DIR / f"v{version}"

    # ── Load ──────────────────────────────────────────────────────────────────

    def _load_sync(self, version: int) -> None:
        if not _TORCH_AVAILABLE:
            logger.warning("torch not available — DKT registry stays unloaded")
            return
        ckpt = self._checkpoint_path(version)
        meta_path = ckpt / "metadata.json"
        if not meta_path.exists():
            logger.error("Registry: metadata.json not found at %s", ckpt)
            return
        meta = json.loads(meta_path.read_text())
        state = torch.load(ckpt / "model.pt", weights_only=True)
        n_skills: int = meta.get("n_skills", meta.get("skills", 1))
        hidden: int = meta.get("hidden", 64)
        self._model = _Net(state, n_skills, hidden)
        self._version = version
        self._metadata = meta
        self._checkpoint_dir = ckpt
        logger.info("Registry: loaded DKT v%d (%d skills, hidden=%d)", version, n_skills, hidden)

    async def load(self, version: int | None = None) -> None:
        """Load a checkpoint (default: latest).  No-op if torch unavailable."""
        async with self._lock:
            target = version if version is not None else self.latest_version()
            if target is None:
                logger.warning("Registry: no DKT checkpoint found — using heuristic fallback")
                return
            await asyncio.to_thread(self._load_sync, target)

    async def rollback(self, version: int) -> None:
        """Switch to a specific checkpoint version."""
        if version not in self.list_versions():
            raise ValueError(f"Version v{version} not found in {_BASE_DIR}")
        await self.load(version)

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_model(self) -> _Net | None:
        return self._model

    def current_info(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "checkpoint": str(self._checkpoint_dir) if self._checkpoint_dir else None,
            "metadata": self._metadata,
            "available_versions": self.list_versions(),
            "torch_available": _TORCH_AVAILABLE,
        }


registry = _Registry()
