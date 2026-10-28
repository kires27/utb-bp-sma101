'''
Layer 3 — live smoke tests (real network).

Run explicitly:  .venv/bin/python -m pytest tests/ -m live
Skipped by default (CI push/PR runs -m "not live").
Invariants only — no hardcoded values.
'''


import math

import pytest

from datasource.yfinance_source import YFinanceSource
from datasource.defeatbeta import DefeatBetaSource
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
	_check_price_rows(build_price_rows(SYMBOL_US, 1, payload["price_rows"], payload["div_events"], payload["split_events"], None), "yfinance")
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


def test_defeatbeta_invariants():
	ds = DefeatBetaSource()
	prices = ds.prices([SYMBOL_US]).get(SYMBOL_US, [])
	assert prices, "DefeatBeta prices empty"
	_dates_ordered([r["date"] for r in prices], "defeatbeta")
	divs = ds.dividends([SYMBOL_US]).get(SYMBOL_US, [])
	splits = ds.splits([SYMBOL_US]).get(SYMBOL_US, [])
	_check_price_rows(build_price_rows(SYMBOL_US, 1, prices, divs, splits, None), "defeatbeta")
	assert build_overview_row(SYMBOL_US, ds.profiles([SYMBOL_US])[SYMBOL_US], [], {}, None)


def test_parity_overlapping_dates():
	'''Same symbol from both sources: overlapping recent closes within 1% tolerance.'''
	yfs = YFinanceSource(max_workers=1)
	ds = DefeatBetaSource()
	yf_rows = build_price_rows(SYMBOL_US, 1, *(lambda p: (p["price_rows"], p["div_events"], p["split_events"], None))(yfs.history_payload(SYMBOL_US)))
	db_rows = build_price_rows(SYMBOL_US, 1, ds.prices([SYMBOL_US])[SYMBOL_US], ds.dividends([SYMBOL_US])[SYMBOL_US], ds.splits([SYMBOL_US])[SYMBOL_US], None)
	yf_by_date = {r["date"]: r["close"] for r in yf_rows}
	overlap = [r for r in db_rows if r["date"] in yf_by_date]
	assert overlap, "no overlapping dates between sources"
	worst = max(abs(r["close"] - yf_by_date[r["date"]]) / yf_by_date[r["date"]] for r in overlap)
	assert worst < 0.01, f"sources disagree by {worst:.2%}"


def test_failover_drill_live():
	'''Real FailoverSource: primary (DefeatBeta) simulated outage -> yfinance fallback serves full history.'''
	from datasource.failover import FailoverSource, price_rows_valid

	yfs = YFinanceSource(max_workers=1)
	failing = DefeatBetaSource.__new__(DefeatBetaSource)
	failing.prices = lambda symbols: (_ for _ in ()).throw(ConnectionError("simulated outage"))
	fo = FailoverSource(failing, yfs)
	rows = fo.prices([SYMBOL_US])[SYMBOL_US]
	assert rows, "fallback produced no price rows"
	assert price_rows_valid(rows)
	_check_price_rows(build_price_rows(SYMBOL_US, 1, rows, fo.dividends([SYMBOL_US])[SYMBOL_US], fo.splits([SYMBOL_US])[SYMBOL_US], None), "failover-yfinance")
