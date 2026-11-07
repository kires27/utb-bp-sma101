from datetime import date, datetime, timezone
from decimal import Decimal

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
	monkeypatch.setattr(p, "get_latest_shares_outstanding", lambda ids: {})
	monkeypatch.setattr(p, "get_split_factors", lambda ids: {})
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
	monkeypatch.setattr(p, "get_latest_shares_outstanding", lambda ids: {})
	monkeypatch.setattr(p, "get_split_factors", lambda ids: {})
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
	monkeypatch.setattr(p, "get_latest_shares_outstanding", lambda ids: {})
	monkeypatch.setattr(p, "get_split_factors", lambda ids: {})
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
	# 5% off, not a clean ADR fraction -> own value wins
	quote = {"stock_price": 100.0, "market_cap": 2e12}
	p.own_market_cap(quote, 5_250_000_000, "TEST")
	assert quote["market_cap"] == 5.25e11


def test_own_market_cap_falls_back_to_yahoo():
	# no / zero / null shares -> Yahoo cap untouched
	quote = {"stock_price": 100.0, "market_cap": 2e12}
	p.own_market_cap(quote, None, "TEST")
	assert quote["market_cap"] == 2e12
	p.own_market_cap(quote, 0, "TEST")
	assert quote["market_cap"] == 2e12
	# negative shares (Yahoo dollar-value-in-count-field, e.g. RY.TO
	# preferred = C$14B) -> invalid, Yahoo cap untouched
	p.own_market_cap(quote, -1_384_554_000, "TEST")
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
	monkeypatch.setattr(p, "get_latest_shares_outstanding", lambda ids: {2: (1_000_000, date(2024, 1, 1))})
	monkeypatch.setattr(p, "get_split_factors", lambda ids: {})
	flushes = []
	monkeypatch.setattr(p, "insert_rows_bulk", lambda table, rows, conflict_keys=None, null_tolerance=1: flushes.append((table, len(rows))) or len(rows))

	quotes = {
		"B": {"stock_price": 25.0, "market_state": "PREPRE", "regular_market_time": 1704211200, "market_cap": None, "regular_market_change": None, "regular_market_change_percent": None},
	}
	monkeypatch.setattr(p.QuotesBatchSource, "fetch", lambda self, symbols: quotes)

	stats = p.run_quote(["B"], {"B": 2})

	assert stats["symbols_ok"] == 1
	assert flushes and flushes[0] == ("stock_quote", 1)


def test_adjusted_shares_applies_later_splits():
	# SMFG (8316.T): filing 2026-06-30 3.83B shares, 2-for-1 split 2026-09-29
	# -> post-split basis; split BEFORE the filing date must NOT apply.
	splits = [(date(2024, 9, 27), 3.0), (date(2026, 9, 29), 2.0)]
	assert p.adjusted_shares(3_826_458_640.0, date(2026, 6, 30), splits) == 7_652_917_280.0
	assert p.adjusted_shares(3_826_458_640.0, date(2026, 12, 31), splits) == 3_826_458_640.0
	assert p.adjusted_shares(1_000.0, date(2024, 1, 1), []) == 1_000.0


def test_adjusted_shares_handles_decimal_share_count():
	# regression: DB returns share_issued as decimal.Decimal (numeric column);
	# Decimal * float used to raise TypeError (2026-11-07 crash on a symbol
	# with a split after the filing's fiscal_date)
	splits = [(date(2026, 9, 29), 2.0)]
	assert p.adjusted_shares(Decimal("38261953477800"), date(2026, 6, 30), splits) == 76_523_906_955_600.0
	assert p.adjusted_shares(Decimal("38261953477800"), date(2026, 12, 31), []) == 38_261_953_477_800.0


def test_derive_adr_ratio_snaps_clean_fractions():
	# real divergences from the 2026-11-07 log
	assert p.derive_adr_ratio(1_535_484_000_000, 76_786_417_664) == 20	# AMX
	assert p.derive_adr_ratio(238_828_218_061, 119_414_112_256) == 2	# PBR
	assert p.derive_adr_ratio(7_189_997_662, 14_379_995_136) == 0.5	# KEP


def test_derive_adr_ratio_rejects_noisy_divergence():
	# treasury-share divergence (1.02-1.17) and split-window (0.508) are
	# not clean fractions -> None (handled by warning / split adjustment)
	assert p.derive_adr_ratio(1.05e11, 1e11) is None
	assert p.derive_adr_ratio(1_150_998_758_912, 2_264_024_062_336) is None


def test_own_market_cap_corrects_via_adr_ratio(capsys):
	# AMX: ADR price x all ordinary shares = 20x true cap -> corrected own
	quote = {"stock_price": 25.72, "market_cap": 76_786_417_664}
	p.own_market_cap(quote, 59_700_000_000, "AMX")
	assert quote["market_cap"] == 25.72 * 59_700_000_000 / 20
	out = capsys.readouterr().out
	assert "ADR 20x" in out and "AMX" in out and "ratio 19.997" in out
	assert "WARNING" not in out


def test_own_market_cap_no_adr_without_yahoo():
	# no yahoo cap -> nothing to derive from -> raw own calc wins
	quote = {"stock_price": 25.72, "market_cap": None}
	p.own_market_cap(quote, 59_700_000_000, "AMX")
	assert quote["market_cap"] == 25.72 * 59_700_000_000
