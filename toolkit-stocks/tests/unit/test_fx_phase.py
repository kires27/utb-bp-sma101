'''run_fx (fx phase): per-pair fetch -> fx_rate rows, counts, failure paths.
DB and network faked out (no datasource mocking - YFinanceSource patched).'''
import pytest

import pipeline.fx as pfx
from pipeline.fx import build_fx_rows, run_fx


class FakeYfs:
	'''fx_history stub: canned rates per ccy, raises for configured failures.'''

	def __init__(self, rates=None, failing=()):
		self.rates = rates or {}
		self.failing = set(failing)
		self.periods = []

	def fx_history(self, ccy, period="max"):
		self.periods.append((ccy, period))
		if ccy in self.failing:
			raise RuntimeError("fx fetch boom")
		return self.rates.get(ccy)  # None -> empty-history warning path


class FakeFlusher:
	def __init__(self, table, flush_size=1000, conflict_keys=None, null_tolerance=1):
		self.table = table
		self.flush_size = flush_size
		self.conflict_keys = conflict_keys
		self.rows = []

	def add(self, rows):
		self.rows.extend(rows)

	def finish(self):
		return len(self.rows)


def _patch(monkeypatch, rates=None, failing=()):
	yfs = FakeYfs(rates=rates, failing=failing)
	flusher = FakeFlusher("fx_rate", conflict_keys=["from", "to", "rate_date"])
	monkeypatch.setattr(pfx, "YFinanceSource", lambda: yfs)
	monkeypatch.setattr(pfx, "RowFlusher", lambda table, **kw: flusher)
	return yfs, flusher


def test_build_fx_rows_shape():
	# sorted oldest-first, from=USD base, one row per date
	rows = build_fx_rows("JPY", {"2026-11-05": 158.4, "2026-11-04": 157.9})
	assert rows == [
		{"from": "USD", "to": "JPY", "rate_date": "2026-11-04", "rate": 157.9},
		{"from": "USD", "to": "JPY", "rate_date": "2026-11-05", "rate": 158.4},
	]


def test_build_fx_rows_rate_rounded_to_6dp():
	# full double precision in -> 6 decimal places out (KRW-scale stays exact
	# enough, JPY-scale trims trailing noise)
	rows = build_fx_rows("KRW", {"2026-11-05": 0.0007234123456})
	assert rows[0]["rate"] == 0.000723
	rows = build_fx_rows("JPY", {"2026-11-05": 157.9123456789})
	assert rows[0]["rate"] == 157.912346


def test_build_fx_rows_empty():
	assert build_fx_rows("JPY", {}) == []


def test_run_fx_counts_and_writes(monkeypatch):
	yfs, flusher = _patch(monkeypatch, rates={
		"JPY": {"2026-11-05": 158.4},
		"EUR": {"2026-11-05": 0.897, "2026-11-04": 0.895},
	})
	stats = run_fx(currencies=["JPY", "EUR"])

	assert stats["symbols_ok"] == 2
	assert stats["failed_symbols"] == []
	assert stats["rows_written"] == 3
	assert flusher.table == "fx_rate"
	assert flusher.conflict_keys == ["from", "to", "rate_date"]


def test_run_fx_refresh_uses_1y(monkeypatch):
	yfs, _ = _patch(monkeypatch, rates={"JPY": {"2026-11-05": 158.4}})
	run_fx(currencies=["JPY"])
	assert yfs.periods == [("JPY", "1y")]


def test_run_fx_force_backfills_max(monkeypatch):
	yfs, _ = _patch(monkeypatch, rates={"JPY": {"2026-11-05": 158.4}})
	run_fx(force=True, currencies=["JPY"])
	assert yfs.periods == [("JPY", "max")]


def test_pair_failure_continues(monkeypatch):
	# one pair raising must not abort the run: EUR still written
	yfs, flusher = _patch(monkeypatch, rates={"EUR": {"2026-11-05": 0.897}}, failing=("JPY",))
	stats = run_fx(currencies=["JPY", "EUR"])

	assert stats["symbols_ok"] == 1
	assert stats["failed_symbols"] == ["JPY"]
	assert [r["to"] for r in flusher.rows] == ["EUR"]


def test_empty_history_counted_failed(monkeypatch):
	# {CCY}=X series can come back empty -> warning + failed count, no rows
	yfs, flusher = _patch(monkeypatch, rates={"JPY": None, "EUR": {"2026-11-05": 0.897}})
	stats = run_fx(currencies=["JPY", "EUR"])

	assert stats["symbols_ok"] == 1
	assert stats["failed_symbols"] == ["JPY"]
	assert flusher.rows and all(r["to"] == "EUR" for r in flusher.rows)
