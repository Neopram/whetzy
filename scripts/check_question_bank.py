#!/usr/bin/env python3
"""Structural checks over the shipped question bank (task 10.2).

These catch the mistakes that are easy to make when a bank grows to thousands of
hand-authored questions and impossible to spot by reading: a duplicated id, a
question that lost its English half, an option list with a repeat, and - the one
that actually changes what a learner experiences - correct answers clustered on
one position.

That last check is not pedantry. Authoring Domain 1 of the AWS track by hand
produced 7/59/5/1 across the four positions: 82 % of answers were option B,
because writing a plausible wrong option first and the right one second is a
habit you do not notice. A learner who spots that scores well while knowing
nothing, and the mastery estimate becomes a lie - which is red line 1.

No network access, so unlike scripts/check_content_sources.py this can run in
CI. Run it after changing the bank:

    python scripts/check_question_bank.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "questions"

# Below this many questions, position counts are noise rather than a pattern.
SKEW_MIN_SAMPLE = 40
# Por debajo de 40 preguntas un track recien empezado daria falsos positivos.
STEM_MIN_SAMPLE = 40
# Con opciones barajadas cada enunciado puede dar 3-4 preguntas defendibles; por
# debajo del 60 % distinto ya no se esta preguntando, se esta rellenando.
STEM_MIN_UNIQUE_SHARE = 0.60
IDENTICAL_STEM_MIN_CHARS = 15
# Opciones de una palabra: legitimas en shell o SQL (track15 llega al 56 %),
# pero un track entero al 95 % son distractores de relleno, no alternativas.
ONE_WORD_OPTION_MAX_SHARE = 0.80
EXEC_NEEDS_CODE = {"fill_blank_exec", "fix_bug", "sql_exec", "js_exec"}
SKEW_MAX_SHARE = 0.45
MIN_PER_SKILL = 6

# Density the adaptive engine actually needs, as opposed to the floor above.
#
# Taking a skill to mastery costs roughly 10-15 attempts of BKT evidence. Below
# that many items per skill the learner meets the same question again before
# mastering the concept, starts recognising the answer rather than knowing it,
# and `p_known` climbs on a memory of the option rather than of the idea. That
# is red line 1 broken from the content side, where no amount of engine work
# can fix it.
#
# It is a WARN, not a failure: the bank sits at ~8.0 today and closing the gap
# is authoring work measured in weeks. Ratchet it as tracks are filled in, so
# the number can only ever move forward.
TARGET_PER_SKILL = 15
# true/false balance: below this many in a track, the ratio is noise.
TF_MIN_SAMPLE = 25
TF_BAND = (0.35, 0.65)

# --- executable practice (17.3) -------------------------------------------
#
# Question types the learner actually runs, rather than picks an option for.
#
# `js_exec` added 2026-09-18 (task 18.3): Worker sandbox live in useRuntime.ts
# (Blob URL, no eval on main thread, console captured, timeout via terminate()),
# 2 questions authored in mod1401, e2e spec written in frontend/e2e/js_exec.spec.ts.
EXEC_TYPES = {"fill_blank_exec", "fix_bug", "sql_exec", "js_exec"}
EXEC_TARGET = 0.15

# Tracks and modules that do NOT chase the 15 % bar, each with the reason.
#
# This list is the honest half of 17.3, and it exists so the bar means
# something. Nothing in these runs in a browser: you cannot execute "should
# this be a microservice", a Docker build, a CI pipeline or an AWS console
# decision inside a Pyodide worker. Chasing the ratio here would produce fake
# exercises - a `fill_blank_exec` whose "execution" is a string comparison -
# which is a worse lie than a low number, because it inflates a metric the
# competitive scorecard reads. Their format of practice is scenario + decision
# (`multiple_choice` with context), and they are removed from the denominator
# rather than counted as failures.
#
# track09 (PCEP) is deliberately NOT here even though it sits at 0 %: it is a
# *Python* certification, Python runs in the browser, and it is the wedge of
# lane 1. Its zero is a real gap, not an exemption.
EXEC_EXEMPT_TRACKS = {
    "track05": "software architecture - design decisions, nothing to execute",
    "track08": "AWS Cloud Practitioner - console and service choices",
    "track10": "AWS Solutions Architect - design decisions",
    "track11": "AWS AI Practitioner - service choices",
    "track15": "Linux - shell commands run in a terminal, not CPython sandbox",
}
# Module-level exemptions inside a track that otherwise does chase the bar.
# Keyed by module id, which is "mod" plus the track and module digits of a skill
# id: sk|04|01|01 -> mod0401 (the last two digits are the skill and are dropped).
EXEC_EXEMPT_MODULES = {
    "mod0401": "Git - version control happens in a terminal, not a sandbox",
    "mod0406": "Docker - no container runtime in a browser",
    "mod0407": "CI/CD - pipelines are not runnable client-side",
    "mod1701": "Network fundamentals (OSI/IP) - conceptual; exec lives in mod1703",
    "mod1702": "Application protocols (HTTP/email/FTP) - conceptual; exec lives in mod1703",
}

# Per-track ratchet. Same idea as MIN_LESSONS: these are today's measured
# numbers, and they may only ever go up. A track that loses executable coverage
# because someone bulk-added multiple choice fails here rather than drifting
# down unnoticed - which is exactly how the ratio fell from 15,57 % to 7,33 %
# between two sessions without anybody deciding to.
EXEC_FLOOR = {
    "track01": 0.15,
    "track02": 0.15,
    "track03": 0.15,
    "track04": 0.15,
    # 1,9 % hasta que la sesion ar autoro 68 ejecutables. Sus 8 originales
    # importaban numpy/pandas y no podian correr en el navegador del alumno,
    # asi que el ratio de antes contaba preguntas rotas. Ver ADR-9 y 17.3.
    "track06": 0.15,
    # 0 % hasta que la sesion as autoro 78 ejecutables (mod0701-0706). AI
    # Engineering parecia un track no ejecutable y no lo es: atencion escalada,
    # softmax, BPE, top-p, coseno, chunking, RRF, ReAct, sha256 de datasets,
    # canary, paridad demografica, p95 y coste en tokens se implementan con
    # stdlib y corren en el navegador. Lo que no cabe es numpy. Ver 17.3.
    "track07": 0.15,
    # 0 % until session ar authored 42 executable questions for it. PCEP is the
    # wedge of lane 1 and it is a *Python* certification, so a zero here was
    # never a limitation of the medium - only of the bank.
    "track09": 0.15,
    # SQL — browser-executable with sql.js; all skills run queries
    "track12": 0.15,
    # 0 % hasta que la sesion ay autoro 49 ejecutables para track13 y 53 para
    # track40 (sesion 2026-09-18). Ambos usan Python stdlib: hashlib/hmac/secrets
    # para criptografia, re para logs/SIEM, ipaddress para redes, html.escape
    # para sanitizacion. Ver tarea 18.2.
    "track13": 0.15,
    "track40": 0.15,
    # 16.7 % on first commit (2 js_exec / 12 Q in mod1401 stub). Task 18.3.
    "track14": 0.15,
    # track16: Algoritmos - ~30% exec (fill_blank_exec in mod1601-1603). Floor set at first commit.
    "track16": 0.30,
    # track17: Redes - mod1703 has exec questions (sockets, urllib). Floor at 15% matches existing ratio.
    "track17": 0.15,
}


def track_key(path: Path) -> str:
    """The track a question file belongs to, not the folder it happens to sit in.

    `content/questions/` has TWELVE directories for ELEVEN tracks:
    `track08_aws_clf_c02` and `track08_aws_cloud_practitioner` are both track08
    (same `sk0801xx` skills). Keying the report by folder split that track in
    two and reported the smaller half at 2.5 Q/skill against a floor of 15 - a
    gap that does not exist, since the two halves together sit at 18.3. The
    same folder-counting mistake had `check_docs.py` accusing the ledger of
    lying about the track count.
    """
    name = path.parent.name
    return name[:7] if name.startswith("track") and name[5:7].isdigit() else name


def load() -> list[tuple[Path, dict]]:
    items = []
    for path in sorted(CONTENT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        # Both shapes exist in content/: a bare list, or {"questions": [...]}.
        # Checking the type first matters — data.get() on a list raises before
        # any default can apply, which silently excluded every list-shaped file.
        questions = data if isinstance(data, list) else data.get("questions", [])
        for q in questions:
            items.append((path, q))
    return items


@lru_cache(maxsize=1)
def declared_skills() -> frozenset[str]:
    """Every skill id the curriculum declares - the denominator for coverage.

    `tracks.json` is the authority here for the same reason `check_docs.py`
    reads it: a skill exists because a track declares it, not because some
    question happens to name it.
    """
    data = json.loads(
        (ROOT / "content" / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    return frozenset(
        skill["id"]
        for track in data["tracks"]
        for module in track.get("modules", [])
        for skill in module.get("skills", [])
    )


def main() -> int:
    items = load()
    problems: list[str] = []
    warnings: list[str] = []

    def fail(path: Path, qid: str, msg: str) -> None:
        problems.append(f"{path.relative_to(ROOT).as_posix()} [{qid}] {msg}")

    # --- ids unique across the whole bank, not just within a file ---
    seen: dict[str, Path] = {}
    for path, q in items:
        qid = q.get("id", "<no id>")
        if qid in seen:
            fail(path, qid, f"duplicate id, also in {seen[qid].name}")
        seen[qid] = path

    # --- bilingual parity (red line 3) and well-formed options ---
    for path, q in items:
        qid = q.get("id", "<no id>")
        for field in ("question_es", "question_en", "explanation_es", "explanation_en"):
            if not (q.get(field) or "").strip():
                fail(path, qid, f"{field} is empty - nothing ships in one language")
        if not (q.get("source") or "").strip():
            fail(path, qid, "no source - red line 2")

        opts_es, opts_en = q.get("options_es"), q.get("options_en")
        if opts_es is None and opts_en is None:
            continue  # open-ended types (fill_blank, *_exec) carry no options
        if not opts_es or not opts_en or len(opts_es) != len(opts_en):
            fail(path, qid, "option lists differ between languages")
            continue
        for side, opts in (("es", opts_es), ("en", opts_en)):
            if len(set(opts)) != len(opts):
                dupe = [o for o, n in Counter(opts).items() if n > 1][:1]
                fail(path, qid, f"repeated option in {side}: {dupe}")
        ci = q.get("correct_index")
        if ci is None or not (0 <= ci < len(opts_es)):
            fail(path, qid, f"correct_index {ci!r} out of range for {len(opts_es)} options")

    # --- el enunciado dice algo? ---
    #
    # Lo de arriba comprueba la FORMA de la pregunta; esto comprueba que haya
    # pregunta. Un generador al que se le pide volumen devuelve el mismo
    # enunciado corto una y otra vez con las opciones barajadas, y eso pasaba
    # todas las comprobaciones anteriores: ids unicos, ES y EN presentes,
    # opciones bien formadas y hasta las posiciones repartidas. Asi entraron
    # 400 preguntas por track salidas de 14 enunciados.
    stems: dict[str, Counter] = defaultdict(Counter)
    for path, q in items:
        stem = (q.get("question_es") or "").strip()
        if stem:
            stems[track_key(path)][stem] += 1

    one_word: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for path, q in items:
        for opt in (q.get("options_es") or []):
            one_word[track_key(path)][1] += 1
            if len(opt.split()) <= 1:
                one_word[track_key(path)][0] += 1

    for track, (short_opts, total_opts) in sorted(one_word.items()):
        if total_opts < STEM_MIN_SAMPLE:
            continue
        share = short_opts / total_opts
        if share > ONE_WORD_OPTION_MAX_SHARE:
            problems.append(
                f"{track}: {share:.0%} de las opciones son de una sola palabra "
                f"({short_opts}/{total_opts}). Cuatro sustantivos sueltos no son "
                f"cuatro alternativas defendibles"
            )

    for track, dist in sorted(stems.items()):
        total = sum(dist.values())
        if total < STEM_MIN_SAMPLE:
            continue
        unique = len(dist)
        if unique / total < STEM_MIN_UNIQUE_SHARE:
            worst, n = dist.most_common(1)[0]
            problems.append(
                f"{track}: solo {unique} enunciados distintos para {total} preguntas "
                f"({unique / total:.0%}); el mas repetido sale {n} veces: {worst[:60]!r}. "
                f"Barajar las opciones de la misma pregunta no son preguntas nuevas"
            )

    for path, q in items:
        qid = q.get("id", "<no id>")
        stem_es = (q.get("question_es") or "").strip()
        stem_en = (q.get("question_en") or "").strip()

        # Dos idiomas nativos es la linea roja 3. Si la cadena es identica no se
        # tradujo (salvo que sea codigo o una sigla suelta, de ahi el minimo).
        if stem_es and stem_es == stem_en and len(stem_es) > IDENTICAL_STEM_MIN_CHARS:
            problems.append(
                f"{path.name} {qid}: question_es y question_en son identicas - sin traducir"
            )

        # Un ejecutable sin codigo no se puede ejecutar: o lleva un bloque ``` en
        # el enunciado (fill_blank_exec, fix_bug) o trae code_es/code_en
        # (sql_exec). Sin una de las dos, el runtime no tiene que correr.
        if q.get("type") in EXEC_NEEDS_CODE:
            has_fence = "```" in (q.get("question_es") or "")
            has_code = bool((q.get("code_es") or "").strip())
            if not has_fence and not has_code:
                problems.append(
                    f"{path.name} {qid}: {q.get('type')} sin codigo que ejecutar "
                    f"(ni bloque ``` en el enunciado ni code_es)"
                )

    # --- answer position skew, per track ---
    #
    # true_false is measured separately below. Its two options are
    # Verdadero/Falso, so a lopsided distribution there is not a position
    # problem to be fixed by reordering (rendering "Falso, Verdadero" is just
    # odd) - it means too many statements were written to be true, which needs
    # rewriting. Mixing the two into one number hides both.
    by_track: dict[str, Counter] = defaultdict(Counter)
    tf_track: dict[str, Counter] = defaultdict(Counter)
    by_skill: dict[str, Counter] = defaultdict(Counter)
    for path, q in items:
        ci = q.get("correct_index")
        opts = q.get("options_es")
        if ci is None or not opts:
            continue
        if q.get("type") == "true_false":
            tf_track[track_key(path)][ci] += 1
        else:
            by_track[track_key(path)][ci] += 1
            skill = q.get("skill_id", "unknown")
            by_skill[skill][ci] += 1

    for track, dist in sorted(by_track.items()):
        total = sum(dist.values())
        if total < SKEW_MIN_SAMPLE:
            continue
        worst, count = dist.most_common(1)[0]
        share = count / total
        if share > SKEW_MAX_SHARE:
            problems.append(
                f"{track}: {share:.0%} of multi-option answers sit at position {worst} "
                f"({count}/{total}) - guessable without knowing the material. "
                "Run scripts/rebalance_answer_positions.py"
            )

    # --- per-skill template detection (≥75% at same position = template artifact) ---
    SKILL_TEMPLATE_MAX = 0.75
    SKILL_MIN_SAMPLE = 10
    for skill, dist in sorted(by_skill.items()):
        total = sum(dist.values())
        if total < SKILL_MIN_SAMPLE:
            continue
        worst, count = dist.most_common(1)[0]
        share = count / total
        if share >= SKILL_TEMPLATE_MAX:
            problems.append(
                f"{skill}: {share:.0%} of answers at position {worst} ({count}/{total}) "
                "- likely template artifact. Run fix_skew or rewrite."
            )

    # --- true/false balance, reported but not failed on ---
    #
    # Measured per track as well as overall: the first version of this check was
    # global only, and a global 59 % hid track03 sitting at 83 %. A learner
    # studies one track at a time, so the per-track number is the one that
    # describes what they actually experience.
    tf_all = Counter()
    for c in tf_track.values():
        tf_all.update(c)
    tf_total = sum(tf_all.values())

    def flag(label: str, dist: Counter) -> None:
        total = sum(dist.values())
        if total < TF_MIN_SAMPLE:
            return
        share_true = dist[0] / total
        if not TF_BAND[0] <= share_true <= TF_BAND[1]:
            side = "true" if share_true > 0.5 else "false"
            worst = dist[0] if side == "true" else dist[1]
            warnings.append(
                f"{label}: true/false questions are {max(share_true, 1 - share_true):.0%} "
                f"\"{side}\" ({worst}/{total}) - always answering {side} scores that much. "
                "Fixing it means rewriting statements, not reordering options"
            )

    if tf_total:
        flag("overall", tf_all)
    for track, dist in sorted(tf_track.items()):
        flag(track, dist)

    # --- per-skill floor ---
    # Counted over the skills the CURRICULUM declares, not over the skills the
    # questions mention. Those are not the same set, and the difference is the
    # worst case rather than a corner one: a skill with zero questions never
    # appears as a key in a Counter built from the bank, so the version of this
    # check that iterated the questions reported PASS while track13 shipped
    # three skills - `Politicas y marcos de seguridad (NIST CSF)`, `TLS/HTTPS y
    # certificados digitales` and `Seguridad inalambrica (WPA2/WPA3)` - that a
    # learner could open and find completely empty. Same shape as the
    # `test_exec_questions.py` hard-coded track list (17.3): the check could
    # only ever see what was already there.
    per_skill = Counter(q.get("skill_id") for _, q in items)
    for skill in sorted(declared_skills()):
        n = per_skill.get(skill, 0)
        if n < MIN_PER_SKILL:
            problems.append(f"skill {skill} has {n} question(s); the floor is {MIN_PER_SKILL}")
    orphans = sorted(set(per_skill) - declared_skills())
    for skill in orphans:
        problems.append(
            f"{per_skill[skill]} question(s) point at skill {skill}, which no track "
            f"declares; the loader drops them silently"
        )

    # --- engine density, per track ---
    # Reported per track because that is the unit authoring happens in, and
    # because the averages differ sharply: the certification track was built at
    # the right density while the original seven were not.
    # Counted over ALL questions, not just the ones with options. `by_track`
    # holds the answer-position distribution, so it only sees multiple choice;
    # dividing that subset by every skill in the track would report a density
    # well below the real one and send authoring after a phantom gap.
    skills_per_track: dict[str, set[str]] = {}
    questions_per_track: Counter[str] = Counter()
    for path, q in items:
        skill = q.get("skill_id")
        if not skill:
            continue
        # Same key as by_track, so the two columns line up on one row.
        skills_per_track.setdefault(track_key(path), set()).add(skill)
        questions_per_track[track_key(path)] += 1

    # Rows are driven by `questions_per_track`, not by `by_track`. `by_track`
    # only sees questions that carry options, so a directory whose questions are
    # all `fill_blank` gets no row at all: `track08_aws_clf_c02` holds 48 of
    # them and was counted in the total while never appearing in the per-track
    # report, which is why the rows summed to 4.464 against a total of 4.512.
    # A track the report cannot show is a track nobody audits.
    print(f"\n[bank] {len(items)} questions across {len(questions_per_track)} tracks, "
          f"{len(per_skill)} skills\n")
    for track in sorted(questions_per_track):
        dist = by_track.get(track, Counter())
        total = questions_per_track.get(track, 0)
        spread = "/".join(str(dist[i]) for i in range(4))
        n_skills = len(skills_per_track.get(track, ()))
        density = f"{total / n_skills:>5.1f}" if n_skills else "    -"
        mark = " " if not n_skills or total / n_skills >= TARGET_PER_SKILL else "*"
        print(f"  {track:<38} {total:>5} Q   {density} Q/skill{mark}  positions {spread}")

    overall_density = len(items) / len(per_skill) if per_skill else 0.0
    if overall_density < TARGET_PER_SKILL:
        short = int(TARGET_PER_SKILL * len(per_skill)) - len(items)
        warnings.append(
            f"bank density is {overall_density:.1f} Q/skill against a target of "
            f"{TARGET_PER_SKILL} (* marks the tracks below it). That is {short} more "
            "questions. Under-dense skills repeat before they are mastered, so "
            "p_known ends up measuring recall of the option rather than of the idea"
        )

    # --- executable practice per track (17.3) ---
    #
    # Reported per track and against a floor that only rises, because the ratio
    # is one of the numbers the competitive scorecard leans on and it moved by
    # eight points between two sessions without anyone deciding it should.
    exec_total: Counter[str] = Counter()
    exec_hits: Counter[str] = Counter()
    for path, q in items:
        track = track_key(path)
        skill = q.get("skill_id") or ""
        # sk040101 -> mod0401: track digits then module digits, skill digits dropped.
        module = "mod" + skill[2:6] if skill.startswith("sk") else ""
        if track in EXEC_EXEMPT_TRACKS or module in EXEC_EXEMPT_MODULES:
            continue
        exec_total[track] += 1
        if q.get("type") in EXEC_TYPES:
            exec_hits[track] += 1

    print("\n  executable practice (17.3)")
    for track in sorted(exec_total):
        total = exec_total[track]
        hits = exec_hits[track]
        ratio = hits / total if total else 0.0
        floor = EXEC_FLOOR.get(track, 0.0)
        if ratio + 1e-9 < floor:
            problems.append(
                f"{track}: executable practice fell to {ratio:.1%} ({hits}/{total}) "
                f"from a floor of {floor:.0%}. The floor only moves up - if this is "
                "deliberate, change EXEC_FLOOR and say why in the commit"
            )
        mark = " " if ratio >= EXEC_TARGET else "*"
        print(f"  {track:<38} {hits:>4}/{total:<5} = {ratio:>5.1%}{mark}  floor {floor:.0%}")
    for track, reason in sorted(EXEC_EXEMPT_TRACKS.items()):
        print(f"  {track:<38} {'exempt':>10}     {reason}")

    below = sorted(t for t, n in exec_total.items() if n and exec_hits[t] / n < EXEC_TARGET)
    if below:
        warnings.append(
            f"executable practice is under {EXEC_TARGET:.0%} in: {', '.join(below)} "
            "(* above). This is authoring work, not a mechanical fix; the exempt "
            "tracks are listed with their reasons and are out of the denominator"
        )

    # Warnings are real findings that this tool is the wrong place to fail on:
    # they need authoring work, not a mechanical fix, so blocking CI on them
    # would just teach people to silence the tool.
    for w in warnings:
        print(f"\n  WARN  {w}")

    if problems:
        print(f"\n[bank] FAIL - {len(problems)} problem(s):\n")
        for p in problems[:40]:
            print(f"  {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        print()
        return 1

    print("\n[bank] PASS - ids unique, both languages present, options well formed, "
          "no position skew\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
