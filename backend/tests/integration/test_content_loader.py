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

from app.models.content import GlossaryTerm, Module, Question, Skill, Track
from app.services import content_loader
from app.services.content_loader import _content_root, load_content

# ── helpers ───────────────────────────────────────────────────────────────────


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
        assert stats["tracks"] == 8  # 7 de aprendizaje + track08 (AWS CLF-C02, tarea 10.2)
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
    @pytest.mark.asyncio
    async def test_main_initialises_db_and_reports_stats(
        self, db_session, tree: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        called: dict[str, bool] = {"init": False}

        async def fake_init_db() -> None:
            called["init"] = True

        class _SessionCtx:
            async def __aenter__(self):
                return db_session

            async def __aexit__(self, *exc: object) -> bool:
                return False

        monkeypatch.setattr(content_loader, "init_db", fake_init_db)
        monkeypatch.setattr(content_loader, "AsyncSessionLocal", lambda: _SessionCtx())

        await content_loader.main()

        assert called["init"] is True
        assert "Content loaded:" in capsys.readouterr().out
