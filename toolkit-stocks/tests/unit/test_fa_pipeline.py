'''run_financial_analysis + insert_fa: quote-row-driven market data,
skip-on-missing, FX statement->trading ccy conversion end-to-end.
DB and network faked out (no datasource mocking - FA reads stock_quote;
dividend_yield is computed inside build_financial_analysis).'''
from datetime import date
from types import SimpleNamespace

import pytest

import pipeline.financial_analysis as pfa
import lib.transforms.financial_analysis as lta
from lib.functions.stats import new_phase
from pipeline.financial_analysis import run_financial_analysis, insert_fa
from lib.transforms.financial_analysis import make_fx_lookup


class FakeCtx:
	def __init__(self, symbols):
		self.args = SimpleNamespace(force=False, full=False)
		self.symbols = symbols
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)}
		self.symbol_meta = {}
		self.yfs = None


@pytest.fixture
def calls(monkeypatch):
	scored = []

	def fake_insert_and_score(ctx, symbol, quote, fx, stats):
		scored.append((symbol, quote))
		pfa.count_symbol(stats, True, rows=1)

	monkeypatch.setattr(pfa, "insert_fa", fake_insert_and_score)
	return scored


def _patch_quotes(monkeypatch, mapping):
	monkeypatch.setattr(pfa, "get_quotes", lambda ids: mapping)


def _no_fx(monkeypatch):
	# empty fx_rate table -> make_fx_lookup returns None (closure absent)
	monkeypatch.setattr(pfa, "get_fx_rates", lambda: {})


def test_all_quotes_present(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": 100.0, "market_cap": 2e12, "currency": "USD"},
	})
	_no_fx(monkeypatch)
	ctx = FakeCtx(["AAPL"])
	stats = run_financial_analysis(ctx)

	assert stats["symbols_ok"] == 1
	assert calls == [("AAPL", {"stock_price": 100.0, "market_cap": 2e12, "currency": "USD"})]


def test_missing_quote_row_skipped(monkeypatch, calls):
	_patch_quotes(monkeypatch, {})
	_no_fx(monkeypatch)
	ctx = FakeCtx(["AAPL", "MSFT"])
	stats = run_financial_analysis(ctx)

	assert stats["symbols_ok"] == 0
	assert stats["failed_symbols"] == ["AAPL", "MSFT"]
	assert calls == []


def test_null_market_cap_skipped_and_named(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": 100.0, "market_cap": None, "currency": "USD"},
		2: {"stock_price": 50.0, "market_cap": 1e12, "currency": "USD"},
	})
	_no_fx(monkeypatch)
	ctx = FakeCtx(["AAPL", "MSFT"])
	stats = run_financial_analysis(ctx)

	assert stats["failed_symbols"] == ["AAPL"]
	assert stats["symbols_ok"] == 1
	assert calls == [("MSFT", {"stock_price": 50.0, "market_cap": 1e12, "currency": "USD"})]


def test_null_price_skipped_and_named(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": None, "market_cap": 2e12, "currency": "USD"},
	})
	_no_fx(monkeypatch)
	ctx = FakeCtx(["AAPL"])
	stats = run_financial_analysis(ctx)

	assert stats["failed_symbols"] == ["AAPL"]
	assert calls == []


# --- FX conversion end-to-end (insert_fa -> build_financial_analysis) ---


def _patch_db(monkeypatch, balance, cash, income, dividends):
	'''Patch the three statement reads + dividend sum inside the transform.'''
	monkeypatch.setattr(lta, "get_statements_by_stock", lambda sid, table, limit=5: (
		balance if table == lta.dbt.balance_sheet else
		cash if table == lta.dbt.cash_flow else income
	))
	monkeypatch.setattr(lta, "get_ttm_dividends", lambda sid: dividends)


def _statements():
	'''All-USD statements (TTM single row + one older row for growth calcs).'''
	balance = [
		{"fiscal_date": date(2025, 12, 31), "net_tangible_assets": 500.0,
			"total_liabilities_net_minority_interest": 100.0,
			"stockholders_equity": 200.0, "current_assets": 400.0,
			"current_liabilities": 200.0, "total_debt": 300.0, "share_issued": 50.0,
			"retained_earnings": 100.0},
		{"fiscal_date": date(2024, 12, 31), "net_tangible_assets": 400.0,
			"total_liabilities_net_minority_interest": 90.0,
			"stockholders_equity": 180.0, "current_assets": 350.0,
			"current_liabilities": 180.0, "total_debt": 250.0, "share_issued": 50.0,
			"retained_earnings": 80.0},
	]
	cash = [
		{"fiscal_date": date(2025, 12, 31), "free_cash_flow": 100.0,
			"capital_expenditure": -30.0},
	]
	income = [
		{"fiscal_date": date(2025, 12, 31), "net_income": 120.0,
			"gross_profit": 300.0, "total_revenue": 500.0,
			"operating_income": 80.0, "otherunder_preferred_stock_dividend": None},
		{"fiscal_date": date(2024, 12, 31), "net_income": 100.0,
			"gross_profit": 260.0, "total_revenue": 440.0,
			"operating_income": 70.0, "otherunder_preferred_stock_dividend": None},
	]
	return balance, cash, income


