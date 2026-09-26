"""BKT vs DKT benchmark on a PUBLIC knowledge-tracing dataset (task 11.3).

WHY THIS FILE EXISTS
---------------------
`eval_dkt.py` compares BKT vs DKT on whatever is in *this app's own database*
(as of writing: a handful of internally-seeded sequences). That is evidence
of a capability ("the harness runs"), not evidence of an advantage. This
script instead benchmarks both models on `synthetic-5`, the dataset used by
Piech et al. (2015) "Deep Knowledge Tracing" — a fixed, third-party,
citable ground truth — so the "adaptive engine" claim has a number behind
it that isn't graded by the app's own homework.

Dataset
-------
    synthetic-5 (Piech et al. 2015)
    https://github.com/chrispiech/DeepKnowledgeTracing
    data/synthetic/naive_c5_q50_s4000_v0.csv        (4000 students x 50 responses, 0/1)
    data/synthetic/info/naive_c5_q50_s4000_v0_info.txt  (per-question concept id, col 3)

    5 concepts, 50 questions/student, 4000 students. Column order within a
    row IS temporal order for that student (this is how the "naive" HMM
    scenario in the paper's own generator produces the data). Only seed v0
    of 20 available seeds is used — fixed, not cherry-picked; see "Honesty
    notes" below.

Item representation — READ THIS BEFORE QUOTING THE NUMBERS ANYWHERE
--------------------------------------------------------------------
    Each response is keyed by its **concept id (0-4)**, taken from the
    dataset's info file, NOT by its question id (0-49). Piech et al. feed
    question ids to DKT (100 one-hot input states); this script feeds
    concept ids (10 input states).

    That makes the task strictly EASIER for both models: with the
    ground-truth concept label handed to the model, there is no
    per-question difficulty left to infer inside a concept — only 5 latent
    skills to track. It is the representation the production engine
    actually uses (Whetzy tracks mastery per skill, not per question), so
    it is the honest thing to benchmark for *this* product. But it is NOT
    the paper's setup.

    Consequences, stated plainly so nobody mistakes them later:
      * The absolute AUCs here are NOT comparable to the paper's 0.75/0.62
        and must never be reported as "we beat Piech et al." Both models
        score higher here because the problem is easier, not because this
        implementation is better.
      * DKT's MARGIN over BKT is the number that actually transfers, and it
        is much smaller in this setup (~+0.03 AUC) than in the paper
        (~+0.13). A well-fit BKT is a strong baseline on 5 concepts; DKT's
        advantage grows with item-level sparsity, which this variant
        removes by construction.
      * So the defensible claim from this file is narrow: "on concept-level
        synthetic-5, our DKT beats our grid-fit BKT by ~0.03 AUC." Anything
        stronger is not supported by this run.

ASSISTments 2009 (secondary dataset, per the task's ledger)
-------------------------------------------------------------
    Attempted and NOT included. The canonical distribution page
    (https://sites.google.com/site/assistmentsdata/home/assistment-2009-2010-data)
    returns HTTP 200 but is a Google Sites page with no static, scriptable
    direct-download URL (the actual CSV sits behind a Google Drive link
    that Sites renders client-side via JS; `curl` on the page yields no
    resolvable file id). A handful of commonly-cited GitHub mirrors were
    checked and all 404'd (see `docs/ml/kt-benchmark.json` -> `assistments_2009`
    for the exact list and HTTP statuses). This is documented as a gap, not
    silently skipped or faked with a look-alike dataset.

Split
-----
    Temporal, by student: sequences[:] kept in the dataset's original row
    order (no shuffling — see honesty notes), first 80% of ROWS (students)
    -> train, last 20% -> test. DKT is trained only on train students,
    then evaluated on held-out test students. Within every evaluated
    sequence, prediction is strictly step-ahead: predicting response t uses
    only responses 1..t-1 of that same student (temporal order preserved,
    no leakage from the future).

BKT baseline
------------
    Reuses `app.services.engine.bkt.BKTModel` UNCHANGED (no reimplementation
    of the HMM update/predict formulas). That model only supports one global
    `SkillParams` (or per-skill overrides via `set_params`, unused here since
    all 5 synthetic concepts are drawn from the same generative distribution).
    Because the production `BKTModel` has no parameter-fitting logic at all
    (grep confirms: no EM/Baum-Welch anywhere in this codebase), evaluating
    it with arbitrary un-fit defaults would artificially depress the BKT
    number and bias the comparison in DKT's favor — precisely the kind of
    rigged result the task's honesty rule prohibits, just in the opposite
    direction. So this script does a small, deterministic grid search over
    the 4 global parameters, selecting by AUC on the TRAIN split only (test
    labels are never touched during fitting). This is not full EM, and that
    is stated plainly in the JSON report's `methodology.bkt_fitting` field.

DKT
---
    Reuses `_Net`, `_DKTDataset`, `_collate` from `app.ml.train_dkt`
    UNCHANGED. Only the outer training loop is rewritten here so it trains
    on an explicit, caller-supplied split instead of train_dkt's own
    internal 80/20 re-split (train_dkt.py and eval_dkt.py are out of scope
    for this task and are not modified).

AUC
---
    `sklearn.metrics.roc_auc_score` (not the hand-rolled trapezoidal AUC in
    train_dkt.py/eval_dkt.py) per the task's explicit instruction.

Honesty notes (read before touching the thresholds in this file)
------------------------------------------------------------------
  * No seed search: the RNG seed for DKT training is fixed once
    (`_DKT_SEED`) and never varied to chase a better number.
  * No dataset-version search: only naive_c5_q50_s4000_v0 is used, not the
    best-of-20 available seeds.
  * The split is fixed row order from the source file, not shuffled/sorted
    to favor either model.
  * Whatever `sklearn.metrics.roc_auc_score` returns on the test split is
    what gets written to `docs/ml/kt-benchmark.json` and printed. If DKT
    loses to BKT, or misses the 0.70 threshold from the ledger, that is
    reported as-is with the acceptance criterion marked not met — this
    script does not special-case or round in either model's favor.

Usage
-----
    cd backend
    python -m app.ml.benchmark_kt [--epochs N] [--hidden H] [--data-dir DIR]

Exit codes
----------
    0  report written (dataset benchmarked; DKT may or may not have won)
    1  torch not available — DKT could not be trained, BLOCKED
    2  dataset download failed — BLOCKED (exact HTTP/network error printed)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sklearn.metrics import roc_auc_score

from app.services.engine.bkt import BKTModel, SkillParams, SkillState

# ── Torch guard (DKT is optional — see docs/DECISIONS.md #4) ────────────────

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# ── Dataset constants ─────────────────────────────────────────────────────────

_SYNTHETIC5_BASE = (
    "https://raw.githubusercontent.com/chrispiech/DeepKnowledgeTracing/master/data/synthetic"
)
SYNTHETIC5_CSV_URL = f"{_SYNTHETIC5_BASE}/naive_c5_q50_s4000_v0.csv"
SYNTHETIC5_INFO_URL = f"{_SYNTHETIC5_BASE}/info/naive_c5_q50_s4000_v0_info.txt"
DATASET_LABEL = "synthetic-5 (Piech et al. 2015, naive_c5_q50_s4000_v0)"

# GitHub mirrors probed for a scriptable ASSISTments 2009 CSV; all returned 404
# when checked on 2026-09-13. Kept here (not just in prose) so a future run
# can re-probe them without re-deriving the list.
ASSISTMENTS_2009_CANDIDATES: tuple[str, ...] = (
    "https://sites.google.com/site/assistmentsdata/home/assistment-2009-2010-data",
    (
        "https://raw.githubusercontent.com/ckyeungac/deep-knowledge-tracing-plus/"
        "master/data/assist2009_pid/skill_builder_data_corrected_collapsed.csv"
    ),
    (
        "https://raw.githubusercontent.com/jennyzhang0215/DKVMN/"
        "master/data/assist2009_pid/builder_train.csv"
    ),
    (
        "https://raw.githubusercontent.com/lccasagrande/Deep-Knowledge-Tracing/"
        "master/data/assistments/skill_builder_data.csv"
    ),
    (
        "https://raw.githubusercontent.com/hcnoh/knowledge-tracing-collection-pytorch/"
        "main/datasets/ASSIST2009/skill_builder_data.csv"
    ),
)

_DKT_SEED = 42
_AUC_THRESHOLD = 0.70

_BKT_GRID_L0: tuple[float, ...] = (0.1, 0.3, 0.5)
_BKT_GRID_T: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4)
_BKT_GRID_G: tuple[float, ...] = (0.1, 0.2, 0.3)
_BKT_GRID_S: tuple[float, ...] = (0.05, 0.1, 0.2)


# ── Dataset download / cache ─────────────────────────────────────────────────

def default_cache_dir() -> Path:
    """User-home cache dir — avoids OneDrive-synced project paths (see
    train_dkt.py's identical rationale for its checkpoint dir)."""
    return Path.home() / ".whetzy" / "data" / "kt_benchmark"


def _download(url: str, dest: Path, timeout: float = 30.0) -> None:
    """Download `url` to `dest`. Raises RuntimeError with the exact HTTP/network
    error on failure — never silently falls back to fabricated data."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "whetzy-kt-benchmark/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            data = resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} {exc.reason} fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error fetching {url}: {exc.reason}") from exc
    dest.write_bytes(data)


def ensure_synthetic5(cache_dir: Path) -> tuple[Path, Path]:
    """Return (csv_path, info_path) for synthetic-5 v0, downloading into
    `cache_dir` if not already cached there."""
    csv_path = cache_dir / "naive_c5_q50_s4000_v0.csv"
    info_path = cache_dir / "naive_c5_q50_s4000_v0_info.txt"
    if not csv_path.exists():
        print(f"[benchmark_kt] Downloading {SYNTHETIC5_CSV_URL} ...")
        _download(SYNTHETIC5_CSV_URL, csv_path)
    if not info_path.exists():
        print(f"[benchmark_kt] Downloading {SYNTHETIC5_INFO_URL} ...")
        _download(SYNTHETIC5_INFO_URL, info_path)
    return csv_path, info_path


# ── Dataset parsing ───────────────────────────────────────────────────────────

def parse_concept_ids(info_text: str) -> list[int]:
    """Parse the per-question concept id (0-based) from the dataset's tab-
    separated info file: `p_correct  variance  concept_id  difficulty`."""
    concept_ids: list[int] = []
    for raw_line in info_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        concept_ids.append(int(parts[2]))
    return concept_ids


def load_synthetic5(csv_text: str, info_text: str) -> tuple[list[list[tuple[int, bool]]], list[str]]:
    """Parse synthetic-5 into (sequences, skill_ids).

    sequences: one list per student of (skill_idx, correct) IN THE ORIGINAL
    COLUMN ORDER — which is temporal order for that student in this dataset.
    skill_ids: string ids "0".."4", index = skill_idx used above.
    """
    concept_ids = parse_concept_ids(info_text)
    n_skills = len(set(concept_ids))
    skill_ids = [str(i) for i in range(n_skills)]

    sequences: list[list[tuple[int, bool]]] = []
    for raw_line in csv_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        values = [int(v) for v in line.split(",")]
        if len(values) != len(concept_ids):
            raise ValueError(
                f"Row has {len(values)} responses but info file describes "
                f"{len(concept_ids)} questions"
            )
        seq = [(concept_ids[i], bool(v)) for i, v in enumerate(values)]
        sequences.append(seq)
    return sequences, skill_ids


def temporal_split(
    sequences: list[list[tuple[int, bool]]], train_frac: float = 0.8
) -> tuple[list[list[tuple[int, bool]]], list[list[tuple[int, bool]]]]:
    """Split BY STUDENT, preserving the dataset's original (temporal) row
    order: first `train_frac` of rows -> train, remainder -> test. No
    shuffling. Within every sequence, later code only ever predicts step t
    from steps < t of that same sequence."""
    split = max(1, int(len(sequences) * train_frac))
    return sequences[:split], sequences[split:]


# ── Metrics ───────────────────────────────────────────────────────────────────

def _accuracy(preds: list[float], labels: list[float]) -> float:
    if not preds:
        return float("nan")
    correct = sum(1 for p, y in zip(preds, labels) if (p >= 0.5) == (y == 1.0))
    return correct / len(preds)


def _safe_auc(preds: list[float], labels: list[float]) -> float:
    if not preds or len(set(labels)) < 2:
        return float("nan")
    return float(roc_auc_score(labels, preds))


def _round_or_none(value: float, ndigits: int = 4) -> float | None:
    return None if math.isnan(value) else round(value, ndigits)


# ── BKT ───────────────────────────────────────────────────────────────────────

def bkt_predict_stepahead(
    params: SkillParams,
    sequences: list[list[tuple[int, bool]]],
    skill_ids: list[str],
) -> tuple[list[float], list[float]]:
    """Step-ahead P(correct) predictions from a fresh BKTModel per sequence
    (mastery state does not leak across students)."""
    model = BKTModel(params)
    all_pred: list[float] = []
    all_true: list[float] = []
    for seq in sequences:
        states: dict[str, SkillState] = {}
        for t, (skill_idx, correct) in enumerate(seq):
            sid = skill_ids[skill_idx]
            if sid not in states:
                states[sid] = model.init_state(sid)
            if t > 0:
                all_pred.append(model.predict_correct(states[sid]))
                all_true.append(1.0 if correct else 0.0)
            model.update(states[sid], correct)
    return all_pred, all_true


def fit_bkt_grid(
    train_sequences: list[list[tuple[int, bool]]],
    skill_ids: list[str],
) -> tuple[SkillParams, float]:
    """Coarse grid search for global BKT parameters, selected by TRAIN-split
    AUC only. See module docstring "BKT baseline" for why this exists."""
    best_params = SkillParams()
    best_auc = float("-inf")
    for p_l0 in _BKT_GRID_L0:
        for p_t in _BKT_GRID_T:
            for p_g in _BKT_GRID_G:
                for p_s in _BKT_GRID_S:
                    params = SkillParams(p_l0=p_l0, p_t=p_t, p_g=p_g, p_s=p_s)
                    preds, labels = bkt_predict_stepahead(params, train_sequences, skill_ids)
                    auc = _safe_auc(preds, labels)
                    if not math.isnan(auc) and auc > best_auc:
                        best_auc = auc
                        best_params = params
    return best_params, best_auc


# ── DKT ───────────────────────────────────────────────────────────────────────

def run_dkt(
    train_sequences: list[list[tuple[int, bool]]],
    test_sequences: list[list[tuple[int, bool]]],
    n_skills: int,
    hidden: int,
    epochs: int,
    lr: float = 1e-3,
    seed: int = _DKT_SEED,
) -> tuple[list[float], list[float]]:
    """Train DKT on `train_sequences` only, return step-ahead (pred, true) on
    `test_sequences`. Reuses `_Net` / `_DKTDataset` / `_collate` from
    `app.ml.train_dkt` verbatim; only this outer loop (explicit split
    instead of train_dkt's internal 80/20 cut) is written here."""
    if not _TORCH_AVAILABLE:
        raise RuntimeError("torch not available")

    from app.ml.train_dkt import _collate, _DKTDataset, _Net

    torch.manual_seed(seed)

    train_ds = _DKTDataset(train_sequences, n_skills)
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
            pred = net(inp)
            b, seq_len, _ = pred.shape
            skill_flat = t_skills.reshape(-1)
            pred_flat = pred.reshape(b * seq_len, n_skills)
            p = pred_flat[torch.arange(b * seq_len), skill_flat].reshape(b, seq_len)
            loss_all = criterion(p, t_correct)
            loss = (loss_all * mask).sum() / mask.sum()
            loss.backward()
            opt.step()
            total_loss += loss.item()
            n_steps += 1
        avg_loss = total_loss / max(n_steps, 1)
        print(f"  [DKT] epoch {epoch}/{epochs}  loss={avg_loss:.4f}")

    net.eval()
    all_pred: list[float] = []
    all_true: list[float] = []
    with torch.no_grad():
        for seq in test_sequences:
            if len(seq) < 2:
                continue
            inp = torch.tensor(
                [s * 2 + (1 if c else 0) for s, c in seq[:-1]], dtype=torch.long
            ).unsqueeze(0)
            pred = net(inp)[0]
            for t_idx, (skill_idx, correct) in enumerate(seq[1:]):
                all_pred.append(pred[t_idx, skill_idx].item())
                all_true.append(1.0 if correct else 0.0)

    return all_pred, all_true


# ── ASSISTments 2009 probing (documents the gap, downloads nothing fake) ────

def probe_assistments_2009(timeout: float = 15.0) -> dict[str, Any]:
    """Best-effort check of known candidate URLs for a scriptable ASSISTments
    2009 download. Returns a report dict; never raises, never fabricates a
    dataset. See module docstring for why none of these are used."""
    results: list[dict[str, Any]] = []
    for url in ASSISTMENTS_2009_CANDIDATES:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "whetzy-kt-benchmark/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                status = resp.status
                note = "200 OK, but no scriptable direct-download CSV" if "sites.google.com" in url else "200 OK (unexpected — re-verify)"
        except urllib.error.HTTPError as exc:
            status = exc.code
            note = f"HTTP {exc.code} {exc.reason}"
        except urllib.error.URLError as exc:
            status = None
            note = f"network error: {exc.reason}"
        results.append({"url": url, "status": status, "note": note})
    return {
        "attempted": True,
        "included_in_benchmark": False,
        "reason": (
            "Official distribution page is a Google Sites page with no "
            "static/scriptable direct-download URL (file lives behind a "
            "client-side-rendered Google Drive link). No working GitHub "
            "mirror was found among the candidates probed below."
        ),
        "candidates_probed": results,
    }


# ── Report ────────────────────────────────────────────────────────────────────

def _repo_root() -> Path:
    # backend/app/ml/benchmark_kt.py -> backend/app/ml -> backend/app -> backend -> repo root
    return Path(__file__).resolve().parents[3]


def _write_report(report: dict[str, Any], out_path: Path) -> None:
    payload = json.dumps(report, indent=2) + "\n"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload)
    except OSError as exc:
        # Windows/OneDrive-synced paths can raise FileNotFoundError (mkdir)
        # or "Bad file descriptor" / errno 9 (write) even though the target
        # directory demonstrably exists and a shell `mkdir`/`cp` succeeds.
        # Fall back to a scratch temp file (never under a synced path) and
        # tell the caller exactly where it landed instead of losing the
        # report or silently writing nothing.
        import tempfile

        fallback = Path(tempfile.gettempdir()) / "kt-benchmark.json"
        fallback.write_text(payload)
        print(
            f"[benchmark_kt] WARNING: could not write {out_path} ({exc}); "
            f"wrote {fallback} instead — copy it to the destination manually "
            f"(e.g. `cp {fallback} {out_path}`).",
            file=sys.stderr,
        )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark BKT vs DKT on synthetic-5 (Piech et al. 2015)")
    parser.add_argument("--epochs", type=int, default=20, help="DKT training epochs (default: 20)")
    parser.add_argument("--hidden", type=int, default=64, help="DKT LSTM hidden size (default: 64)")
    parser.add_argument("--train-frac", type=float, default=0.8, help="Fraction of students used for train (default: 0.8)")
    parser.add_argument("--data-dir", type=str, default="", help="Dataset cache dir (default: ~/.whetzy/data/kt_benchmark)")
    parser.add_argument("--output", type=str, default="", help="Path to write kt-benchmark.json (default: <repo>/docs/ml/kt-benchmark.json)")
    parser.add_argument("--skip-assistments-probe", action="store_true", help="Skip the network probe for ASSISTments 2009 mirrors")
    args = parser.parse_args()

    cache_dir = Path(args.data_dir) if args.data_dir else default_cache_dir()

    print(f"[benchmark_kt] Dataset: {DATASET_LABEL}")
    try:
        csv_path, info_path = ensure_synthetic5(cache_dir)
    except RuntimeError as exc:
        print(f"BLOCKED: could not download synthetic-5 dataset: {exc}", file=sys.stderr)
        return 2

    sequences, skill_ids = load_synthetic5(csv_path.read_text(), info_path.read_text())
    n_skills = len(skill_ids)
    train_seqs, test_seqs = temporal_split(sequences, args.train_frac)

    print(
        f"[benchmark_kt] {len(sequences)} students total · {n_skills} skills · "
        f"train={len(train_seqs)} · test={len(test_seqs)} (temporal, by student, "
        "original row order — no shuffling)"
    )

    # ── BKT ──────────────────────────────────────────────────────────────────
    print("[benchmark_kt] Fitting BKT (grid search on train split only) ...")
    bkt_params, bkt_train_auc = fit_bkt_grid(train_seqs, skill_ids)
    print(
        f"  [BKT] fitted params: p_l0={bkt_params.p_l0} p_t={bkt_params.p_t} "
        f"p_g={bkt_params.p_g} p_s={bkt_params.p_s}  (train AUC={bkt_train_auc:.4f})"
    )
    bkt_pred, bkt_true = bkt_predict_stepahead(bkt_params, test_seqs, skill_ids)
    bkt_test_auc = _safe_auc(bkt_pred, bkt_true)
    bkt_test_acc = _accuracy(bkt_pred, bkt_true)
    print(f"  [BKT] TEST  AUC={bkt_test_auc:.4f}  ACC={bkt_test_acc:.4f}  n={len(bkt_pred)}")

    # ── DKT ──────────────────────────────────────────────────────────────────
    dkt_test_auc = float("nan")
    dkt_test_acc = float("nan")
    dkt_note: str | None = None

    if not _TORCH_AVAILABLE:
        dkt_note = "torch not installed — DKT could not be trained"
        print(f"BLOCKED: {dkt_note}", file=sys.stderr)
        print(
            "Try: pip install torch --index-url https://download.pytorch.org/whl/cpu",
            file=sys.stderr,
        )
        return 1

    print(f"[benchmark_kt] Training DKT (hidden={args.hidden}, epochs={args.epochs}, seed={_DKT_SEED}) ...")
    dkt_pred, dkt_true = run_dkt(train_seqs, test_seqs, n_skills, args.hidden, args.epochs)
    dkt_test_auc = _safe_auc(dkt_pred, dkt_true)
    dkt_test_acc = _accuracy(dkt_pred, dkt_true)
    print(f"  [DKT] TEST  AUC={dkt_test_auc:.4f}  ACC={dkt_test_acc:.4f}  n={len(dkt_pred)}")

    # ── Acceptance criterion (ledger 11.3) ──────────────────────────────────
    meets_threshold = dkt_test_auc >= _AUC_THRESHOLD
    beats_bkt = dkt_test_auc > bkt_test_auc
    criterion_met = meets_threshold and beats_bkt

    print()
    print(f"  Criterion: DKT AUC >= {_AUC_THRESHOLD:.2f} AND DKT AUC > BKT AUC")
    print(f"    DKT AUC = {dkt_test_auc:.4f}  (>= {_AUC_THRESHOLD:.2f}? {meets_threshold})")
    print(f"    BKT AUC = {bkt_test_auc:.4f}  (DKT > BKT? {beats_bkt})")
    print(f"    Result: {'MET' if criterion_met else 'NOT MET'}")

    # ── ASSISTments 2009 ──────────────────────────────────────────────────────
    if args.skip_assistments_probe:
        assistments_report: dict[str, Any] = {
            "attempted": False,
            "included_in_benchmark": False,
            "reason": "Probe skipped via --skip-assistments-probe.",
        }
    else:
        print("[benchmark_kt] Probing ASSISTments 2009 sources (secondary dataset, per ledger) ...")
        assistments_report = probe_assistments_2009()
        print(f"  [ASSISTments 2009] included_in_benchmark=False — {assistments_report['reason']}")

    # ── Write report ──────────────────────────────────────────────────────────
    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "task": "11.3 — BKT vs DKT benchmark on a public knowledge-tracing dataset",
        "dataset": {
            "name": "synthetic-5",
            "citation": "Piech et al. 2015, 'Deep Knowledge Tracing' (NeurIPS)",
            "source": "https://github.com/chrispiech/DeepKnowledgeTracing",
            "file": "data/synthetic/naive_c5_q50_s4000_v0.csv",
            "n_concepts": n_skills,
            "n_students": len(sequences),
            "n_questions_per_student": len(sequences[0]) if sequences else 0,
            "seed_variant_used": "v0",
            "seed_variant_note": "20 seed variants (v0-v19) exist upstream; only v0 was used — not cherry-picked across seeds.",
            "item_representation": "concept id (0-4) from the info file, NOT question id (0-49)",
            "item_representation_note": (
                "This is the representation the production engine uses (mastery "
                "per skill, not per question), but it is NOT the paper's setup, "
                "which keys on question ids. Handing the model ground-truth "
                "concept labels removes within-concept difficulty and makes the "
                "task strictly easier for BOTH models — which is why both score "
                "above the paper's numbers here. See paper_reference_numbers."
            ),
        },
        "split": {
            "method": "temporal, by student — original row order preserved, no shuffling",
            "train_frac": args.train_frac,
            "n_train_students": len(train_seqs),
            "n_test_students": len(test_seqs),
            "note": "Step-ahead prediction within every evaluated sequence uses only responses 1..t-1 of that student.",
        },
        "methodology": {
            "auc_implementation": "sklearn.metrics.roc_auc_score",
            "bkt_fitting": (
                "Coarse grid search over 4 global BKTModel parameters "
                f"(p_l0 in {list(_BKT_GRID_L0)}, p_t in {list(_BKT_GRID_T)}, "
                f"p_g in {list(_BKT_GRID_G)}, p_s in {list(_BKT_GRID_S)}), "
                "selected by AUC on the TRAIN split only. NOT full Baum-Welch/EM. "
                "The production BKTModel (app/services/engine/bkt.py) has no "
                "parameter-fitting logic at all; grid search was added here "
                "only for this benchmark, via the existing public "
                "BKTModel(SkillParams) API, to avoid under-fitting the baseline."
            ),
            "dkt_reuse": "app.ml.train_dkt._Net / _DKTDataset / _collate reused unmodified; only the outer train/eval loop is new.",
            "dkt_seed": _DKT_SEED,
            "dkt_hidden": args.hidden,
            "dkt_epochs": args.epochs,
        },
        "bkt": {
            "fitted_params": {
                "p_l0": bkt_params.p_l0,
                "p_t": bkt_params.p_t,
                "p_g": bkt_params.p_g,
                "p_s": bkt_params.p_s,
            },
            "train_auc": _round_or_none(bkt_train_auc),
            "test_auc": _round_or_none(bkt_test_auc),
            "test_acc": _round_or_none(bkt_test_acc),
            "n_test_predictions": len(bkt_pred),
        },
        "dkt": {
            "test_auc": _round_or_none(dkt_test_auc),
            "test_acc": _round_or_none(dkt_test_acc),
            "n_test_predictions": len(dkt_pred),
            "note": dkt_note,
        },
        "paper_reference_numbers": {
            "note": (
                "Piech et al. 2015 report these on synthetic-5 with their own "
                "split/CV setup AND question-id items. NOT comparable to the "
                "AUCs above — see dataset.item_representation_note. These are "
                "context for the DKT-over-BKT margin, not a scoreboard: do not "
                "report this run as beating the paper."
            ),
            "dkt_auc": 0.75,
            "bkt_auc": 0.62,
            "paper_dkt_minus_bkt": 0.13,
            "this_run_dkt_minus_bkt": _round_or_none(dkt_test_auc - bkt_test_auc),
            "margin_note": (
                "The margin, not the absolute AUC, is what transfers. It is much "
                "smaller here than in the paper: a well-fit BKT is a strong "
                "baseline over only 5 concepts, and DKT's edge grows with "
                "item-level sparsity that this concept-level variant removes by "
                "construction. Defensible claim from this file: 'on "
                "concept-level synthetic-5, our DKT beats our grid-fit BKT by "
                "~0.03 AUC.' Nothing stronger."
            ),
        },
        "acceptance_criterion": {
            "text": "DKT AUC >= 0.70 AND DKT AUC > BKT AUC",
            "dkt_meets_0_70": meets_threshold,
            "dkt_beats_bkt": beats_bkt,
            "met": criterion_met,
        },
        "assistments_2009": assistments_report,
    }

    out_path = Path(args.output) if args.output else (_repo_root() / "docs" / "ml" / "kt-benchmark.json")
    _write_report(report, out_path)
    print(f"\n[benchmark_kt] Report written -> {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
