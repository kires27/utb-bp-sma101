'''
Layer 3 — live smoke tests (real network).

Run explicitly:  .venv/bin/python -m pytest tests/ -m live
Skipped by default (CI push/PR runs -m "not live").
Invariants only — no hardcoded values.
'''


import math

import pytest

from datasource.yfinance_source import YFinanceSource
from datasource.quotes_batch import QuotesBatchSource
from lib.transforms import (
	build_price_rows, build_dividend_rows, build_split_rows,
	build_overview_row, build_statement_rows,
)

SYMBOL_US = "AAPL"
SYMBOL_INTL = "ASML.AS"

pytestmark = pytest.mark.live


def _dates_ordered(dates, source):
	'''Dates must be strictly monotonic (either direction) with no dupes.'''
	assert dates == sorted(dates) or dates == sorted(dates, reverse=True), f"{source}: dates not ordered"
	assert len(set(dates)) == len(dates), f"{source}: duplicate dates"


def _check_price_rows(rows, source):
	assert rows, f"{source}: no price rows"
	_dates_ordered([r["date"] for r in rows], source)
	for r in rows:
		for field in ("open", "high", "low", "close"):
			v = r[field]
			assert v is None or (isinstance(v, float) and v > 0 and not math.isnan(v)), f"{source}: bad {field} {v}"


def test_yfinance_history_invariants():
	yfs = YFinanceSource(max_workers=1)
	payload = yfs.history_payload(SYMBOL_US)
	assert payload and payload["price_rows"]
	_check_price_rows(build_price_rows(SYMBOL_US, 1, payload["price_rows"], None), "yfinance")
	assert build_dividend_rows(SYMBOL_US, 1, payload["div_events"], None) is not None
	assert build_split_rows(SYMBOL_US, 1, payload["split_events"], None) is not None
	for d in payload["div_events"]:
		assert d["amount"] > 0
	for s in payload["split_events"]:
		assert s["factor"] > 0


def test_yfinance_statements_and_info_invariants():
	yfs = YFinanceSource(max_workers=1)
	info = yfs.info(SYMBOL_US)
	assert info and info.get("longName") or info.get("shortName")
	row = build_overview_row(SYMBOL_US, info, None, {}, info)
	assert row  # mapper ran without exception
	grouped = yfs.statements_payload(SYMBOL_US, "income_statement")
	assert grouped
	rows = build_statement_rows(SYMBOL_US, 1, grouped, "annual", "income_statement")
	assert rows and all(r["fiscal_date"] for r in rows)


def test_quotes_batch_invariants():
	'''Batched v7/quote: 2 symbols, 1 call, normalized fields present.'''
	src = QuotesBatchSource()
	quotes = src.fetch([SYMBOL_US, SYMBOL_INTL])
	assert len(quotes) == 2, f"quotes_batch returned {len(quotes)} symbols"
	for sym, q in quotes.items():
		assert q["stock_price"] is not None, f"{sym}: no price"
		assert q["market_state"] in ("REGULAR", "PRE", "POST", "POSTPOST", "CLOSED", "PREPRE"), f"{sym}: bad market_state {q['market_state']}"
		assert q["regular_market_time"] is not None, f"{sym}: no regular_market_time"


def test_quotes_batch_gbp_scaling():
	'''GBp-quoted symbols: price scaled to base currency (marketCap untouched).'''
	from data.symbols import manual_symbols

	gbp_syms = [s for s in manual_symbols if s.endswith(".L")][:3]
	assert gbp_syms, "no GBP symbols in dev list"
	src = QuotesBatchSource()
	quotes = src.fetch(gbp_syms)
	for sym, q in quotes.items():
		assert q["currency"] in ("GBp", "GBX")
		assert q["stock_price"] < q["market_cap"], f"{sym}: GBp price not scaled (price={q['stock_price']}, mcap={q['market_cap']})"
