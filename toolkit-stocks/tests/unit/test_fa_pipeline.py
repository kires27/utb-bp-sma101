'''run_financial_analysis: quote-row-driven market data, skip-on-missing.
DB and network faked out (no datasource mocking - FA reads stock_quote;
dividend_yield is computed inside build_financial_analysis).'''
from types import SimpleNamespace

import pytest

import pipeline.financial_analysis as pfa
from pipeline.financial_analysis import run_financial_analysis


class FakeCtx:
	def __init__(self, symbols):
		self.args = SimpleNamespace(force=False, full=False)
		self.symbols = symbols
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)}
		self.yfs = None


@pytest.fixture
def calls(monkeypatch):
	scored = []

	def fake_insert_and_score(ctx, symbol, quote, stats):
		scored.append((symbol, quote))
		pfa.count_symbol(stats, True, rows=1)

	monkeypatch.setattr(pfa, "insert_fa", fake_insert_and_score)
	return scored


def _patch_quotes(monkeypatch, mapping):
	monkeypatch.setattr(pfa, "get_quotes", lambda ids: mapping)


def test_all_quotes_present(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": 100.0, "market_cap": 2e12},
	})
	ctx = FakeCtx(["AAPL"])
	stats = run_financial_analysis(ctx)

	assert stats["symbols_ok"] == 1
	assert calls == [("AAPL", {"stock_price": 100.0, "market_cap": 2e12})]


def test_missing_quote_row_skipped(monkeypatch, calls):
	_patch_quotes(monkeypatch, {})
	ctx = FakeCtx(["AAPL", "MSFT"])
	stats = run_financial_analysis(ctx)

	assert stats["symbols_ok"] == 0
	assert stats["failed_symbols"] == ["AAPL", "MSFT"]
	assert calls == []


def test_null_market_cap_skipped_and_named(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": 100.0, "market_cap": None},
		2: {"stock_price": 50.0, "market_cap": 1e12},
	})
	ctx = FakeCtx(["AAPL", "MSFT"])
	stats = run_financial_analysis(ctx)

	assert stats["failed_symbols"] == ["AAPL"]
	assert stats["symbols_ok"] == 1
	assert calls == [("MSFT", {"stock_price": 50.0, "market_cap": 1e12})]


def test_null_price_skipped_and_named(monkeypatch, calls):
	_patch_quotes(monkeypatch, {
		1: {"stock_price": None, "market_cap": 2e12},
	})
	ctx = FakeCtx(["AAPL"])
	stats = run_financial_analysis(ctx)

	assert stats["failed_symbols"] == ["AAPL"]
	assert calls == []
