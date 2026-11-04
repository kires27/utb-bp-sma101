'''run_quality_score (fqs phase): per-symbol score upsert, stats, failure path.
DB and network faked out (no domain mocking - scoring transform is patched).'''
from types import SimpleNamespace

import pytest

import pipeline.quality_score as pqs
from pipeline.quality_score import run_quality_score


class FakeCtx:
	def __init__(self, symbols):
		self.args = SimpleNamespace(force=False, full=False)
		self.symbols = symbols
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)}
		self.yfs = None


def _fqs(fiscal_date, score):
	return {
		"data": {"stock_id": 1, "fiscal_date": fiscal_date, "period": "TTM",
			"maintenance_update": "2026-11-02T00:00:00Z",
			"quality_score": score, "median_comparison": None},
		"fiscal_date": fiscal_date,
		"period": "TTM",
	}


@pytest.fixture
def ups(monkeypatch):
	inserted = []
	monkeypatch.setattr(pqs, "insert_data_statement",
		lambda data, table, update_condition=None: inserted.append((update_condition["stock_id"], data["quality_score"])) or 1)
	return inserted


def test_scores_upserted(ups, monkeypatch):
	monkeypatch.setattr(pqs, "build_quality_score", lambda stock_id: _fqs("2025-12-31", 62.5))
	stats = run_quality_score(FakeCtx(["AAPL", "MSFT"]))

	assert stats["symbols_ok"] == 2
	assert stats["failed_symbols"] == []
	assert ups == [(1, 62.5), (2, 62.5)]


def test_build_failure_counted(ups, monkeypatch):
	# build_quality_score returns {} on exception -> phase counts a fail, moves on
	monkeypatch.setattr(pqs, "build_quality_score", lambda stock_id: {})
	stats = run_quality_score(FakeCtx(["AAPL", "MSFT"]))

	assert stats["symbols_ok"] == 0
	assert stats["failed_symbols"] == ["AAPL", "MSFT"]
	assert ups == []


def test_update_condition_keys(ups, monkeypatch):
	captured = {}
	def fake_insert(data, table, update_condition=None):
		captured.update(update_condition)
		return 1
	monkeypatch.setattr(pqs, "insert_data_statement", fake_insert)
	monkeypatch.setattr(pqs, "build_quality_score", lambda stock_id: _fqs("2025-12-31", 10.0))
	run_quality_score(FakeCtx(["AAPL"]))

	assert captured == {"stock_id": 1, "fiscal_date": "2025-12-31", "period": "TTM"}
