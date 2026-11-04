'''Per-phase gating in pipeline.market_data: --fetch prices/dividends/splits
must touch only its own table and only fetch its own dataset.'''
import datetime as dt

import pytest

from pipeline import market_data as md
from lib.functions.stats import new_phase


class Args:
	def __init__(self, prices=False, splits=False, dividends=False, fa=False, force=False):
		self.prices = prices
		self.splits = splits
		self.dividends = dividends
		self.fa = fa
		self.force = force


class FakeCtx:
	def __init__(self, args, symbols=()):
		self.args = args
		self.symbols = list(symbols)
		self.stock_ids = {s: i + 1 for i, s in enumerate(self.symbols)}
		self.yfs = None


class FakeFlusher:
	'''Stand-in for RowFlusher: records table, rows and constructor args.'''
	instances = []

	def __init__(self, table, flush_size=None, conflict_keys=None, null_tolerance=None):
		self.table = table
		self.flush_size = flush_size
		self.conflict_keys = conflict_keys
		self.null_tolerance = null_tolerance
		self.rows = []
		FakeFlusher.instances.append(self)

	def add(self, rows):
		self.rows.extend(rows)

	def finish(self):
		return len(self.rows)


@pytest.fixture(autouse=True)
def _reset_flushers():
	FakeFlusher.instances.clear()
	yield


class FakeYFS:
	'''map_symbols bypasses the fetch fn and returns payloads directly.'''
	def map_symbols(self, fn, targets, label):
		return {sym: self.payload() for i, sym in enumerate(targets)}

	def payload(self):
		return {
			"stock_id": 1,
			"latest": None,
			"price_rows": [{"date": "2024-01-02", "close": 1.0}],
			"div_events": [{"date": "2024-01-02", "amount": 0.25}],
			"split_events": [],
		}


def test_want_reads_phase_flags():
	ctx = FakeCtx(Args(prices=True, dividends=True))
	assert md._want(ctx) == {"prices": True, "splits": False, "dividends": True}


def test_run_yf_writes_only_requested_tables(monkeypatch):
	ctx = FakeCtx(Args(dividends=True, force=True), symbols=["ASML"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "RowFlusher", FakeFlusher)

	stats = new_phase("market_data", 1)
	md.run_yf(ctx, stats)

	assert [f.table for f in FakeFlusher.instances] == ["stock_dividend"]
	assert stats["symbols_ok"] == 1
	assert stats["rows_written"] == 1


def test_run_yf_all_flags_writes_all_tables(monkeypatch):
	ctx = FakeCtx(Args(prices=True, dividends=True, splits=True, force=True), symbols=["ASML"])
	ctx.yfs = FakeYFS()
	fake = FakeYFS()

	def payload():
		p = fake.payload()
		p["split_events"] = [{"date": "2024-01-02", "factor": 2.0}]
		return p

	fake.payload = payload
	monkeypatch.setattr(md, "RowFlusher", FakeFlusher)

	stats = new_phase("market_data", 1)
	md.run_yf(ctx, stats)

	assert [f.table for f in FakeFlusher.instances] == ["stock_historical_price", "stock_dividend", "stock_split"]


def test_run_yf_incremental_skips_old_rows(monkeypatch):
	'''Incremental mode: rows older than the DB latest date are filtered out.'''
	class FakeYFS:
		def map_symbols(self, fn, targets, label):
			return {"ASML": {
				"stock_id": 1,
				"latest": dt.date(2024, 6, 1),
				"price_rows": [
					{"date": "2024-01-02", "close": 1.0},   # older than latest -> skipped
					{"date": "2024-06-15", "close": 2.0},   # newer -> kept
				],
				"div_events": [],
				"split_events": [],
			}}

	ctx = FakeCtx(Args(prices=True), symbols=["ASML"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "get_latest_dates", lambda table, ids: {ids[0]: dt.date(2024, 6, 1)})
	monkeypatch.setattr(md, "RowFlusher", FakeFlusher)

	stats = new_phase("market_data", 1)
	md.run_yf(ctx, stats)

	# only the 2024-06-15 row survives the incremental filter
	assert len(FakeFlusher.instances) == 1
	assert FakeFlusher.instances[0].table == "stock_historical_price"
	assert len(FakeFlusher.instances[0].rows) == 1
	assert stats["rows_written"] == 1


def test_run_yf_split_never_receives_conflict_keys(monkeypatch):
	'''Guardrail: stock_split must never be updated from Python (rebase trigger).'''
	class FakeYFS:
		def map_symbols(self, fn, targets, label):
			return {"ASML": {
				"stock_id": 1,
				"latest": None,
				"price_rows": [{"date": "2024-01-02", "close": 1.0}],
				"div_events": [],
				"split_events": [{"date": "2024-01-02", "factor": 2.0}],
			}}

	ctx = FakeCtx(Args(prices=True, splits=True, force=True), symbols=["ASML"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "RowFlusher", FakeFlusher)

	stats = new_phase("market_data", 1)
	md.run_yf(ctx, stats)

	by_table = {f.table: f for f in FakeFlusher.instances}
	# prices re-pull with DO UPDATE on force
	assert by_table["stock_historical_price"].conflict_keys == ["stock_id", "date"]
	# splits never receive conflict keys (rebase trigger guardrail)
	assert by_table["stock_split"].conflict_keys is None


def test_run_yf_fetch_failure_counts_failed_symbol(monkeypatch):
	class FakeYFS:
		def map_symbols(self, fn, targets, label):
			return {}  # nothing fetched

	ctx = FakeCtx(Args(prices=True, force=True), symbols=["AAA"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "RowFlusher", FakeFlusher)

	stats = new_phase("market_data", 1)
	md.run_yf(ctx, stats)

	assert stats["symbols_ok"] == 0
	assert stats["failed_symbols"] == ["AAA"]
