"""
Synthetic cohort system-validation harness.

Drives 30 synthetic personas against a running Whetzy API, concurrently.
Each persona follows a generative student model parameterised by its JSON file.

PURPOSE: system validation — crash detection, concurrency, content exhaustion,
         mastery-trajectory continuity.  NOT calibration.  NOT AUC evidence.
         All output is labelled "synthetic system validation".

Usage:
    python -m scripts.synthetic_cohort [--base-url URL] [--concurrency N]
                                       [--out PATH] [--verbose]

    Default base URL: http://localhost:8000/api/v1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PERSONAS_DIR = Path(__file__).parent.parent.parent / "content" / "personas"
DEFAULT_BASE_URL = os.getenv("WHETZY_BASE_URL", "http://localhost:8000/api/v1")
SYNTH_PASSWORD = "Synth!V@l1d2026"  # uniform password, never reused outside harness
MAX_CONCURRENT = 10  # stay within local rate limits

log = logging.getLogger("synth_cohort")


# ---------------------------------------------------------------------------
# Persona model
# ---------------------------------------------------------------------------

@dataclass
class Persona:
    id: str
    name: str
    archetype: str
    language: str
    track: str
    prior_knowledge: float
    learn_rate: float
    slip: float
    guess: float
    dont_know_propensity: float
    exec_skill: float
    session_length: int
    n_sessions: int
    abandon_prob: float

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Persona":
        return cls(
            id=d["id"],
            name=d["name"],
            archetype=d["archetype"],
            language=d.get("language", "es"),
            track=d["track"],
            prior_knowledge=float(d["prior_knowledge"]),
            learn_rate=float(d["learn_rate"]),
            slip=float(d["slip"]),
            guess=float(d["guess"]),
            dont_know_propensity=float(d["dont_know_propensity"]),
            exec_skill=float(d["exec_skill"]),
            session_length=int(d["session_length"]),
            n_sessions=int(d["n_sessions"]),
            abandon_prob=float(d["abandon_prob"]),
        )

    @property
    def email(self) -> str:
        return f"synth-{self.id}@whetzy-synth.io"

    @property
    def username(self) -> str:
        return f"synth_{self.id}"


# ---------------------------------------------------------------------------
# Per-persona result
# ---------------------------------------------------------------------------

@dataclass
class PersonaResult:
    persona_id: str
    persona_name: str
    archetype: str
    sessions_completed: int = 0
    sessions_abandoned: int = 0
    total_answers: int = 0
    correct_answers: int = 0
    declared_unknown_count: int = 0
    content_exhaustion_events: int = 0  # session returned no question
    mastery_trajectory: list[dict[str, float]] = field(default_factory=list)
    final_mastery: dict[str, float] = field(default_factory=dict)
    crash_log: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def record_mastery(self, skill_mastery: dict[str, float]) -> None:
        if skill_mastery:
            self.mastery_trajectory.append(dict(skill_mastery))
            self.final_mastery = dict(skill_mastery)


# ---------------------------------------------------------------------------
# Student model helpers
# ---------------------------------------------------------------------------

def compute_correct_prob(true_mastery: float, slip: float, guess: float) -> float:
    """P(correct | true_mastery) using BKT emission model."""
    return true_mastery * (1.0 - slip) + (1.0 - true_mastery) * guess


def update_mastery(
    true_mastery: float, was_correct: bool, learn_rate: float
) -> float:
    if was_correct:
        return true_mastery + learn_rate * (1.0 - true_mastery)
    else:
        return true_mastery * 0.97  # small decay on error


def pick_response_time(exec_skill: float) -> int:
    """Simulate response time in ms; higher exec_skill → faster."""
    base = 8000 - int(exec_skill * 5000)  # 3 000–8 000 ms range
    jitter = random.randint(-1000, 2000)
    return max(500, base + jitter)


# ---------------------------------------------------------------------------
# API client helpers
# ---------------------------------------------------------------------------

async def _login(client: httpx.AsyncClient, email: str) -> str | None:
    """Form-encoded login (OAuth2PasswordRequestForm). Returns token or None."""
    try:
        r = await client.post(
            "/auth/login",
            data={"username": email, "password": SYNTH_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", "60"))
            log.warning("Rate-limited on login, sleeping %ds", retry_after + 2)
            await asyncio.sleep(retry_after + 2)
            r2 = await client.post(
                "/auth/login",
                data={"username": email, "password": SYNTH_PASSWORD},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r2.status_code == 200:
                return r2.json().get("access_token")
    except Exception as exc:
        log.debug("login error: %s", exc)
    return None


async def register_or_login(
    client: httpx.AsyncClient, persona: Persona
) -> str | None:
    """
    Returns a Bearer token or None on failure.
    - Login uses OAuth2PasswordRequestForm (form-encoded, username=email).
    - Register uses JSON; on 201 the token is returned directly (no second login).
    - On 409 (already exists) falls back to login.
    - Respects Retry-After on 429.
    """
    # Try login first (idempotent for repeated runs)
    token = await _login(client, persona.email)
    if token:
        return token

    # Register — returns Token on 201
    try:
        reg_payload = {
            "email": persona.email,
            "username": persona.username,
            "display_name": persona.name,
            "language": persona.language,
            "password": SYNTH_PASSWORD,
        }
        r = await client.post("/auth/register", json=reg_payload)
        if r.status_code == 201:
            return r.json().get("access_token")
        if r.status_code == 409:
            # Already exists — login
            return await _login(client, persona.email)
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", "60"))
            log.warning("Rate-limited on register, sleeping %ds", retry_after + 2)
            await asyncio.sleep(retry_after + 2)
            r2 = await client.post("/auth/register", json=reg_payload)
            if r2.status_code == 201:
                return r2.json().get("access_token")
            if r2.status_code == 409:
                return await _login(client, persona.email)
        log.debug("register %s: HTTP %d %s", persona.id, r.status_code, r.text[:200])
    except Exception as exc:
        log.debug("register error for %s: %s", persona.id, exc)

    return None


async def start_session(
    client: httpx.AsyncClient, token: str, persona: Persona
) -> tuple[str | None, dict | None]:
    """Returns (session_id, first_question) or (None, None) on failure."""
    headers = {"Authorization": f"Bearer {token}"}
    payload: dict[str, Any] = {"mode": "study", "track_id": persona.track}
    try:
        r = await client.post("/quiz/start", json=payload, headers=headers)
        if r.status_code != 200:
            return None, None
        data = r.json()
        return str(data["session_id"]), data.get("question")
    except Exception:
        return None, None


async def submit_answer(
    client: httpx.AsyncClient,
    token: str,
    session_id: str,
    question: dict,
    declared_unknown: bool,
    selected_index: int | None,
) -> dict | None:
    headers = {"Authorization": f"Bearer {token}"}
    payload: dict[str, Any] = {
        "session_id": session_id,
        "question_id": question["id"],
        "declared_unknown": declared_unknown,
        "selected_index": None if declared_unknown else selected_index,
        "response_time_ms": pick_response_time(0.5),
    }
    if question.get("type") in ("fill_blank_exec", "fix_bug"):
        payload["exec_output"] = ""  # harness doesn't run Pyodide
    try:
        r = await client.post("/quiz/answer", json=payload, headers=headers)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


async def end_session(
    client: httpx.AsyncClient, token: str, session_id: str
) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = await client.post("/quiz/end", json={"session_id": session_id}, headers=headers)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Persona simulation
# ---------------------------------------------------------------------------

async def simulate_persona(
    persona: Persona,
    base_url: str,
    semaphore: asyncio.Semaphore,
    token: str,
    verbose: bool = False,
) -> PersonaResult:
    result = PersonaResult(
        persona_id=persona.id,
        persona_name=persona.name,
        archetype=persona.archetype,
    )
    t0 = time.monotonic()

    async with semaphore:
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:

            # Internal "true mastery" — independent from BKT estimates
            true_mastery = persona.prior_knowledge
            # Memory: question_id → correct_index (learned from prior answers)
            question_memory: dict[str, int] = {}

            for session_num in range(persona.n_sessions):
                session_id, question = await start_session(client, token, persona)

                if session_id is None:
                    result.crash_log.append(f"session_start_failed@s{session_num}")
                    continue

                if question is None:
                    result.content_exhaustion_events += 1
                    if verbose:
                        log.info("%s: content exhaustion at session %d", persona.id, session_num)
                    await end_session(client, token, session_id)
                    continue

                # Decide to abandon this session?
                if random.random() < persona.abandon_prob:
                    result.sessions_abandoned += 1
                    # Do NOT call /quiz/end — tests orphan session handling
                    continue

                answered = 0
                while question is not None and answered < persona.session_length:
                    q_id = question["id"]

                    # Decide declared_unknown
                    declared_unknown = random.random() < persona.dont_know_propensity

                    if declared_unknown:
                        selected_index = None
                        result.declared_unknown_count += 1
                    else:
                        correct_prob = compute_correct_prob(
                            true_mastery, persona.slip, persona.guess
                        )
                        wants_correct = random.random() < correct_prob

                        if wants_correct and q_id in question_memory:
                            # Use remembered correct index
                            if random.random() > persona.slip:
                                selected_index = question_memory[q_id]
                            else:
                                # slip: pick wrong index
                                choices = [i for i in range(4) if i != question_memory[q_id]]
                                selected_index = random.choice(choices) if choices else 0
                        else:
                            # Unknown question: random guess
                            selected_index = random.randint(0, 3)

                    ans = await submit_answer(
                        client, token, session_id, question,
                        declared_unknown, selected_index
                    )

                    if ans is None:
                        result.crash_log.append(f"answer_failed@s{session_num}q{answered}")
                        break

                    answered += 1
                    result.total_answers += 1
                    was_correct = ans.get("correct", False)
                    if was_correct:
                        result.correct_answers += 1

                    # Remember correct index for this question
                    if ans.get("correct_index") is not None:
                        question_memory[q_id] = ans["correct_index"]

                    # Update internal mastery
                    if not declared_unknown:
                        true_mastery = update_mastery(
                            true_mastery, was_correct, persona.learn_rate
                        )

                    # Record API mastery estimate
                    if ans.get("skill_mastery"):
                        result.record_mastery(ans["skill_mastery"])

                    # Next question from inline response
                    question = ans.get("next_question")
                    if question is None and answered < persona.session_length:
                        result.content_exhaustion_events += 1

                await end_session(client, token, session_id)
                result.sessions_completed += 1

    result.duration_seconds = time.monotonic() - t0
    if verbose:
        acc = result.correct_answers / result.total_answers if result.total_answers else 0
        log.info(
            "%s (%s): %d sessions, %d answers, acc=%.2f, mastery_points=%d, crashes=%d",
            persona.id, persona.archetype, result.sessions_completed,
            result.total_answers, acc, len(result.mastery_trajectory),
            len(result.crash_log),
        )
    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(results: list[PersonaResult]) -> dict:
    total_answers = sum(r.total_answers for r in results)
    total_correct = sum(r.correct_answers for r in results)
    total_sessions = sum(r.sessions_completed for r in results)
    total_abandoned = sum(r.sessions_abandoned for r in results)
    total_crashes = sum(len(r.crash_log) for r in results)
    total_exhaustion = sum(r.content_exhaustion_events for r in results)

    personas_out = []
    for r in results:
        acc = r.correct_answers / r.total_answers if r.total_answers else 0.0
        final_avg = (
            sum(r.final_mastery.values()) / len(r.final_mastery)
            if r.final_mastery else None
        )
        personas_out.append({
            "id": r.persona_id,
            "name": r.persona_name,
            "archetype": r.archetype,
            "sessions_completed": r.sessions_completed,
            "sessions_abandoned": r.sessions_abandoned,
            "total_answers": r.total_answers,
            "accuracy": round(acc, 4),
            "declared_unknown_count": r.declared_unknown_count,
            "content_exhaustion_events": r.content_exhaustion_events,
            "final_mastery_avg": round(final_avg, 4) if final_avg is not None else None,
            "mastery_trajectory_length": len(r.mastery_trajectory),
            "crash_log": r.crash_log,
            "duration_seconds": round(r.duration_seconds, 2),
        })

    return {
        "label": "synthetic system validation",
        "warning": (
            "All personas are synthetic. These numbers CANNOT be used to claim "
            "user accuracy, calibrate BKT, or publish AUC. Benchmark AUC comes "
            "from synthetic-5 (Piech 2015) — a fixed third-party dataset."
        ),
        "run_at": datetime.now(timezone.utc).isoformat(),
        "n_personas": len(results),
        "aggregate": {
            "sessions_completed": total_sessions,
            "sessions_abandoned": total_abandoned,
            "total_answers": total_answers,
            "overall_accuracy": round(total_correct / total_answers, 4) if total_answers else 0.0,
            "content_exhaustion_events": total_exhaustion,
            "crash_events": total_crashes,
            "personas_with_crashes": sum(1 for r in results if r.crash_log),
        },
        "personas": personas_out,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def load_personas(personas_dir: Path) -> list[Persona]:
    personas = []
    for p in sorted(personas_dir.glob("p*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            personas.append(Persona.from_dict(data))
        except Exception as exc:
            log.warning("Skipping %s: %s", p.name, exc)
    return personas


async def run(
    base_url: str,
    concurrency: int,
    out_path: Path,
    verbose: bool,
) -> None:
    personas = load_personas(PERSONAS_DIR)
    log.info("Loaded %d personas from %s", len(personas), PERSONAS_DIR)

    # Phase 1 — sequential auth to stay under 12-req/min rate limit.
    # Login tries first (idempotent for repeated runs), register only if needed.
    # ~5 s between requests → max 12/min, safe margin.
    tokens: dict[str, str] = {}
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as auth_client:
        for idx, persona in enumerate(personas):
            if idx > 0:
                await asyncio.sleep(6.0)  # 1 req/persona × 6s = 10/min < 12/min limit
            log.info("Auth [%d/%d] %s …", idx + 1, len(personas), persona.id)
            token = await register_or_login(auth_client, persona)
            if token is None:
                log.warning("Auth FAILED for %s — persona will be skipped", persona.id)
            else:
                tokens[persona.id] = token

    log.info("Auth complete: %d/%d personas authenticated", len(tokens), len(personas))

    # Phase 2 — parallel session simulation with pre-collected tokens.
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        simulate_persona(p, base_url, semaphore, token=tokens[p.id], verbose=verbose)
        for p in personas
        if p.id in tokens
    ]
    # Append stub results for personas that failed auth
    failed_personas = [p for p in personas if p.id not in tokens]
    stub_results = [
        PersonaResult(
            persona_id=p.id,
            persona_name=p.name,
            archetype=p.archetype,
            crash_log=["auth_failed"],
            duration_seconds=0.0,
        )
        for p in failed_personas
    ]
    results = list(await asyncio.gather(*tasks)) + stub_results

    report = build_report(list(results))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    agg = report["aggregate"]
    print(f"\n=== Synthetic Cohort - System Validation Report ===")
    print(f"Personas          : {report['n_personas']}")
    print(f"Sessions completed: {agg['sessions_completed']}")
    print(f"Sessions abandoned: {agg['sessions_abandoned']}")
    print(f"Total answers     : {agg['total_answers']}")
    print(f"Overall accuracy  : {agg['overall_accuracy']:.2%}")
    print(f"Content exhaustion: {agg['content_exhaustion_events']}")
    print(f"Crash events      : {agg['crash_events']} ({agg['personas_with_crashes']} personas)")
    print(f"\nFull report -> {out_path}")
    print(f"\nWARNING: {report['warning']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Whetzy synthetic cohort harness")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--concurrency", type=int, default=MAX_CONCURRENT)
    parser.add_argument(
        "--out",
        default="docs/synthetic_cohort_report.json",
        help="Output JSON report path (relative to repo root)",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Required to target a non-local host. SYNTH_PASSWORD is public in this "
             "repo, so running against a real deployment creates 30 accounts whose "
             "password anyone can read. Never point this at production.",
    )
    args = parser.parse_args()

    host = httpx.URL(args.base_url).host
    if host not in ("localhost", "127.0.0.1", "::1") and not args.allow_remote:
        parser.error(
            f"refusing to run against non-local host {host!r}: SYNTH_PASSWORD is "
            f"public in this repo. Pass --allow-remote only for a throwaway "
            f"environment, never production."
        )

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    repo_root = Path(__file__).parent.parent.parent
    out_path = repo_root / args.out

    asyncio.run(run(args.base_url, args.concurrency, out_path, args.verbose))


if __name__ == "__main__":
    main()
