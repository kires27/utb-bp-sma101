'''Per-phase gating in pipeline.market_data/context: --fetch prices/dividends/splits
must touch only its own table and only fetch its own dataset.'''
from pipeline import market_data as md
from pipeline import context as ctx_mod
from lib.functions.stats import new_phase


class Args:
	def __init__(self, prices=False, splits=False, dividends=False, metrics=False, fa=False, force=False):
		self.prices = prices
		self.splits = splits
		self.dividends = dividends
		self.metrics = metrics
		self.fa = fa
		self.force = force


class FakeCtx:
	def __init__(self, args, us=(), intl=()):
		self.args = args
		self.us_symbols = list(us)
		self.intl_symbols = list(intl)
		self.stock_ids = {s: i + 1 for i, s in enumerate(list(us) + list(intl))}
		self.ds = None
		self.yfs = None
		self.market_data_cache = None


def test_want_reads_phase_flags():
	ctx = FakeCtx(Args(prices=True, dividends=True))
	assert md._want(ctx) == {"prices": True, "splits": False, "dividends": True}


def test_market_data_cache_fetches_only_requested(monkeypatch):
	calls = []

	class FakeDS:
		def prices(self, symbols):
			calls.append("prices")
			return {}

		def shares_outstanding(self, symbols):
			calls.append("shares")
			return {}

		def dividends(self, symbols):
			calls.append("dividends")
			return {}

		def splits(self, symbols):
			calls.append("splits")
			return {}

	ctx = FakeCtx(Args(dividends=True), us=["AAA"])
	ctx.ds = FakeDS()

	md_data = ctx_mod.market_data(ctx)
	assert calls == ["dividends"]
	assert md_data["splits"] == {}


def test_market_data_cache_metrics_needs_prices_shares_dividends(monkeypatch):
	calls = []

	class FakeDS:
		def prices(self, symbols):
			calls.append("prices")
			return {}

		def shares_outstanding(self, symbols):
			calls.append("shares")
			return {}

		def dividends(self, symbols):
			calls.append("dividends")
			return {}

		def splits(self, symbols):
			calls.append("splits")
			return {}

	ctx = FakeCtx(Args(metrics=True), us=["AAA"])
	ctx.ds = FakeDS()
	ctx_mod.market_data(ctx)

	assert calls == ["prices", "shares", "dividends"]


def test_run_us_uses_shared_cache_only(monkeypatch):
	'''run_us must not re-fetch: ds methods absent -> any call would raise.'''
	class BrokenDS:
		def __getattr__(self, name):
			raise AssertionError(f"run_us re-fetched ds.{name}")

	ctx = FakeCtx(Args(dividends=True, force=True), us=["AAA"])
	ctx.ds = BrokenDS()
	ctx.market_data_cache = {
		"prices": {},
		"shares": {},
		"dividends": {"AAA": [{"date": "2024-02-01", "amount": 0.25}]},
		"splits": {},
	}
	writes = []
	monkeypatch.setattr(md, "insert_data_statement", lambda rows, table, **k: writes.append(table) or len(rows))
	monkeypatch.setattr(md, "get_latest_dates", lambda *a, **k: {})

	stats = new_phase("market_data", 1)
	md.run_us(ctx, stats)

	assert writes == ["stock_dividend"]
	assert stats["symbols_ok"] == 1
	assert stats["rows_written"] == 1


def test_run_us_skips_unrequested_tables(monkeypatch):
	writes = []

	ctx = FakeCtx(Args(dividends=True, force=True), us=["AAA"])
	ctx.market_data_cache = {
		"prices": {"AAA": [{"date": "2024-01-02", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}]},
		"shares": {},
		"dividends": {},
		"splits": {},
	}
	monkeypatch.setattr(md, "insert_data_statement", lambda rows, table, **k: writes.append(table) or len(rows))
	monkeypatch.setattr(md, "get_latest_dates", lambda *a, **k: {})

	stats = new_phase("market_data", 1)
	md.run_us(ctx, stats)

	assert writes == []


