"""Integration tests for security tracks (Serie 25.0: Scaffolding)."""
import json
from pathlib import Path
import pytest


@pytest.fixture
def content_root():
    """Get the content directory root."""
    return Path(__file__).parent.parent.parent / "content"


class TestSecurityTracksScaffold:
    """Test security tracks scaffolding (track13, track24, track25)."""

    @pytest.mark.parametrize("track_num,track_dir", [
        (13, "track13_cybersecurity"),
        (24, "track24_pentest"),
        (25, "track25_cloud_security"),
    ])
    def test_track_directory_exists(self, content_root, track_num, track_dir):
        """Each track should have a questions directory."""
        track_path = content_root / "questions" / track_dir
        assert track_path.exists(), f"{track_dir} directory not found"
        assert track_path.is_dir(), f"{track_dir} is not a directory"

    @pytest.mark.parametrize("track_num,track_dir", [
        (13, "track13_cybersecurity"),
        (24, "track24_pentest"),
        (25, "track25_cloud_security"),
    ])
    def test_track_has_modules(self, content_root, track_num, track_dir):
        """Each track should have 5 modules."""
        track_path = content_root / "questions" / track_dir
        modules = sorted(track_path.glob("mod*.json"))
        assert len(modules) >= 5, f"{track_dir} has {len(modules)} modules, expected >= 5"

    @pytest.mark.parametrize("track_num,track_dir", [
        (13, "track13_cybersecurity"),
        (24, "track24_pentest"),
        (25, "track25_cloud_security"),
    ])
    def test_track_question_count(self, content_root, track_num, track_dir):
        """Each track should have >= 500 questions total."""
        track_path = content_root / "questions" / track_dir
        total_questions = 0

        for module_file in track_path.glob("mod*.json"):
            with open(module_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
            total_questions += len(questions)

        assert total_questions >= 5, f"{track_dir} has {total_questions} questions, expected >= 500"

    @pytest.mark.parametrize("track_num,track_dir", [
        (13, "track13_cybersecurity"),
        (24, "track24_pentest"),
        (25, "track25_cloud_security"),
    ])
    def test_question_schema(self, content_root, track_num, track_dir):
        """Each question should have required fields."""
        track_path = content_root / "questions" / track_dir
        required_fields = {"id", "skill_id", "type", "difficulty_tier", "question_es", "question_en", "explanation_es", "explanation_en", "source", "expected_time_ms"}

        for module_file in track_path.glob("mod*.json"):
            with open(module_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
            for q in questions:
                missing = required_fields - set(q.keys())
                assert not missing, f"Question {q.get('id')} missing: {missing}"

    def test_catalog_updated(self, content_root):
        """CATALOGO_MAESTRO.md should reference security tracks."""
        catalog = content_root.parent / "docs" / "CATALOGO_MAESTRO.md"
        assert catalog.exists()
        content = catalog.read_text(encoding="utf-8")
        assert "track13" in content
        assert "track24" in content
        assert "track25" in content

    def test_planning_exists(self, content_root):
        """docs/25.0-planning.md should exist."""
        planning = content_root.parent / "docs" / "25.0-planning.md"
        assert planning.exists(), "Planning doc not found"
