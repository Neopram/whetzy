"""Guard: no motor file hardcodes its own domain-threshold literal (C.1,
2026-10-04).

Scans the motor files S3 owns (SESIONES.md §4.3) for threshold-shaped
literals that should instead import from
`app.services.engine.domain_thresholds` — the single source of truth this
PR introduces. Scoped to S3's own territory, not the whole repo: a sibling
file outside this list (e.g. `app/services/gamification/service.py`, S1's)
can still hardcode its own copy, and this guard will not see it — that one
is flagged as a NECESITO instead of fixed or enforced here.

Parses each file with `ast` rather than grepping its text, specifically so
a docstring or comment that quotes "p_known >= 0.95" as prose (this file's
own module docstring does, explaining the bug) can never be mistaken for
the real thing: actual code shapes only — a comparison against `p_known`,
a `threshold`-named default argument, or `.get("min_mastery_to_unlock", ...)`.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
ENGINE_DIR = BACKEND / "app" / "services" / "engine"
ML_DIR = BACKEND / "app" / "ml"

# Motor files outside app/services/engine and app/ml that also use a domain
# threshold. Kept as an explicit list (not a repo-wide scan) because that is
# the boundary of S3's own territory tonight.
OTHER_MOTOR_FILES = [
    BACKEND / "app" / "services" / "quiz.py",
    BACKEND / "app" / "services" / "domain_report.py",
    BACKEND / "app" / "services" / "progress.py",
    BACKEND / "app" / "services" / "track_exam.py",
    BACKEND / "app" / "services" / "content_loader.py",
    BACKEND / "app" / "api" / "v1" / "endpoints" / "ml.py",
    BACKEND / "app" / "api" / "v1" / "endpoints" / "placement.py",
    BACKEND / "app" / "api" / "v1" / "endpoints" / "quiz.py",
    BACKEND / "app" / "api" / "v1" / "endpoints" / "exams.py",
    BACKEND / "app" / "api" / "v1" / "endpoints" / "progress.py",
]

# The one file allowed to hold the real literal.
CANONICAL_FILE = ENGINE_DIR / "domain_thresholds.py"

_THRESHOLD_PARAM_NAMES = {"threshold", "mastery_threshold"}
_MASTERY_VALUE = 0.95
_UNLOCK_VALUE = 0.7


def _is_const(node: ast.expr | None, value: float) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _mentions_mastery(node: ast.expr) -> bool:
    """True if `node` is shaped like a reference to a mastery/p_known value:
    a name or attribute containing "p_known" or "mastery", or a `.get(...)`
    call on an object whose own name contains one of those (e.g.
    `mastery_by_skill.get(sid, 0.0)`, the real shape `quiz.py` used)."""
    needles = ("p_known", "mastery")
    if isinstance(node, ast.Name):
        return any(n in node.id for n in needles)
    if isinstance(node, ast.Attribute):
        return any(n in node.attr for n in needles) or _mentions_mastery(node.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return _mentions_mastery(node.func.value) or any(n in node.func.attr for n in needles)
    return False


def _violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []

    for node in ast.walk(tree):
        # A `threshold`/`mastery_threshold` parameter defaulting to a bare 0.95.
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            args = node.args
            defaults = list(zip(args.args[len(args.args) - len(args.defaults):], args.defaults, strict=True))
            for arg, default in defaults:
                if arg.arg in _THRESHOLD_PARAM_NAMES and _is_const(default, _MASTERY_VALUE):
                    found.append(f"{path.relative_to(BACKEND)}:{node.lineno}: "
                                 f"def {node.name}(..., {arg.arg}=0.95, ...)")

        # A direct comparison against `p_known` (or `...mastery_by_skill.get(...)`) and 0.95.
        if isinstance(node, ast.Compare) and len(node.comparators) == 1:
            left, right = node.left, node.comparators[0]
            for a, b in ((left, right), (right, left)):
                if _is_const(b, _MASTERY_VALUE) and _mentions_mastery(a):
                    found.append(
                        f"{path.relative_to(BACKEND)}:{node.lineno}: "
                        "comparison against a p_known/mastery value == 0.95"
                    )

        # `something.get("min_mastery_to_unlock", 0.7)`.
        if (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and len(node.args) == 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "min_mastery_to_unlock"
            and _is_const(node.args[1], _UNLOCK_VALUE)
        ):
            found.append(f'{path.relative_to(BACKEND)}:{node.lineno}: .get("min_mastery_to_unlock", 0.7)')

    return found


def _scanned_files() -> list[Path]:
    files = [p for p in ENGINE_DIR.glob("*.py") if p != CANONICAL_FILE]
    files += list(ML_DIR.glob("*.py"))
    files += list(OTHER_MOTOR_FILES)
    return [p for p in files if p.exists()]


def test_no_motor_file_hardcodes_its_own_domain_threshold() -> None:
    violations = [v for path in _scanned_files() for v in _violations_in(path)]
    assert violations == [], (
        "domain-threshold literal(s) found outside app/services/engine/domain_thresholds.py "
        "- import MASTERY_THRESHOLD / DEFAULT_MODULE_UNLOCK_MASTERY from there instead:\n"
        + "\n".join(violations)
    )


def test_the_canonical_module_is_excluded_from_the_scan() -> None:
    """Sanity check on the guard itself: the canonical file legitimately
    holds `settings.MASTERY_THRESHOLD` and is meant to, so it must be the
    one file the scan skips rather than flagging itself."""
    assert CANONICAL_FILE.exists()
    assert CANONICAL_FILE not in _scanned_files()
