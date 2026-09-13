"""Unit tests for the BKT vs DKT public-dataset benchmark (task 11.3).

No network access and no real dataset download in any test here — a tiny
in-memory fixture, shaped exactly like the real synthetic-5 files (tab-
separated info file, comma-separated 0/1 CSV rows), exercises parsing,
splitting, BKT grid-fitting, and the metric helpers. DKT training tests run
only when torch is installed (it is optional project-wide — see
docs/DECISIONS.md #4) and are skipped otherwise rather than failing CI.
"""

from __future__ import annotations

import math
import urllib.error
from pathlib import Path

import pytest

from app.ml import benchmark_kt as bk
from app.services.engine.bkt import SkillParams

# ── Fixture: a tiny synthetic-5-shaped dataset (2 skills, 4 questions, 6 students) ──

INFO_TEXT = (
    "0.5\t0.49\t0\t1.0\n"
    "0.5\t0.49\t1\t1.0\n"
    "0.5\t0.49\t0\t1.0\n"
    "0.5\t0.49\t1\t1.0"
)

# Students 0-2 skew correct, students 3-5 skew incorrect: a learnable but
# noisy signal, so AUC is well-defined (not NaN / not trivially 1.0).
CSV_TEXT = (
    "1,1,1,1\n"
    "1,0,1,1\n"
    "0,1,1,1\n"
    "0,0,0,1\n"
    "1,0,0,0\n"
    "0,0,1,0"
)


class TestParsing:
    def test_parse_concept_ids(self) -> None:
        assert bk.parse_concept_ids(INFO_TEXT) == [0, 1, 0, 1]

    def test_parse_concept_ids_ignores_blank_lines(self) -> None:
        assert bk.parse_concept_ids(INFO_TEXT + "\n\n") == [0, 1, 0, 1]

    def test_load_synthetic5_shapes(self) -> None:
        sequences, skill_ids = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        assert skill_ids == ["0", "1"]
        assert len(sequences) == 6
        assert all(len(seq) == 4 for seq in sequences)
        assert sequences[0] == [(0, True), (1, True), (0, True), (1, True)]

    def test_load_synthetic5_mismatched_columns_raises(self) -> None:
        bad_csv = "1,1,1\n"  # 3 columns, but info describes 4 questions
        with pytest.raises(ValueError, match="responses"):
            bk.load_synthetic5(bad_csv, INFO_TEXT)


class TestSplit:
    def test_temporal_split_default_frac(self) -> None:
        sequences = [[(0, True)] for _ in range(10)]
        train, test = bk.temporal_split(sequences, train_frac=0.8)
        assert len(train) == 8
        assert len(test) == 2

    def test_temporal_split_preserves_order_no_shuffle(self) -> None:
        sequences = [[(i, True)] for i in range(5)]
        train, test = bk.temporal_split(sequences, train_frac=0.6)
        assert train == sequences[:3]
        assert test == sequences[3:]

    def test_temporal_split_always_keeps_at_least_one_train(self) -> None:
        sequences = [[(0, True)]]
        train, test = bk.temporal_split(sequences, train_frac=0.8)
        assert len(train) == 1
        assert test == []


class TestMetrics:
    def test_accuracy_perfect(self) -> None:
        assert bk._accuracy([0.9, 0.1], [1.0, 0.0]) == 1.0

    def test_accuracy_all_wrong(self) -> None:
        assert bk._accuracy([0.1, 0.9], [1.0, 0.0]) == 0.0

    def test_accuracy_empty_is_nan(self) -> None:
        assert math.isnan(bk._accuracy([], []))

    def test_safe_auc_matches_sklearn(self) -> None:
        from sklearn.metrics import roc_auc_score

        preds = [0.9, 0.2, 0.6, 0.4]
        labels = [1.0, 0.0, 1.0, 0.0]
        assert bk._safe_auc(preds, labels) == pytest.approx(roc_auc_score(labels, preds))

    def test_safe_auc_single_class_is_nan(self) -> None:
        assert math.isnan(bk._safe_auc([0.5, 0.6], [1.0, 1.0]))

    def test_safe_auc_empty_is_nan(self) -> None:
        assert math.isnan(bk._safe_auc([], []))


