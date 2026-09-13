"""DKT training pipeline.

Usage:
    cd backend
    python -m app.ml.train_dkt [--epochs N] [--hidden H] [--min-seqs M]

Reads responses from the DB configured by DATABASE_URL (env var or .env).
Produces a versioned checkpoint at models/dkt/v{N}/:
  - model.pt        torch state_dict (requires torch)
  - metadata.json   skill_index, hidden size, AUC, trained_at, etc.

Exit codes:
  0  checkpoint written
  1  torch not available
  2  not enough training data
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ── 1. Torch guard ──────────────────────────────────────────────────────────

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# ── 2. DB helpers ────────────────────────────────────────────────────────────

def _sync_url(url: str) -> str:
    """Convert asyncpg URL to psycopg2 URL for synchronous training query."""
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def _load_sequences(db_url: str) -> tuple[list[list[tuple[int, bool]]], list[str]]:
    """Return (sequences, skill_index) from the DB.

    sequences: per-user list of (skill_idx, correct) ordered by time
    skill_index: list of skill_ids; position = index used in encoding
    """
    from sqlalchemy import create_engine, text

    engine = create_engine(_sync_url(db_url), echo=False, pool_pre_ping=True)
    sql = text("""
        SELECT ss.user_id, q.skill_id, r.correct, r.created_at
        FROM   responses r
        JOIN   study_sessions ss ON r.session_id = ss.id
        JOIN   questions      q  ON r.question_id = q.id
        ORDER  BY ss.user_id, r.created_at
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
    engine.dispose()

    if not rows:
        return [], []

    # Build skill index (deterministic alphabetical order for reproducibility)
    skill_ids: list[str] = sorted({str(r[1]) for r in rows})
    skill_to_idx: dict[str, int] = {s: i for i, s in enumerate(skill_ids)}

    # Group by user_id
    user_seqs: dict[Any, list[tuple[int, bool]]] = {}
    for user_id, skill_id, correct, _ in rows:
        key = str(user_id)
        if key not in user_seqs:
            user_seqs[key] = []
        idx = skill_to_idx.get(str(skill_id))
        if idx is not None:
            user_seqs[key].append((idx, bool(correct)))

    sequences = [seq for seq in user_seqs.values() if len(seq) >= 2]
    return sequences, skill_ids


# ── 3. Dataset ───────────────────────────────────────────────────────────────