def test_run_intl_writes_only_requested_tables(monkeypatch):
	writes = []

	class FakeYFS:
		def map_symbols(self, fn, targets, label):
			return {
				sym: {
					"stock_id": i + 1,
					"latest": None,
					"price_rows": [{"date": "2024-01-02", "close": 1}],
					"div_events": [{"date": "2024-01-02", "amount": 0.5}],
					"split_events": [],
				}
				for i, sym in enumerate(targets)
			}

	ctx = FakeCtx(Args(dividends=True, force=True), intl=["ASML"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "insert_data_statement", lambda rows, table, **k: writes.append(table) or 1)

	stats = new_phase("market_data", 1)
	md.run_intl(ctx, stats)

	assert writes == ["stock_dividend"]
	assert stats["rows_written"] == 1


def test_run_intl_all_flags_writes_all_tables(monkeypatch):
	writes = []

	class FakeYFS:
		def map_symbols(self, fn, targets, label):
			return {
				sym: {
					"stock_id": i + 1,
					"latest": None,
					"price_rows": [],
					"div_events": [],
					"split_events": [],
				}
				for i, sym in enumerate(targets)
			}

	ctx = FakeCtx(Args(prices=True, splits=True, dividends=True, force=True), intl=["ASML"])
	ctx.yfs = FakeYFS()
	monkeypatch.setattr(md, "insert_data_statement", lambda rows, table, **k: writes.append(table) or 1)

	stats = new_phase("market_data", 1)
	md.run_intl(ctx, stats)

	assert writes == ["stock_historical_price", "stock_dividend", "stock_split"]


def test_dividends_failover_yf_primary():
	'''Dividends: yfinance primary (full precision), DefeatBeta fallback.'''

	class YfSource:
		def history_payload(self, symbol, period="max"):
			return {"div_events": [{"date": "2024-02-01", "amount": 0.0033}]}

	class DbSource:
		def __init__(self):
			self.called = False

		def dividends(self, symbols):
			self.called = True
			return {}

	yf, db = YfSource(), DbSource()
	fo = ctx_mod.FailoverSource(db, yf)
	out = fo.dividends(["AAA"])

	assert out == {"AAA": [{"date": "2024-02-01", "amount": 0.0033}]}
	assert db.called is False


def test_dividends_breakdown_counts_by_serving_source(capsys):
	'''yf-served symbol must be counted under YFinanceSource, not DefeatBetaSource.'''

	class YfSource:
		def history_payload(self, symbol, period="max"):
			return {"div_events": [{"date": "2024-02-01", "amount": 0.0033}]}

	class DbSource:
		def dividends(self, symbols):
			return {}

	fo = ctx_mod.FailoverSource(DbSource(), YfSource())
	fo.dividends(["AAA"])

	out = capsys.readouterr().out
	assert "dividends served by YfSource: 1" in out
	assert "DbSource: 1" not in out


def test_dividends_failover_falls_back_to_defeatbeta():
	class YfSource:
		def history_payload(self, symbol, period="max"):
			return None

	class DbSource:
		def dividends(self, symbols):
			return {"AAA": [{"date": "2024-02-01", "amount": 0.25}]}

	fo = ctx_mod.FailoverSource(DbSource(), YfSource())
	assert fo.dividends(["AAA"]) == {"AAA": [{"date": "2024-02-01", "amount": 0.25}]}


def test_prices_failover_defeatbeta_primary():
	class YfSource:
		def __init__(self):
			self.called = False

		def history_payload(self, symbol, period="max"):
			self.called = True
			return None

	class DbSource:
		def prices(self, symbols):
			return {"AAA": [{"date": "2024-01-02", "close": 1}]}

	yf = YfSource()
	fo = ctx_mod.FailoverSource(DbSource(), yf)
	assert fo.prices(["AAA"]) == {"AAA": [{"date": "2024-01-02", "close": 1}]}
	assert yf.called is False
