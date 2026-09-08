"""Deep Knowledge Tracing (DKT) service.

Uses PyTorch LSTM when available; falls back to a simple exponential-weighted
moving-average heuristic so the module is always importable on Railway where
torch is intentionally excluded (too large for free tier).

Interface: `predict(history) -> dict[skill_id, float]`
  history: list of {"skill_id": str, "correct": bool} ordered chronologically
  returns: P(correct on next question) per skill in [0, 1]
"""

from __future__ import annotations

from typing import Any

try:
    import torch

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# ── LSTM model (only instantiated when torch is present) ─────────────────────

class _DKT:
    """Minimal 1-layer LSTM DKT model."""

    def __init__(self, n_skills: int, hidden: int = 64) -> None:
        import torch
        from torch import nn

        self.n_skills = n_skills
        self.hidden = hidden

        class _Net(nn.Module):  # type: ignore[misc]
            def __init__(self, n_skills: int, hidden: int) -> None:
                super().__init__()
                self.embed = nn.Embedding(n_skills * 2, hidden)
                self.lstm = nn.LSTM(hidden, hidden, batch_first=True)
                self.out = nn.Linear(hidden, n_skills)

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                e = self.embed(x)
                h, _ = self.lstm(e)
                return torch.sigmoid(self.out(h))

        self.net = _Net(n_skills, hidden)
        self.net.eval()

    def predict_sequence(self, indices: list[int]) -> list[list[float]]:
        import torch
        with torch.no_grad():
            x = torch.tensor([indices], dtype=torch.long)  # (1, T)
            out = self.net(x)  # (1, T, n_skills)
            return out[0].tolist()  # type: ignore[no-any-return]


# ── Public API ────────────────────────────────────────────────────────────────

_ALPHA = 0.3  # EWA decay for the heuristic fallback


def predict(
    history: list[dict[str, Any]],
    skill_index: dict[str, int] | None = None,
) -> dict[str, float]:
    """Return P(correct) per skill given answer history.

    Args:
        history: [{"skill_id": str, "correct": bool}, ...] chronological
        skill_index: optional mapping skill_id → int index (0-based).
                     When None, builds it from the history.

    Returns:
        dict skill_id → float in [0, 1]
    """
    if not history:
        return {}

    # Build skill index if not provided
    if skill_index is None:
        seen: list[str] = []
        for rec in history:
            sid = rec["skill_id"]
            if sid not in seen:
                seen.append(sid)
        skill_index = {sid: i for i, sid in enumerate(seen)}

    n_skills = len(skill_index)
    index_to_skill = {v: k for k, v in skill_index.items()}

    if _TORCH_AVAILABLE and n_skills >= 2:
        model = _DKT(n_skills=n_skills)
        # Encode as skill_idx * 2 + correct (standard DKT encoding)
        indices = [
            skill_index[r["skill_id"]] * 2 + (1 if r["correct"] else 0)
            for r in history
            if r["skill_id"] in skill_index
        ]
        if not indices:
            return _heuristic_predict(history, skill_index)
        seq_out = model.predict_sequence(indices)
        # Use last time-step output as prediction
        last = seq_out[-1]  # list of n_skills floats
        return {index_to_skill[i]: round(last[i], 4) for i in range(n_skills)}

    return _heuristic_predict(history, skill_index)


def _heuristic_predict(
    history: list[dict[str, Any]],
    skill_index: dict[str, int],
) -> dict[str, float]:
    """Exponential-weighted moving average fallback (no torch required)."""
    ewma: dict[str, float] = {}
    for rec in history:
        sid = rec["skill_id"]
        if sid not in skill_index:
            continue
        value = 1.0 if rec["correct"] else 0.0
        prev = ewma.get(sid, 0.5)
        ewma[sid] = _ALPHA * value + (1 - _ALPHA) * prev
    return {sid: round(v, 4) for sid, v in ewma.items()}
