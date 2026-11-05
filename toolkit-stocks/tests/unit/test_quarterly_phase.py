'''run_statements quarterly branch: target selection, stats, stamping.
DB and network faked out.'''
from types import SimpleNamespace

import pytest

import pipeline.statements as ps
from pipeline.statements import run_statements


class FakeCtx:
	def __init__(self, symbols):
		self.args = SimpleNamespace(force=False, full=False)
		self.symbols = symbols
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)}
		self.yfs = None


class FakeYfs:
	'''map_symbols mirrors the threaded fetch shape; payload = one record.'''

	def map_symbols(self, fn, symbols, label):
		return {s: fn(s) for s in symbols}

	@staticmethod
	def statements_payload(symbol, kind, period):
		return [{"report_date": "2026-09-30", "total_revenue": 100.0}]


class FakeFlusher:
	instances = []

	def __init__(self, table, flush_size=None, conflict_keys=None, null_tolerance=None):
		self.table = table
		self.conflict_keys = conflict_keys
		self.rows = []
		FakeFlusher.instances.append(self)

	def add(self, rows):
		self.rows.extend(rows)

	def finish(self):
		return len(self.rows)


@pytest.fixture(autouse=True)
def _fakes(monkeypatch):
	FakeFlusher.instances.clear()
	touched = []
	fake_sql = SimpleNamespace(
		quarterly_fetch_ids=set(),
		stamped_ids=set(),
		fresh_ids=set(),
	)
	monkeypatch.setattr(ps, "get_quarterly_fetch_ids", lambda tables, ids, bucket: fake_sql.quarterly_fetch_ids)
	monkeypatch.setattr(ps, "get_stamped_stock_ids", lambda table, ids: fake_sql.stamped_ids)
	monkeypatch.setattr(ps, "get_fresh_stock_ids", lambda table, ids, cutoff: fake_sql.fresh_ids)
	monkeypatch.setattr(ps, "touch_statement_rows", lambda table, ids: touched.extend(ids))
	monkeypatch.setattr(ps, "RowFlusher", FakeFlusher)
	yield SimpleNamespace(touched=touched, sql=fake_sql)


def _run(symbols=("AAPL", "MSFT", "NVDA"), **kw):
	ctx = FakeCtx(list(symbols))
	ctx.yfs = FakeYfs()
	return run_statements(ctx, "income_statement", "stock_statement_income", 0.4, **kw), ctx


def test_quarterly_fetches_only_stale_and_not_suppressed(_fakes):
	sids = {2, 3}	# MSFT, NVDA stale per calendar-aware query
	_fakes.sql.quarterly_fetch_ids = sids
	_fakes.sql.stamped_ids = {1, 2, 3}	# everyone stamped -> no legacy refetch

	stats, ctx = _run(period_type="quarterly")

	assert stats["phase"] == "income_statement_quarterly"
	assert stats["symbols_ok"] == 2
	assert stats["skipped_fresh"] == 1
	flusher = FakeFlusher.instances[0]
	assert flusher.table == "stock_statement_income"
	# quarterly rows carry Q-period mapping via build_statement_rows
	assert all(r["period"] == "Q3" for r in flusher.rows)
	# fetched symbols stamped; suppressed symbol bumped to restart its clock
	assert _fakes.touched == [2, 3, 1]


def test_quarterly_legacy_null_stamp_refetched(_fakes):
	# MSFT within window (not in fetch_ids) but unstamped rows -> refetch once
	_fakes.sql.quarterly_fetch_ids = set()
	_fakes.sql.stamped_ids = {1, 3}

	stats, ctx = _run(period_type="quarterly")

	assert stats["symbols_ok"] == 1
	assert stats["skipped_fresh"] == 2


def test_quarterly_no_name_error_without_fetch_ids(_fakes):
	# nothing stale -> empty needed; regression guard for the fresh-bump tail
	_fakes.sql.quarterly_fetch_ids = set()
	_fakes.sql.stamped_ids = {1, 2, 3}

	stats, ctx = _run(period_type="quarterly")

	assert stats["symbols_ok"] == 0
	assert stats["skipped_fresh"] == 3
	assert FakeFlusher.instances[0].rows == []


def test_quarterly_force_fetches_all(_fakes):
	ctx = FakeCtx(["AAPL"])
	ctx.yfs = FakeYfs()
	ctx.args = SimpleNamespace(force=True, full=False)
	stats = run_statements(ctx, "income_statement", "stock_statement_income", 0.4, period_type="quarterly")
	assert stats["symbols_ok"] == 1
	assert stats.get("skipped_fresh", 0) == 0


def test_annual_phase_name_unchanged(_fakes):
	_fakes.sql.stamped_ids = {1, 2, 3}
	stats, ctx = _run(period_type="annual")
	assert stats["phase"] == "income_statement"