class TestBKT:
    def test_predict_stepahead_lengths(self) -> None:
        sequences, skill_ids = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        preds, labels = bk.bkt_predict_stepahead(SkillParams(), sequences, skill_ids)
        # 4-step sequence -> 3 step-ahead predictions; 6 students.
        assert len(preds) == len(labels) == 6 * 3

    def test_predict_stepahead_predictions_in_unit_interval(self) -> None:
        sequences, skill_ids = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        preds, _ = bk.bkt_predict_stepahead(SkillParams(), sequences, skill_ids)
        assert all(0.0 <= p <= 1.0 for p in preds)

    def test_fit_bkt_grid_returns_valid_params_and_finite_auc(self) -> None:
        sequences, skill_ids = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        params, auc = bk.fit_bkt_grid(sequences, skill_ids)
        assert isinstance(params, SkillParams)
        assert not math.isnan(auc)
        assert 0.0 <= auc <= 1.0

    def test_fit_bkt_grid_only_sees_the_sequences_it_was_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression guard for the honesty rule: the grid search must only
        ever be shown the train split it was called with, never a separate
        held-out set — fitting on test data would invalidate the benchmark.
        """
        sequences, skill_ids = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        train, test = bk.temporal_split(sequences, train_frac=0.5)
        assert train and test and train != test

        seen: list[list[list[tuple[int, bool]]]] = []
        original = bk.bkt_predict_stepahead

        def spy(
            params: SkillParams,
            seqs: list[list[tuple[int, bool]]],
            sids: list[str],
        ) -> tuple[list[float], list[float]]:
            seen.append(seqs)
            return original(params, seqs, sids)

        monkeypatch.setattr(bk, "bkt_predict_stepahead", spy)
        bk.fit_bkt_grid(train, skill_ids)

        assert seen  # grid search actually ran
        for seqs in seen:
            assert seqs == train
            assert seqs != test


class TestDatasetCaching:
    def test_ensure_synthetic5_skips_download_when_cached(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        csv_path = tmp_path / "naive_c5_q50_s4000_v0.csv"
        info_path = tmp_path / "naive_c5_q50_s4000_v0_info.txt"
        csv_path.write_text(CSV_TEXT)
        info_path.write_text(INFO_TEXT)

        def fail_if_called(url: str, dest: Path, timeout: float = 30.0) -> None:
            raise AssertionError(f"must not download when already cached: {url}")

        monkeypatch.setattr(bk, "_download", fail_if_called)
        result_csv, result_info = bk.ensure_synthetic5(tmp_path)
        assert result_csv == csv_path
        assert result_info == info_path

    def test_ensure_synthetic5_downloads_missing_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        downloaded: list[str] = []

        def fake_download(url: str, dest: Path, timeout: float = 30.0) -> None:
            downloaded.append(url)
            dest.write_text(CSV_TEXT if dest.suffix == ".csv" else INFO_TEXT)

        monkeypatch.setattr(bk, "_download", fake_download)
        csv_path, info_path = bk.ensure_synthetic5(tmp_path)
        assert downloaded == [bk.SYNTHETIC5_CSV_URL, bk.SYNTHETIC5_INFO_URL]
        assert csv_path.exists()
        assert info_path.exists()

    def test_download_raises_runtimeerror_on_http_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def raise_http_error(req: object, timeout: float = 30.0) -> None:
            raise urllib.error.HTTPError("http://example.test", 404, "Not Found", None, None)  # type: ignore[arg-type]

        monkeypatch.setattr(bk.urllib.request, "urlopen", raise_http_error)
        with pytest.raises(RuntimeError, match="HTTP 404"):
            bk._download("http://example.test/data.csv", tmp_path / "out.csv")

    def test_download_raises_runtimeerror_on_network_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def raise_url_error(req: object, timeout: float = 30.0) -> None:
            raise urllib.error.URLError("no route to host")

        monkeypatch.setattr(bk.urllib.request, "urlopen", raise_url_error)
        with pytest.raises(RuntimeError, match="Network error"):
            bk._download("http://example.test/data.csv", tmp_path / "out.csv")


class TestAssistmentsProbeDoesNotFabricateData:
    def test_probe_reports_not_included_without_network(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Even if every candidate URL were reachable, the probe must never
        claim ASSISTments 2009 was included in the benchmark — it only
        reports reachability, never synthesizes a substitute dataset."""

        def fake_urlopen(req: object, timeout: float = 15.0) -> object:
            raise urllib.error.HTTPError("http://example.test", 404, "Not Found", None, None)  # type: ignore[arg-type]

        monkeypatch.setattr(bk.urllib.request, "urlopen", fake_urlopen)
        report = bk.probe_assistments_2009(timeout=1.0)
        assert report["included_in_benchmark"] is False
        assert report["attempted"] is True
        assert len(report["candidates_probed"]) == len(bk.ASSISTMENTS_2009_CANDIDATES)


_TORCH_AVAILABLE = bk._TORCH_AVAILABLE


@pytest.mark.skipif(
    not _TORCH_AVAILABLE, reason="torch is optional project-wide (docs/DECISIONS.md #4)"
)
class TestDKT:
    def test_run_dkt_returns_stepahead_predictions_for_test_split_only(self) -> None:
        sequences, _ = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        train, test = bk.temporal_split(sequences, train_frac=0.67)
        preds, labels = bk.run_dkt(train, test, n_skills=2, hidden=4, epochs=1)
        expected_n = sum(len(seq) - 1 for seq in test)
        assert len(preds) == len(labels) == expected_n
        assert all(0.0 <= p <= 1.0 for p in preds)

    def test_run_dkt_is_reproducible_given_fixed_seed(self) -> None:
        sequences, _ = bk.load_synthetic5(CSV_TEXT, INFO_TEXT)
        train, test = bk.temporal_split(sequences, train_frac=0.67)
        preds_a, _ = bk.run_dkt(train, test, n_skills=2, hidden=4, epochs=1, seed=7)
        preds_b, _ = bk.run_dkt(train, test, n_skills=2, hidden=4, epochs=1, seed=7)
        assert preds_a == pytest.approx(preds_b)
