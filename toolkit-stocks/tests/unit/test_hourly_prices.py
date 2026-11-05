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


def test_run_quote_skips_gated_and_flushes_remaining(monkeypatch):
	import lib.supabase.sql_functions as sqlf

	monkeypatch.setattr(p, "get_latest_market_times", lambda ids: {2: datetime.fromtimestamp(1704211200 + 3600, tz=timezone.utc)})
	monkeypatch.setattr(p, "get_missing_market_caps", lambda ids: set())
	monkeypatch.setattr(p, "get_latest_share_issued", lambda ids: {})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append((table, len(rows))) or len(rows))

	quotes = {
		"A": {"stock_price": 1.0, "market_state": "REGULAR", "regular_market_time": 1, "market_cap": 10, "regular_market_change": None, "regular_market_change_percent": None},
		"B": {"stock_price": 2.0, "market_state": "CLOSED", "regular_market_time": 1704211200, "market_cap": 20, "regular_market_change": None, "regular_market_change_percent": None},
		"C": {"stock_price": 3.0, "market_state": "CLOSED", "regular_market_time": 1704211200 + 7200, "market_cap": 30, "regular_market_change": None, "regular_market_change_percent": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	ids = {"A": 1, "B": 2, "C": 3}
	stats = p.run_quote(["A", "B", "C"], ids)

	assert stats["symbols_ok"] == 2  # A live, C newer-than-stored; B gated out
	assert stats["skipped_fresh"] == 1
	assert flushes and flushes[0] == ("stock_quote", 2)


def test_run_quote_self_heals_missing_cap(monkeypatch):
	# B: closed market, time equal to stored (gated out), but stored cap is
	# NULL and this fetch has one -> must be written despite gating.
	gated = datetime.fromtimestamp(1704211200, tz=timezone.utc)
	monkeypatch.setattr(p, "get_latest_market_times", lambda ids: {2: gated, 3: gated})
	monkeypatch.setattr(p, "get_missing_market_caps", lambda ids: {2})
	monkeypatch.setattr(p, "get_latest_share_issued", lambda ids: {})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append((table, len(rows))) or len(rows))

	quotes = {
		"A": {"stock_price": 1.0, "market_state": "REGULAR", "regular_market_time": 1, "market_cap": 10, "regular_market_change": None, "regular_market_change_percent": None},
		"B": {"stock_price": 2.0, "market_state": "PREPRE", "regular_market_time": 1704211200, "market_cap": 20, "regular_market_change": None, "regular_market_change_percent": None},
		"C": {"stock_price": 3.0, "market_state": "PREPRE", "regular_market_time": 1704211200, "market_cap": None, "regular_market_change": None, "regular_market_change_percent": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	stats = p.run_quote(["A", "B", "C"], {"A": 1, "B": 2, "C": 3})

	assert stats["symbols_ok"] == 2  # A live, B self-healed; C fetch has no cap
	assert stats["skipped_fresh"] == 1
	assert flushes and flushes[0] == ("stock_quote", 2)


def test_run_quote_self_heal_needs_fetched_cap(monkeypatch):
	# stored cap NULL but fetch also has none -> gated out, no write loop
	monkeypatch.setattr(p, "get_latest_market_times", lambda ids: {2: datetime.fromtimestamp(1704211200, tz=timezone.utc)})
	monkeypatch.setattr(p, "get_missing_market_caps", lambda ids: {2})
	monkeypatch.setattr(p, "get_latest_share_issued", lambda ids: {})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append(len(rows)))

	quotes = {
		"B": {"stock_price": 2.0, "market_state": "PREPRE", "regular_market_time": 1704211200, "market_cap": None, "regular_market_change": None, "regular_market_change_percent": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	stats = p.run_quote(["B"], {"B": 2})

	assert stats["symbols_ok"] == 0
	assert stats["skipped_fresh"] == 1
	assert not flushes


def test_own_market_cap_prefers_own_calc():
	quote = {"stock_price": 100.0, "market_cap": 2e12}
	p.own_market_cap(quote, 5_000_000_000, "TEST")
	assert quote["market_cap"] == 5e11


def test_own_market_cap_falls_back_to_yahoo():
	# no / zero / null shares -> Yahoo cap untouched
	quote = {"stock_price": 100.0, "market_cap": 2e12}
	p.own_market_cap(quote, None, "TEST")
	assert quote["market_cap"] == 2e12
	p.own_market_cap(quote, 0, "TEST")
	assert quote["market_cap"] == 2e12
	# no price either -> fallback
	quote = {"stock_price": None, "market_cap": 2e12}
	p.own_market_cap(quote, 1_000_000, "TEST")
	assert quote["market_cap"] == 2e12


def test_own_market_cap_divergence_warns(capsys):
	# own calc 5% off Yahoo -> WARNING logged, own value still wins
	quote = {"stock_price": 100.0, "market_cap": 1e11}
	p.own_market_cap(quote, 1_050_000_000, "DIV")  # ratio 1.05
	assert quote["market_cap"] == 1.05e11
	out = capsys.readouterr().out
	assert "DIV" in out and "divergence" in out and "1.050" in out


def test_own_market_cap_within_tolerance_silent(capsys):
	# 1% off -> no warning, own value still wins
	quote = {"stock_price": 100.0, "market_cap": 1e11}
	p.own_market_cap(quote, 1_010_000_000, "OK")  # ratio 1.01
	assert quote["market_cap"] == 1.01e11
	assert "divergence" not in capsys.readouterr().out


def test_run_quote_self_heals_cap_via_own_calc(monkeypatch):
	# B: Yahoo cap missing, but BS shares exist -> own calc fills it and the
	# self-heal write fires despite gating (gated time equal to stored).
	gated = datetime.fromtimestamp(1704211200, tz=timezone.utc)
	monkeypatch.setattr(p, "get_latest_market_times", lambda ids: {2: gated})
	monkeypatch.setattr(p, "get_missing_market_caps", lambda ids: {2})
	monkeypatch.setattr(p, "get_latest_share_issued", lambda ids: {2: 1_000_000})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append((table, len(rows))) or len(rows))

	quotes = {
		"B": {"stock_price": 25.0, "market_state": "PREPRE", "regular_market_time": 1704211200, "market_cap": None, "regular_market_change": None, "regular_market_change_percent": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	stats = p.run_quote(["B"], {"B": 2})

	assert stats["symbols_ok"] == 1
	assert flushes and flushes[0] == ("stock_quote", 1)