def test_insert_fa_usd_usd_unchanged(monkeypatch):
	# golden-equivalent: same ccy -> rate 1.0 -> all metrics byte-identical
	balance, cash, income = _statements()
	_patch_db(monkeypatch, balance, cash, income, dividends=1.02)
	inserted = []
	monkeypatch.setattr(pfa, "insert_data_statement",
		lambda data, table, update_condition=None, label="": inserted.append(data) or 1)

	quote = {"stock_price": 100.0, "market_cap": 2000.0, "currency": "USD"}
	ctx = FakeCtx(["AAPL"])
	ctx.symbol_meta = {"AAPL": {"statement_currency": "USD"}}
	stats = new_phase("fa", 1)
	insert_fa(ctx, "AAPL", quote, None, stats)

	assert stats["symbols_ok"] == 1
	assert len(inserted) == 1
	row = inserted[0]
	# eps = 120/50 = 2.4 -> pe = 100/2.4
	assert row["pe_ratio"] == pytest.approx(100 / 2.4)
	# pb = 2000/200
	assert row["pb_ratio"] == pytest.approx(10.0)
	# assets_price = ((500 - 100) * 1.5) / 2000
	assert row["assets_price"] == pytest.approx(0.3)
	assert row["period"] == "TTM"


def test_insert_fa_fx_scales_statement_side(monkeypatch):
	# KEP-style: KRW statements, USD quote. rate(USD/KRW) = 1/1400
	balance, cash, income = _statements()
	_patch_db(monkeypatch, balance, cash, income, dividends=0.0)
	inserted = []
	monkeypatch.setattr(pfa, "insert_data_statement",
		lambda data, table, update_condition=None, label="": inserted.append(data) or 1)

	fx = make_fx_lookup({("USD", "KRW", date(2026, 11, 5)): 1400.0})
	quote = {"stock_price": 30.0, "market_cap": 1500.0, "currency": "USD"}
	ctx = FakeCtx(["KEP"])
	ctx.symbol_meta = {"KEP": {"statement_currency": "KRW"}}
	stats = new_phase("fa", 1)
	insert_fa(ctx, "KEP", quote, fx, stats)

	assert stats["symbols_ok"] == 1
	row = inserted[0]
	rate = 1 / 1400
	eps_trading = 120.0 * rate / 50.0
	assert row["pe_ratio"] == pytest.approx(30.0 / eps_trading)
	assert row["pb_ratio"] == pytest.approx(1500.0 / (200.0 * rate))
	assert row["assets_price"] == pytest.approx(round(((500.0 - 100.0) * rate * 1.5) / 1500.0, 4))


def test_insert_fa_missing_fx_rate_nulls_ratio_keys_only(monkeypatch):
	# unknown statement ccy -> pe/pb/assets_price NULL, other metrics intact
	balance, cash, income = _statements()
	_patch_db(monkeypatch, balance, cash, income, dividends=1.02)
	inserted = []
	monkeypatch.setattr(pfa, "insert_data_statement",
		lambda data, table, update_condition=None, label="": inserted.append(data) or 1)

	# fx closure present but TRY has no rates
	fx = make_fx_lookup({("USD", "KRW", date(2026, 11, 5)): 1400.0})
	quote = {"stock_price": 100.0, "market_cap": 2000.0, "currency": "USD"}
	ctx = FakeCtx(["TRY"])
	ctx.symbol_meta = {"TRY": {"statement_currency": "TRY"}}  # no TRY rate in fx
	stats = new_phase("fa", 1)
	insert_fa(ctx, "TRY", quote, fx, stats)

	assert stats["symbols_ok"] == 1
	row = inserted[0]
	assert row["pe_ratio"] is None
	assert row["pb_ratio"] is None
	assert row["assets_price"] is None
	# ccy-pure metrics unaffected
	assert row["gross_margin"] == pytest.approx(300.0 / 500.0)
	assert row["return_on_equity"] == pytest.approx(120.0 / 200.0)
	# growth ccy-cancelled (same ccy both years) -> unaffected
	assert row["revenue_growth"] is not None
