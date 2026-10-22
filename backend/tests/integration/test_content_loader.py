"""Tests for the content loader — the ingest path that runs on every deploy.

Two layers:
  * Hermetic: a tiny curriculum/questions/glossary tree built in tmp_path and
    pointed at with CONTENT_DIR, so upsert semantics are asserted precisely.
  * Real corpus: the repo's own `content/` tree is loaded once, proving the
    path that `start.sh` runs in production actually ingests the bank with
    zero skipped items.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select

from app.models.content import Domain, GlossaryTerm, Module, Question, Skill, Track
from app.services import content_loader
from app.services.content_loader import _content_root, load_content

# ── helpers ───────────────────────────────────────────────────────────────────


def _declared_track_count() -> int:
    """How many tracks the shipped curriculum declares.

    Read from `tracks.json` instead of hard-coded so that adding a track is a
    one-file change: the literal this replaced (8) silently went stale when
    tracks 09-11 shipped and turned the whole backend CI job red.
    """
    payload = json.loads((_content_root() / "curriculum" / "tracks.json").read_text("utf-8"))
    return len(payload if isinstance(payload, list) else payload["tracks"])


def _track_payload(**over: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": "trackX",
        "name_es": "Pista X",
        "name_en": "Track X",
        "order": 1,
        "icon": "🧪",
        "color": "#1CB0F6",
        "modules": [
            {
                "id": "trackX_m1",
                "name_es": "Modulo 1",
                "name_en": "Module 1",
                "order": 1,
                "description_es": "desc es",
                "description_en": "desc en",
                "min_mastery_to_unlock": 0.7,
                "skills": [
                    {"id": "skX01", "name_es": "Habilidad 1", "name_en": "Skill 1", "order": 1},
                    {"id": "skX02", "name_es": "Habilidad 2", "name_en": "Skill 2", "order": 2},
                ],
            }
        ],
    }
    data.update(over)
    return data


def _question_payload(qid: str = "qX01", skill_id: str = "skX01", **over: Any) -> dict[str, Any]:
    q: dict[str, Any] = {
        "id": qid,
        "skill_id": skill_id,
        "type": "mcq",
        "difficulty_tier": "medium",
        "question_es": "¿Pregunta?",
        "question_en": "Question?",
        "options_es": ["a", "b"],
        "options_en": ["a", "b"],
        "correct_index": 0,
        "explanation_es": "porque si",
        "explanation_en": "because yes",
        "source": "https://docs.python.org/3/",
        "expected_time_ms": 15000,
    }
    q.update(over)
    return q


def _term_payload(tid: str = "glX01", **over: Any) -> dict[str, Any]:
    t: dict[str, Any] = {
        "id": tid,
        "term_es": "Variable",
        "term_en": "Variable",
        "definition_es": "Un nombre enlazado a un objeto.",
        "definition_en": "A name bound to an object.",
        "source": "https://docs.python.org/3/",
    }
    t.update(over)
    return t


def build_tree(
    root: Path,
    *,
    tracks: list[dict[str, Any]] | None = None,
    questions: dict[str, Any] | None = None,
    glossary: dict[str, Any] | None = None,
) -> Path:
    """Write a minimal content tree and return its root."""
    (root / "curriculum").mkdir(parents=True, exist_ok=True)
    (root / "curriculum" / "tracks.json").write_text(
        json.dumps({"tracks": tracks if tracks is not None else [_track_payload()]}),
        encoding="utf-8",
    )
    qdir = root / "questions" / "trackX"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "bank.json").write_text(
        json.dumps(questions if questions is not None else {"questions": [_question_payload()]}),
        encoding="utf-8",
    )
    if glossary is not None:
        gdir = root / "glossary"
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "trackX.json").write_text(json.dumps(glossary), encoding="utf-8")
    return root


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = build_tree(tmp_path / "content")
    monkeypatch.setenv("CONTENT_DIR", str(root))
    return root


# ── _content_root ─────────────────────────────────────────────────────────────


class TestContentRoot:
    def test_env_override_wins(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("CONTENT_DIR", str(tmp_path))
        assert _content_root() == tmp_path

    def test_falls_back_to_repo_layout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        root = _content_root()
        assert root.name == "content"

    def test_repo_layout_actually_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Guards the `parents[3]` hop: a file move would silently break prod ingest.
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        root = _content_root()
        assert (root / "curriculum" / "tracks.json").is_file()
        assert (root / "questions").is_dir()


# ── curriculum ingest ─────────────────────────────────────────────────────────


class TestCurriculum:
    @pytest.mark.asyncio
    async def test_creates_track_module_and_skills(self, db_session, tree: Path) -> None:
        stats = await load_content(db_session)
        assert stats["tracks"] == 1

        track = await db_session.get(Track, "trackX")
        assert track is not None
        assert track.name_es == "Pista X"
        assert track.name_en == "Track X"
        assert track.icon == "🧪"
        assert track.color == "#1CB0F6"

        module = await db_session.get(Module, "trackX_m1")
        assert module is not None
        assert module.track_id == "trackX"
        assert module.min_mastery_to_unlock == pytest.approx(0.7)

        skills = (await db_session.execute(select(Skill))).scalars().all()
        assert {s.id for s in skills} == {"skX01", "skX02"}

    @pytest.mark.asyncio
    async def test_applies_defaults_for_optional_fields(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bare = {
            "id": "trackY",
            "name_es": "Y",
            "name_en": "Y",
            "modules": [
                {
                    "id": "mY",
                    "name_es": "m",
                    "name_en": "m",
                    "skills": [{"id": "skY", "name_es": "s", "name_en": "s"}],
                }
            ],
        }
        root = build_tree(
            tmp_path / "c",
            tracks=[bare],
            questions={"questions": [_question_payload("qY", "skY")]},
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        track = await db_session.get(Track, "trackY")
        assert track is not None
        assert track.order == 0
        assert track.icon == "📘"
        assert track.color == "#1CB0F6"

        module = await db_session.get(Module, "mY")
        assert module is not None
        assert module.order == 1  # enumerate fallback
        assert module.description_es == ""
        assert module.min_mastery_to_unlock == pytest.approx(0.7)

        skill = await db_session.get(Skill, "skY")
        assert skill is not None
        assert skill.order == 1

    @pytest.mark.asyncio
    async def test_rerun_updates_instead_of_duplicating(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(tmp_path / "c")
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        renamed = _track_payload(name_es="Pista Renombrada")
        (root / "curriculum" / "tracks.json").write_text(
            json.dumps({"tracks": [renamed]}), encoding="utf-8"
        )
        await load_content(db_session)

        tracks = (await db_session.execute(select(Track))).scalars().all()
        assert len(tracks) == 1
        assert tracks[0].name_es == "Pista Renombrada"


# ── question ingest ───────────────────────────────────────────────────────────


class TestQuestions:
    @pytest.mark.asyncio
    async def test_ingests_question_fields(self, db_session, tree: Path) -> None:
        stats = await load_content(db_session)
        assert stats["questions"] == 1
        assert stats["skipped"] == 0
        assert stats["files"] == 1

        q = await db_session.get(Question, "qX01")
        assert q is not None
        assert q.skill_id == "skX01"
        assert q.type == "mcq"
        assert q.question_es == "¿Pregunta?"
        assert q.question_en == "Question?"
        assert q.correct_index == 0
        assert q.source == "https://docs.python.org/3/"
        assert q.expected_time_ms == 15000

    @pytest.mark.asyncio
    async def test_unknown_skill_is_skipped_not_fatal(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            questions={
                "questions": [
                    _question_payload("good", "skX01"),
                    _question_payload("orphan", "sk_does_not_exist"),
                ]
            },
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)

        assert stats["questions"] == 1
        assert stats["skipped"] == 1
        assert await db_session.get(Question, "good") is not None
        assert await db_session.get(Question, "orphan") is None

    @pytest.mark.asyncio
    async def test_irt_difficulty_seeds_elo_rating(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            questions={
                "questions": [
                    _question_payload("easy", difficulty=-1.0),
                    _question_payload("hard", difficulty=2.0),
                    _question_payload("plain"),  # no difficulty key
                ]
            },
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        easy = await db_session.get(Question, "easy")
        hard = await db_session.get(Question, "hard")
        plain = await db_session.get(Question, "plain")
        assert easy is not None and hard is not None and plain is not None
        assert easy.elo_rating == pytest.approx(1500.0 - 120.0)
        assert hard.elo_rating == pytest.approx(1500.0 + 240.0)
        assert plain.elo_rating == pytest.approx(1500.0)

    @pytest.mark.asyncio
    async def test_irt_discrimination_and_guessing(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            questions={"questions": [_question_payload("irt", discrimination=1.4, guessing=0.25)]},
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        q = await db_session.get(Question, "irt")
        assert q is not None
        assert q.discrimination == pytest.approx(1.4)
        assert q.guessing == pytest.approx(0.25)

    @pytest.mark.asyncio
    async def test_bare_list_payload_is_accepted(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Some bank files are a top-level list rather than {"questions": [...]}.
        root = build_tree(tmp_path / "c", questions=[_question_payload("bare")])  # type: ignore[arg-type]
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)
        assert stats["questions"] == 1
        assert await db_session.get(Question, "bare") is not None

    @pytest.mark.asyncio
    async def test_rerun_updates_question_in_place(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(tmp_path / "c")
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        (root / "questions" / "trackX" / "bank.json").write_text(
            json.dumps({"questions": [_question_payload("qX01", question_es="corregida")]}),
            encoding="utf-8",
        )
        await load_content(db_session)

        total = await db_session.scalar(select(func.count(Question.id)))
        assert total == 1
        q = await db_session.get(Question, "qX01")
        assert q is not None
        assert q.question_es == "corregida"

    @pytest.mark.asyncio
    async def test_nested_question_dirs_are_walked(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(tmp_path / "c")
        deep = root / "questions" / "trackX" / "sub" / "deeper"
        deep.mkdir(parents=True)
        (deep / "more.json").write_text(
            json.dumps({"questions": [_question_payload("deep", "skX02")]}), encoding="utf-8"
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)

        assert stats["files"] == 2
        assert await db_session.get(Question, "deep") is not None


# ── glossary ingest ───────────────────────────────────────────────────────────


class TestGlossary:
    @pytest.mark.asyncio
    async def test_missing_glossary_dir_is_optional(self, db_session, tree: Path) -> None:
        stats = await load_content(db_session)
        assert stats["glossary"] == 0

    @pytest.mark.asyncio
    async def test_file_level_track_id_is_inherited(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            glossary={"track_id": "trackX", "terms": [_term_payload("glX01"), _term_payload("glX02")]},
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)

        assert stats["glossary"] == 2
        term = await db_session.get(GlossaryTerm, "glX01")
        assert term is not None
        assert term.track_id == "trackX"
        assert term.term_en == "Variable"

    @pytest.mark.asyncio
    async def test_per_term_track_id_overrides_file_level(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            glossary={
                "track_id": "trackX",
                "terms": [_term_payload("glX01", track_id="nope"), _term_payload("glX02")],
            },
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)

        assert stats["glossary"] == 1
        assert stats["skipped"] == 1
        assert await db_session.get(GlossaryTerm, "glX01") is None
        assert await db_session.get(GlossaryTerm, "glX02") is not None

    @pytest.mark.asyncio
    async def test_order_falls_back_to_file_position(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            glossary={
                "track_id": "trackX",
                "terms": [_term_payload("a"), _term_payload("b"), _term_payload("c", order=99)],
            },
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        a = await db_session.get(GlossaryTerm, "a")
        b = await db_session.get(GlossaryTerm, "b")
        c = await db_session.get(GlossaryTerm, "c")
        assert a is not None and b is not None and c is not None
        assert (a.order, b.order, c.order) == (1, 2, 99)

    @pytest.mark.asyncio
    async def test_bare_list_glossary_payload(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c", glossary=[_term_payload("solo", track_id="trackX")]  # type: ignore[arg-type]
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        stats = await load_content(db_session)
        assert stats["glossary"] == 1

    @pytest.mark.asyncio
    async def test_rerun_updates_term_in_place(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c", glossary={"track_id": "trackX", "terms": [_term_payload("glX01")]}
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)
        (root / "glossary" / "trackX.json").write_text(
            json.dumps(
                {"track_id": "trackX", "terms": [_term_payload("glX01", definition_es="nueva")]}
            ),
            encoding="utf-8",
        )
        await load_content(db_session)

        total = await db_session.scalar(select(func.count(GlossaryTerm.id)))
        assert total == 1
        term = await db_session.get(GlossaryTerm, "glX01")
        assert term is not None
        assert term.definition_es == "nueva"


# ── denormalized counts ───────────────────────────────────────────────────────


class TestTrackCounts:
    @pytest.mark.asyncio
    async def test_total_questions_is_denormalized(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = build_tree(
            tmp_path / "c",
            questions={
                "questions": [
                    _question_payload("q1", "skX01"),
                    _question_payload("q2", "skX01"),
                    _question_payload("q3", "skX02"),
                ]
            },
        )
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        track = await db_session.get(Track, "trackX")
        assert track is not None
        assert track.total_questions == 3

    @pytest.mark.asyncio
    async def test_track_without_questions_counts_zero(
        self, db_session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        empty = _track_payload(id="trackEmpty")
        empty["modules"][0]["id"] = "mEmpty"
        empty["modules"][0]["skills"] = [
            {"id": "skEmpty", "name_es": "s", "name_en": "s", "order": 1}
        ]
        root = build_tree(tmp_path / "c", tracks=[_track_payload(), empty])
        monkeypatch.setenv("CONTENT_DIR", str(root))
        await load_content(db_session)

        track = await db_session.get(Track, "trackEmpty")
        assert track is not None
        assert track.total_questions == 0


# ── the real corpus (the path start.sh runs in production) ────────────────────


class TestCertificationDomains:
    """Domains exist in the schema since 10.1 but were never populated until
    10.3, so `Skill.domain_id` was null for every question in the bank and a
    per-domain report had nothing to group by."""

    @pytest.mark.asyncio
    async def test_certification_track_loads_its_exam_domains(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        domains = (
            await db_session.scalars(
                select(Domain).where(Domain.track_id == "track08").order_by(Domain.order)
            )
        ).all()

        assert [d.name_en for d in domains] == [
            "Domain 1: Cloud Concepts",
            "Domain 2: Security and Compliance",
            "Domain 3: Cloud Technology and Services",
            "Domain 4: Billing, Pricing, and Support",
        ]
        # The published CLF-C02 blueprint. If these drift, the per-domain report
        # and the exam's question mix stop mirroring the real exam.
        assert [d.weight_pct for d in domains] == [24, 30, 34, 12]
        assert sum(d.weight_pct for d in domains) == 100

    @pytest.mark.asyncio
    async def test_every_certification_skill_belongs_to_a_domain(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A skill with no domain is a question that no report can attribute."""
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        orphans = (
            await db_session.scalars(
                select(Skill.id)
                .join(Module, Skill.module_id == Module.id)
                .where(Module.track_id == "track08", Skill.domain_id.is_(None))
            )
        ).all()
        assert orphans == [], f"certification skills with no exam domain: {orphans}"

    @pytest.mark.asyncio
    async def test_learning_tracks_have_no_domains(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only certification tracks mirror a blueprint; the learning tracks must
        not acquire domains as a side effect.

        Derived from `Track.is_certification` rather than naming a track id: this
        assertion used to read `!= "track08"` and broke the moment tracks 09-11
        (PCEP, SAA-C03, AIF-C01) shipped their own blueprints, flagging correct
        data as stray.
        """
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        stray = (
            await db_session.scalars(
                select(Domain)
                .join(Track, Domain.track_id == Track.id)
                .where(Track.is_certification.is_(False))
            )
        ).all()
        assert stray == []

    @pytest.mark.asyncio
    async def test_certification_track_carries_its_exam_format(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        track = await db_session.get(Track, "track08")
        assert track is not None
        assert track.is_certification is True
        assert track.cert_provider == "AWS"
        # 65 questions in 90 minutes, from the official exam page.
        assert track.exam_question_count == 65
        assert track.exam_duration_minutes == 90

        learning = await db_session.get(Track, "track01")
        assert learning is not None
        assert learning.is_certification is False
        assert learning.exam_question_count is None

    @pytest.mark.asyncio
    async def test_certification_track_keeps_its_blueprint_identity(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """42.12: the exam code, the guide it was built from and a fingerprint
        of the blueprint. Without them nothing could tell which version of
        the vendor's guide a readiness figure was computed against."""
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        track = await db_session.get(Track, "track08")
        assert track is not None
        assert track.cert_code == "CLF-C02"
        assert track.exam_guide == "AWS Certified Cloud Practitioner (CLF-C02) Exam Guide, Version 1.0"
        assert track.exam_guide_url is not None and track.exam_guide_url.startswith("https://")
        assert track.blueprint_version is not None and len(track.blueprint_version) == 12
        first = track.blueprint_version

        await load_content(db_session)  # idempotent: same content, same fingerprint
        assert (await db_session.get(Track, "track08")).blueprint_version == first

        learning = await db_session.get(Track, "track01")
        assert learning is not None
        assert (learning.cert_code, learning.exam_guide, learning.blueprint_version) == (None, None, None)


class TestRealCorpus:
    @pytest.mark.asyncio
    async def test_repo_content_loads_with_zero_skipped(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every shipped question must map to a skill declared in tracks.json.

        A non-zero `skipped` means questions silently never reach users — the
        exact failure the loader is supposed to make impossible.
        """
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        stats = await load_content(db_session)

        assert stats["skipped"] == 0, f"orphaned content items: {stats}"
        # 7 de aprendizaje + 4 de certificacion (track08 CLF-C02, track09 PCEP,
        # track10 SAA-C03, track11 AIF-C01). Se cuenta contra tracks.json en vez
        # de contra un literal: el numero anterior (8) se quedo viejo en cuanto
        # aterrizaron los tracks 09-11 y tumbo la job de CI.
        assert stats["tracks"] == _declared_track_count()
        assert stats["questions"] >= 1253
        assert stats["glossary"] >= 70

    @pytest.mark.asyncio
    async def test_real_corpus_is_idempotent(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        first = await load_content(db_session)
        count_after_first = await db_session.scalar(select(func.count(Question.id)))
        second = await load_content(db_session)
        count_after_second = await db_session.scalar(select(func.count(Question.id)))

        assert first == second
        assert count_after_first == count_after_second

    @pytest.mark.asyncio
    async def test_every_shipped_question_cites_a_source(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Red line 2: every question ships with a source."""
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        missing = await db_session.scalar(
            select(func.count(Question.id)).where(
                (Question.source.is_(None)) | (Question.source == "")
            )
        )
        assert missing == 0

    @pytest.mark.asyncio
    async def test_every_shipped_question_is_bilingual(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Red line 3: nothing ships in a single language."""
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        missing = await db_session.scalar(
            select(func.count(Question.id)).where(
                (Question.question_es.is_(None))
                | (Question.question_es == "")
                | (Question.question_en.is_(None))
                | (Question.question_en == "")
            )
        )
        assert missing == 0

    @pytest.mark.asyncio
    async def test_track_totals_match_the_question_table(
        self, db_session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CONTENT_DIR", raising=False)
        await load_content(db_session)

        tracks = (await db_session.execute(select(Track))).scalars().all()
        total_denormalized = sum(t.total_questions for t in tracks)
        total_rows = await db_session.scalar(select(func.count(Question.id)))
        assert total_denormalized == total_rows


# ── module entrypoint ─────────────────────────────────────────────────────────


class TestMain:
    """`main()` es lo que corre `scripts/start.sh` en produccion.

    Hasta el 2026-09-20 llamaba a `init_db()` —o sea `Base.metadata.create_all`—
    sin mirar el entorno, y eso tumbo produccion: `create_all` intenta crear
    **toda** tabla registrada en `Base.metadata`, incluidas las cuatro de
    `models/payment.py` que ninguna migracion crea a proposito. La FK de
    `stripe_customers.user_id` no se pudo crear, `set -e` mato el contenedor, y
    la API devolvio 502 durante horas.

    El test que habia solo comprobaba la rama de development (`init` llamado), y
    cuando se anadio la guarda se quedo en rojo sin que nadie lo viera. Aqui se
    comprueban **las dos ramas**, porque la que importa es la otra: que fuera de
    development el esquema NO se toque.
    """

    @staticmethod
    def _parchear_sesion(monkeypatch, db_session, llamadas: dict) -> None:
        async def fake_init_db() -> None:
            llamadas["init"] = True

        class _SessionCtx:
            async def __aenter__(self):
                return db_session

            async def __aexit__(self, *exc: object) -> bool:
                return False

        monkeypatch.setattr(content_loader, "init_db", fake_init_db)
        monkeypatch.setattr(content_loader, "AsyncSessionLocal", lambda: _SessionCtx())

    @pytest.mark.asyncio
    async def test_main_initialises_db_in_development(
        self, db_session, tree: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """En local no hay Alembic corriendo antes, asi que aqui si crea."""
        llamadas: dict[str, bool] = {"init": False}
        self._parchear_sesion(monkeypatch, db_session, llamadas)
        monkeypatch.setattr(content_loader.settings, "ENVIRONMENT", "development")

        await content_loader.main()

        assert llamadas["init"] is True
        assert "Content loaded:" in capsys.readouterr().out

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entorno", ["production", "staging", "test"])
    async def test_main_no_toca_el_esquema_fuera_de_development(
        self, db_session, tree: Path, monkeypatch: pytest.MonkeyPatch, capsys, entorno
    ) -> None:
        """La guarda del 502: el esquema es de Alembic, no de `create_all`.

        Si esto se pone en verde volviendo a llamar a `init_db()`, produccion se
        cae en el siguiente reinicio del contenedor, no en el deploy — que es
        justo por lo que costo horas encontrarlo.
        """
        llamadas: dict[str, bool] = {"init": False}
        self._parchear_sesion(monkeypatch, db_session, llamadas)
        monkeypatch.setattr(content_loader.settings, "ENVIRONMENT", entorno)

        await content_loader.main()

        assert llamadas["init"] is False, (
            f"`main()` llamo a init_db() con ENVIRONMENT={entorno!r}. Eso es "
            f"`create_all` sobre un esquema de Alembic: intenta crear las tablas "
            f"de payment.py que ninguna migracion crea, la FK de "
            f"stripe_customers revienta y el contenedor muere en bucle"
        )
        assert "Content loaded:" in capsys.readouterr().out, (
            "el contenido tiene que cargarse igual; lo unico que cambia es que no "
            "se toca el esquema"
        )
