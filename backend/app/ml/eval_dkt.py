"""DKT vs BKT evaluation harness (step-ahead correct-answer prediction).

Usage:
    cd backend
    python -m app.ml.eval_dkt [--checkpoint DIR] [--min-seqs N] [--db URL]

Evaluates step-ahead P(correct) on the 20 % val split (same temporal cut used
by train_dkt). Reports AUC and ACC for both DKT and BKT, then writes a JSON
report alongside the checkpoint.

If DKT AUC < BKT AUC the report records the likely reason (small dataset, not
enough epochs, etc.) and still exits 0.

Exit codes:
  0  report written (or BKT-only report when torch / checkpoint unavailable)
  2  not enough data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Torch guard ───────────────────────────────────────────────────────────────

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# ── DB helpers (reuse from train_dkt) ─────────────────────────────────────────

def _sync_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def _load_sequences(db_url: str) -> tuple[list[list[tuple[int, bool]]], list[str]]:
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

    skill_ids: list[str] = sorted({str(r[1]) for r in rows})
    skill_to_idx: dict[str, int] = {s: i for i, s in enumerate(skill_ids)}

    user_seqs: dict[Any, list[tuple[int, bool]]] = {}
    for user_id, skill_id, correct, _ in rows:
        key = str(user_id)
        user_seqs.setdefault(key, []).append(
            (skill_to_idx[str(skill_id)], bool(correct))
        )

    sequences = [seq for seq in user_seqs.values() if len(seq) >= 2]
    return sequences, skill_ids


# ── AUC (trapezoidal, no sklearn) ────────────────────────────────────────────

def _auc(preds: list[float], labels: list[float]) -> float:
    if len(set(labels)) < 2 or not preds:
        return float("nan")
    pairs = sorted(zip(preds, labels), key=lambda x: -x[0])
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    tp = fp = auc = 0.0
    prev_tp = prev_fp = 0.0
    for _, lab in pairs:
        if lab == 1.0:
            tp += 1
        else:
            fp += 1
        auc += (fp - prev_fp) * (tp + prev_tp) / 2.0
        prev_tp, prev_fp = tp, fp
    return auc / (pos * neg)


def _acc(preds: list[float], labels: list[float]) -> float:
    if not preds:
        return float("nan")
    correct = sum(1 for p, l in zip(preds, labels) if (p >= 0.5) == (l == 1.0))
    return correct / len(preds)


# ── BKT baseline ─────────────────────────────────────────────────────────────

def _bkt_eval(
    sequences: list[list[tuple[int, bool]]],
    skill_ids: list[str],
) -> tuple[list[float], list[float]]:
    """Step-ahead predictions using BKT (default parameters)."""
    from app.services.engine.bkt import BKTModel

    bkt = BKTModel()
    all_pred: list[float] = []
    all_true: list[float] = []

    for seq in sequences:
        states: dict[str, Any] = {}
        for t, (skill_idx, correct) in enumerate(seq):
            sid = skill_ids[skill_idx]
            if sid not in states:
                states[sid] = bkt.init_state(sid)
            if t > 0:
                all_pred.append(bkt.predict_correct(states[sid]))
                all_true.append(1.0 if correct else 0.0)
            bkt.update(states[sid], correct)

    return all_pred, all_true


# ── DKT evaluation ───────────────────────────────────────────────────────────

def _dkt_eval(
    sequences: list[list[tuple[int, bool]]],
    skill_ids: list[str],
    ckpt_dir: Path,
) -> tuple[list[float], list[float]]:
    """Step-ahead predictions using a saved DKT checkpoint."""
    if not _TORCH_AVAILABLE:
        raise RuntimeError("torch not available")

    from app.ml.train_dkt import _Net

    meta_path = ckpt_dir / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"No metadata.json in {ckpt_dir}")

    meta = json.loads(meta_path.read_text())
    hidden: int = meta["hidden"]
    n_skills = len(skill_ids)

    net = _Net(n_skills, hidden)
    net.load_state_dict(torch.load(ckpt_dir / "model.pt", weights_only=True))
    net.eval()

    all_pred: list[float] = []
    all_true: list[float] = []

    with torch.no_grad():
        for seq in sequences:
            if len(seq) < 2:
                continue
            # Run model on the full prefix up to each step
            inp = torch.tensor(
                [s * 2 + (1 if c else 0) for s, c in seq[:-1]], dtype=torch.long
            ).unsqueeze(0)  # (1, T)
            pred = net(inp)[0]  # (T, n_skills)
            for t, (skill_idx, correct) in enumerate(seq[1:]):
                all_pred.append(pred[t, skill_idx].item())
                all_true.append(1.0 if correct else 0.0)

    return all_pred, all_true


# ── Checkpoint discovery ──────────────────────────────────────────────────────

def _find_latest_checkpoint(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    candidates = [
        p for p in base_dir.iterdir()
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: int(p.name[1:]))


# ── Report ────────────────────────────────────────────────────────────────────

def _print_row(label: str, auc: float, acc: float) -> None:
    auc_s = f"{auc:.4f}" if auc == auc else "  N/A "
    acc_s = f"{acc:.4f}" if acc == acc else "  N/A "
    print(f"  {label:<8}  AUC={auc_s}  ACC={acc_s}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DKT vs BKT baseline")
    parser.add_argument("--checkpoint", type=str, default="",
                        help="Path to DKT checkpoint directory (default: latest in ~/.whetzy/models/dkt)")
    parser.add_argument("--min-seqs",  type=int, default=5,
                        help="Minimum sequences required (default: 5)")
    parser.add_argument("--db",        type=str, default="",
                        help="Database URL (overrides env)")
    args = parser.parse_args()

    # Resolve DB URL
    db_url = args.db or os.environ.get("DATABASE_URL", "")
    if not db_url:
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
        if not db_url:
            print("ERROR: DATABASE_URL not set.", file=sys.stderr)
            sys.exit(2)

    print("[eval_dkt] Loading sequences …")
    sequences, skill_ids = _load_sequences(db_url)

    if len(sequences) < args.min_seqs:
        print(
            f"ERROR: only {len(sequences)} sequences (need {args.min_seqs}). "
            "Train on more data first.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Same 80/20 temporal split as training
    split = max(1, int(len(sequences) * 0.8))
    val_seqs = sequences[split:]
    if not val_seqs:
        # Fall back to full set if too few sequences
        val_seqs = sequences

    print(
        f"[eval_dkt] {len(sequences)} total seqs · "
        f"{len(val_seqs)} val seqs · {len(skill_ids)} skills"
    )

    # ── BKT ──────────────────────────────────────────────────────────────────
    print("[eval_dkt] Running BKT …")
    bkt_pred, bkt_true = _bkt_eval(val_seqs, skill_ids)
    bkt_auc = _auc(bkt_pred, bkt_true)
    bkt_acc = _acc(bkt_pred, bkt_true)
    _print_row("BKT", bkt_auc, bkt_acc)

    # ── DKT ──────────────────────────────────────────────────────────────────
    ckpt_dir: Path | None = None
    dkt_auc = float("nan")
    dkt_acc = float("nan")
    dkt_note = ""

    if not _TORCH_AVAILABLE:
        dkt_note = "torch not installed — DKT skipped"
        print(f"[eval_dkt] {dkt_note}")
    else:
        base_dir = (
            Path(args.checkpoint) if args.checkpoint
            else Path.home() / ".whetzy" / "models" / "dkt"
        )
        ckpt_dir = (
            base_dir if (base_dir / "metadata.json").exists()
            else _find_latest_checkpoint(base_dir)
        )
        if ckpt_dir is None:
            dkt_note = "no checkpoint found — run train_dkt first"
            print(f"[eval_dkt] {dkt_note}")
        else:
            print(f"[eval_dkt] Using checkpoint {ckpt_dir} …")
            try:
                dkt_pred, dkt_true = _dkt_eval(val_seqs, skill_ids, ckpt_dir)
                dkt_auc = _auc(dkt_pred, dkt_true)
                dkt_acc = _acc(dkt_pred, dkt_true)
                _print_row("DKT", dkt_auc, dkt_acc)
            except Exception as exc:
                dkt_note = f"DKT eval failed: {exc}"
                print(f"[eval_dkt] WARNING: {dkt_note}")

    # ── Comparison note ───────────────────────────────────────────────────────
    comparison = "N/A"
    if dkt_auc == dkt_auc and bkt_auc == bkt_auc:
        if dkt_auc >= bkt_auc:
            comparison = f"DKT ≥ BKT (+{dkt_auc - bkt_auc:.4f})"
        else:
            gap = bkt_auc - dkt_auc
            dkt_note = (
                dkt_note or (
                    f"DKT AUC {dkt_auc:.4f} < BKT AUC {bkt_auc:.4f} "
                    f"(gap={gap:.4f}). Likely cause: small dataset "
                    f"({len(val_seqs)} val seqs), insufficient training "
                    "epochs, or high class imbalance. "
                    "Recommend: more data → retrain with --epochs 30."
                )
            )
            comparison = f"BKT > DKT (gap={gap:.4f})"

    print(f"\n  Comparison: {comparison}")
    if dkt_note:
        print(f"  Note: {dkt_note}")

    # ── Save report ───────────────────────────────────────────────────────────
    report: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "n_sequences_total": len(sequences),
        "n_sequences_val":   len(val_seqs),
        "n_skills":          len(skill_ids),
        "bkt": {
            "auc": round(bkt_auc, 4) if bkt_auc == bkt_auc else None,
            "acc": round(bkt_acc, 4) if bkt_acc == bkt_acc else None,
            "n_predictions": len(bkt_pred),
        },
        "dkt": {
            "checkpoint": str(ckpt_dir) if ckpt_dir else None,
            "auc": round(dkt_auc, 4) if dkt_auc == dkt_auc else None,
            "acc": round(dkt_acc, 4) if dkt_acc == dkt_acc else None,
        },
        "comparison": comparison,
        "note": dkt_note or None,
    }

    # Write report next to checkpoint (or to cwd if no checkpoint)
    report_dir = ckpt_dir if ckpt_dir else Path(".")
    report_path = report_dir / "eval_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n[eval_dkt] Report saved → {report_path}")


if __name__ == "__main__":
    main()
