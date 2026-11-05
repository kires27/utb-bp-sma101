from datetime import date, datetime, timedelta, timezone

from lib.functions.stats import new_phase, summary_line
from verify import MAX_FAILED_RATIO, days_since, check_failed_ratio, parse_phase_lines


def test_days_since_with_date():
	assert days_since(date.today()) == 0
	assert days_since(date.today() - timedelta(days=3)) == 3


def test_days_since_with_timestamptz_datetime():
	# Regression: maintenance_update arrives from psycopg2 as tz-aware
	# datetime; date.today() - datetime raises TypeError without coercion.
	aware = datetime.now(timezone.utc) - timedelta(days=2)
	assert days_since(aware) == 2


def test_days_since_with_naive_datetime():
	naive = datetime.now() - timedelta(days=5)
	assert days_since(naive) == 5


def test_check_failed_ratio_healthy():
	ok, msg = check_failed_ratio({"symbols_total": 100, "symbols_ok": 100})
	assert ok
	assert "failed=0" in msg


def test_check_failed_ratio_over_threshold():
	ok, _ = check_failed_ratio({"symbols_total": 100, "symbols_ok": 90})
	assert not ok	# 10% failed > 2% limit


def test_check_failed_ratio_fresh_skips_not_failures():
	# skipped_fresh symbols fetched nothing (data already current); they are
	# not failures. Regression: 100 skips looked like 100% failure.
	ok, msg = check_failed_ratio({
		"symbols_total": 100, "symbols_ok": 0, "skipped_fresh": 100,
	})
	assert ok
	assert "failed=0" in msg


def test_check_failed_ratio_skips_counted_separately():
	# 98 ok + 2 fresh skips = 0 real failures.
	ok, msg = check_failed_ratio({
		"symbols_total": 100, "symbols_ok": 98, "skipped_fresh": 2,
	})
	assert ok
	assert "failed=0" in msg
	# 96 ok + 1 skip + 3 real failures = 3% > 2% limit.
	ok, _ = check_failed_ratio({
		"symbols_total": 100, "symbols_ok": 96, "skipped_fresh": 1,
		"failed_symbols": ["BAD1", "BAD2", "BAD3"],
	})
	assert not ok


def test_check_failed_ratio_all_skipped_lists_no_failures():
	ok, msg = check_failed_ratio({
		"symbols_total": 198, "symbols_ok": 0, "skipped_fresh": 198,
	})
	assert ok
	assert "skipped_fresh=198" in msg


def test_check_failed_ratio_at_threshold():
	total, failed = 50, 1
	ok, _ = check_failed_ratio({"symbols_total": total, "symbols_ok": total - failed})
	assert ok	# 1/50 = 2% <= limit (inclusive)


def test_check_failed_ratio_default_limit():
	ok, _ = check_failed_ratio({"symbols_total": 100, "symbols_ok": 97})
	assert ok is (MAX_FAILED_RATIO >= 0.03)	# sanity: threshold read from constant


def test_check_failed_ratio_no_symbols():
	ok, msg = check_failed_ratio({"symbols_total": 0, "symbols_ok": 0})
	assert not ok
	assert msg == "no symbols processed at all"


def test_check_failed_ratio_lists_failed_symbols():
	ok, msg = check_failed_ratio({
		"symbols_total": 100, "symbols_ok": 97,
		"failed_symbols": ["BAD1", "BAD2", "BAD3"],
	})
	assert not ok	# 3% failed > 2% limit
	assert "first: BAD1, BAD2, BAD3" in msg


def test_parse_phase_lines_full_format():
	stats = parse_phase_lines(
		"PHASE quote total=4000 ok=3990 rows=3990 skipped_fresh=0 first=BAD1,BAD2"
	)
	assert stats == {
		"quote": {
			"symbols_total": 4000,
			"symbols_ok": 3990,
			"rows_written": 3990,
			"skipped_fresh": 0,
			"skipped_no_q": 0,
			"failed_symbols": ["BAD1", "BAD2"],
		}
	}


def test_parse_phase_lines_skips_fresh_value():
	stats = parse_phase_lines(
		"PHASE balance_sheet total=198 ok=0 rows=0 skipped_fresh=198"
	)
	assert stats["balance_sheet"] == {
		"symbols_total": 198,
		"symbols_ok": 0,
		"rows_written": 0,
		"skipped_fresh": 198,
		"skipped_no_q": 0,
		"failed_symbols": [],
	}


def test_parse_phase_lines_no_q_value():
	stats = parse_phase_lines(
		"PHASE cash_flow_quarterly total=198 ok=72 rows=358 skipped_fresh=81 no_q=45"
	)
	assert stats["cash_flow_quarterly"] == {
		"symbols_total": 198,
		"symbols_ok": 72,
		"rows_written": 358,
		"skipped_fresh": 81,
		"skipped_no_q": 45,
		"failed_symbols": [],
	}


def test_parse_phase_lines_healthy_line_has_no_failed_symbols():
	# skipped_fresh=0 must not be mistaken for the first= failure tail.
	stats = parse_phase_lines("PHASE overview total=100 ok=100 rows=50 skipped_fresh=0")
	assert stats["overview"]["failed_symbols"] == []
	assert stats["overview"]["rows_written"] == 50


def test_parse_phase_lines_multiple_phases():
	stats = parse_phase_lines(
		"PHASE quote total=10 ok=10 rows=10 skipped_fresh=0\n"
		"noise line\n"
		"PHASE financial_analysis total=10 ok=8 rows=8 skipped_fresh=0 first=A"
	)
	assert set(stats) == {"quote", "financial_analysis"}
	assert stats["financial_analysis"]["failed_symbols"] == ["A"]


def test_parse_phase_lines_malformed_lines_skipped():
	stats = parse_phase_lines(
		"PHASE broken total=10\n"				# IndexError path
		"PHASE broken2 total=abc ok=10 rows=10	\n"	# ValueError path
		"PHASE good total=10 ok=10 rows=10 skipped_fresh=0"
	)
	assert stats == {
		"good": {
			"symbols_total": 10, "symbols_ok": 10, "rows_written": 10,
			"skipped_fresh": 0, "skipped_no_q": 0, "failed_symbols": [],
		}
	}


def test_roundtrip_with_summary_line():
	# verify.py parsing must match what lib.functions.stats emits.
	stats = new_phase("quote", 100)
	stats["symbols_ok"] = 98
	stats["rows_written"] = 98
	stats["skipped_fresh"] = 2
	stats["skipped_no_q"] = 0
	stats["failed_symbols"] = ["BAD1"]
	parsed = parse_phase_lines(summary_line(stats))
	assert parsed["quote"] == {
		"symbols_total": 100, "symbols_ok": 98, "rows_written": 98,
		"skipped_fresh": 2, "skipped_no_q": 0, "failed_symbols": ["BAD1"],
	}