if _TORCH_AVAILABLE:
    class _DKTDataset(Dataset):  # type: ignore[type-arg, misc]
        """Yields (input_seq, target_seq) pairs for DKT training.

        Encoding: skill_idx * 2 + (1 if correct else 0)
        Target at step t: P(correct on skill asked at step t+1)
        """

        def __init__(self, sequences: list[list[tuple[int, bool]]], n_skills: int) -> None:
            self.data = sequences
            self.n_skills = n_skills

        def __len__(self) -> int:
            return len(self.data)

        def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            seq = self.data[idx]
            # inputs: encode each (skill_idx, correct) pair
            inputs = torch.tensor(
                [s * 2 + (1 if c else 0) for s, c in seq[:-1]], dtype=torch.long
            )
            # targets: skill asked at each next step + whether correct
            target_skills = torch.tensor([s for s, _ in seq[1:]], dtype=torch.long)
            target_correct = torch.tensor([1.0 if c else 0.0 for _, c in seq[1:]])
            return inputs, target_skills, target_correct

    def _collate(batch: list[Any]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Pad sequences to equal length within a batch."""
        inputs, t_skills, t_correct = zip(*batch)
        max_len = max(x.shape[0] for x in inputs)
        bs = len(inputs)
        inp_pad = torch.zeros(bs, max_len, dtype=torch.long)
        sk_pad  = torch.zeros(bs, max_len, dtype=torch.long)
        co_pad  = torch.zeros(bs, max_len)
        mask    = torch.zeros(bs, max_len, dtype=torch.bool)
        for i, (inp, sk, co) in enumerate(zip(inputs, t_skills, t_correct)):
            L = inp.shape[0]
            inp_pad[i, :L] = inp
            sk_pad[i, :L]  = sk
            co_pad[i, :L]  = co
            mask[i, :L]    = True
        return inp_pad, sk_pad, co_pad, mask  # type: ignore[return-value]

    class _Net(nn.Module):  # type: ignore[misc]
        def __init__(self, n_skills: int, hidden: int) -> None:
            super().__init__()
            self.embed = nn.Embedding(n_skills * 2, hidden)
            self.lstm  = nn.LSTM(hidden, hidden, batch_first=True)
            self.out   = nn.Linear(hidden, n_skills)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            e = self.embed(x)
            h, _ = self.lstm(e)
            return torch.sigmoid(self.out(h))


# ── 4. Training ───────────────────────────────────────────────────────────────

def _train(
    sequences: list[list[tuple[int, bool]]],
    skill_ids: list[str],
    hidden: int,
    epochs: int,
    lr: float = 1e-3,
) -> tuple[Any, float]:
    """Train DKT; return (state_dict, val_auc)."""
    n_skills = len(skill_ids)
    # Temporal split: first 80% of sequences for train, last 20% for val
    split = max(1, int(len(sequences) * 0.8))
    train_seqs = sequences[:split]
    val_seqs   = sequences[split:]

    train_ds = _DKTDataset(train_seqs, n_skills)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, collate_fn=_collate)

    net = _Net(n_skills, hidden)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    criterion = nn.BCELoss(reduction="none")

    for epoch in range(1, epochs + 1):
        net.train()
        total_loss = 0.0
        n_steps = 0
        for inp, t_skills, t_correct, mask in train_dl:
            opt.zero_grad()
            pred = net(inp)  # (B, T, n_skills)
            # Gather predicted P(correct) for the next skill
            B, T, _ = pred.shape
            skill_flat = t_skills.view(-1)           # (B*T,)
            pred_flat  = pred.view(B * T, n_skills)  # (B*T, n_skills)
            # Each row: probability for the target skill
            p = pred_flat[torch.arange(B * T), skill_flat].view(B, T)
            loss_all = criterion(p, t_correct)        # (B, T)
            loss = (loss_all * mask).sum() / mask.sum()
            loss.backward()
            opt.step()
            total_loss += loss.item()
            n_steps += 1
        avg_loss = total_loss / max(n_steps, 1)
        print(f"  epoch {epoch}/{epochs}  loss={avg_loss:.4f}")

    # Validation AUC
    val_auc = _compute_auc(net, val_seqs, n_skills) if val_seqs else float("nan")
    print(f"  val AUC={val_auc:.4f}" if val_seqs else "  no val split")
    return net.state_dict(), val_auc


def _compute_auc(
    net: _Net,
    sequences: list[list[tuple[int, bool]]],
    n_skills: int,
) -> float:
    net.eval()
    all_pred: list[float] = []
    all_true: list[float] = []
    with torch.no_grad():
        for seq in sequences:
            if len(seq) < 2:
                continue
            inp = torch.tensor(
                [s * 2 + (1 if c else 0) for s, c in seq[:-1]], dtype=torch.long
            ).unsqueeze(0)
            pred = net(inp)[0]  # (T, n_skills)
            for t, (skill_idx, correct) in enumerate(seq[1:]):
                all_pred.append(pred[t, skill_idx].item())
                all_true.append(1.0 if correct else 0.0)

    if len(set(all_true)) < 2:
        return float("nan")

    # Compute AUC via trapezoidal rule (no sklearn needed)
    pairs = sorted(zip(all_pred, all_true), key=lambda x: -x[0])
    tp = fp = 0
    pos = sum(all_true)
    neg = len(all_true) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    auc = 0.0
    prev_fp = 0
    prev_tp = 0
    for _, label in pairs:
        if label == 1.0:
            tp += 1
        else:
            fp += 1
        auc += (fp - prev_fp) * (tp + prev_tp) / 2.0
        prev_fp = fp
        prev_tp = tp
    return auc / (pos * neg)


# ── 5. Checkpoint ─────────────────────────────────────────────────────────────

def _next_version(models_dir: Path) -> int:
    """Return next version number (1-based, never reuses existing)."""
    if not models_dir.exists():
        return 1
    existing = [
        int(p.name[1:]) for p in models_dir.iterdir()
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
    ]
    return max(existing, default=0) + 1


def _save_checkpoint(
    state_dict: Any,
    skill_ids: list[str],
    hidden: int,
    epochs: int,
    val_auc: float,
    models_dir: Path,
    db_url: str,
) -> Path:
    version = _next_version(models_dir)
    ckpt_dir = models_dir / f"v{version}"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    torch.save(state_dict, ckpt_dir / "model.pt")

    # Sanitise DB URL (strip credentials)
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(db_url)
    safe_url = urlunparse(parsed._replace(netloc=f"***:***@{parsed.hostname}:{parsed.port}"))

    meta: dict[str, Any] = {
        "version": version,
        "n_skills": len(skill_ids),
        "hidden": hidden,
        "epochs": epochs,
        "val_auc": round(val_auc, 4) if not math.isnan(val_auc) else None,
        "trained_at": datetime.now(UTC).isoformat(),
        "skill_ids": skill_ids,
        "db_url": safe_url,
        "run_id": str(uuid.uuid4()),
    }
    (ckpt_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
    return ckpt_dir


# ── 6. Entrypoint ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train DKT checkpoint from DB responses")
    parser.add_argument("--epochs",     type=int, default=10, help="Training epochs (default: 10)")
    parser.add_argument("--hidden",     type=int, default=64, help="LSTM hidden size (default: 64)")
    parser.add_argument("--min-seqs",   type=int, default=5,  help="Minimum user sequences required (default: 5)")
    parser.add_argument("--db",         type=str, default="",  help="Database URL (overrides env)")
    parser.add_argument("--output-dir", type=str, default="",
                        help="Base dir for checkpoints (default: ~/.whetzy/models/dkt)")
    args = parser.parse_args()

    if not _TORCH_AVAILABLE:
        print("ERROR: torch is not installed. Install it with: pip install torch", file=sys.stderr)
        sys.exit(1)

    # Resolve DB URL
    db_url = args.db or os.environ.get("DATABASE_URL", "")
    if not db_url:
        # Try .env file in backend/
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
        if not db_url:
            print("ERROR: DATABASE_URL not set. Use --db or set the env var.", file=sys.stderr)
            sys.exit(2)

    print("[train_dkt] Loading sequences from DB …")
    sequences, skill_ids = _load_sequences(db_url)

    if len(sequences) < args.min_seqs:
        print(
            f"ERROR: only {len(sequences)} user sequences with ≥2 responses "
            f"(need {args.min_seqs}). Seed more data first.",
            file=sys.stderr,
        )
        sys.exit(2)

    n_skills = len(skill_ids)
    total_steps = sum(len(s) - 1 for s in sequences)
    print(
        f"[train_dkt] {len(sequences)} users · {n_skills} skills · "
        f"{total_steps} training steps"
    )

    # Models dir: prefer user home (not OneDrive-synced) so Python I/O works on Windows.
    if args.output_dir:
        models_dir = Path(args.output_dir)
    else:
        models_dir = Path.home() / ".whetzy" / "models" / "dkt"

    print(f"[train_dkt] Training {args.epochs} epochs · hidden={args.hidden} …")
    state_dict, val_auc = _train(sequences, skill_ids, args.hidden, args.epochs)

    ckpt_dir = _save_checkpoint(
        state_dict, skill_ids, args.hidden, args.epochs, val_auc, models_dir, db_url
    )
    print(f"[train_dkt] Checkpoint saved → {ckpt_dir}")
    print(
        f"[train_dkt] val_auc={val_auc:.4f}"
        if not math.isnan(val_auc)
        else "[train_dkt] val_auc=N/A (no val split)"
    )


if __name__ == "__main__":
    main()
