from datetime import datetime, timezone

import pipeline.prices as p


def test_should_write_live_states():
	for state in ("REGULAR", "POST", "POSTPOST"):
		assert p.should_write({"market_state": state, "regular_market_time": 1000}, None)


def test_should_write_closed_newer_time():
	# closed market, fetched time newer than stored -> write (missed close)
	stored = datetime(2024, 1, 2, 15, 0, tzinfo=timezone.utc)
	assert p.should_write({"market_state": "CLOSED", "regular_market_time": 1704211200 + 3600}, stored)


def test_should_write_closed_older_or_equal():
	stored = datetime.fromtimestamp(1704211200 + 3600, tz=timezone.utc)
	assert not p.should_write({"market_state": "CLOSED", "regular_market_time": 1704211200}, stored)
	assert not p.should_write({"market_state": "CLOSED", "regular_market_time": 1704211200 + 3600}, stored)


def test_should_write_closed_no_time():
	assert not p.should_write({"market_state": "CLOSED", "regular_market_time": None}, None)
	assert not p.should_write({"market_state": "CLOSED"}, None)


def test_should_write_unknown_state_with_time():
	# unknown state (e.g. PRE/PREPRE) behaves like closed: only newer-than-stored
	stored = datetime.fromtimestamp(1000, tz=timezone.utc)
	assert p.should_write({"market_state": "PREPRE", "regular_market_time": 2000}, stored)
	assert not p.should_write({"market_state": "PREPRE", "regular_market_time": 1000}, stored)


def test_run_hourly_skips_gated_and_flushes_remaining(monkeypatch):
	import lib.supabase.sql_functions as sqlf

	monkeypatch.setattr(p, "get_latest_market_times", lambda ids: {2: datetime.fromtimestamp(1704211200 + 3600, tz=timezone.utc)})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append((table, len(rows))) or len(rows))

	quotes = {
		"A": {"stock_price": 1.0, "market_state": "REGULAR", "regular_market_time": 1, "market_cap": 10, "regular_market_change": None, "regular_market_change_percent": None, "dividend_yield": None},
		"B": {"stock_price": 2.0, "market_state": "CLOSED", "regular_market_time": 1704211200, "market_cap": 20, "regular_market_change": None, "regular_market_change_percent": None, "dividend_yield": None},
		"C": {"stock_price": 3.0, "market_state": "CLOSED", "regular_market_time": 1704211200 + 7200, "market_cap": 30, "regular_market_change": None, "regular_market_change_percent": None, "dividend_yield": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	ids = {"A": 1, "B": 2, "C": 3}
	stats = p.run_hourly_prices(["A", "B", "C"], ids)

	assert stats["symbols_ok"] == 2  # A live, C newer-than-stored; B gated out
	assert flushes and flushes[0] == ("stock_metric", 2)
