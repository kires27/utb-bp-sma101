from lib.functions.stats import count_symbol, new_phase, summary_line
from verify import parse_phase_lines


def test_new_phase_defaults():
	stats = new_phase("prices", 100)
	assert stats == {
		"phase": "prices",
		"symbols_total": 100,
		"symbols_ok": 0,
		"rows_written": 0,
		"failed_symbols": [],
	}


def test_count_symbol_ok_accumulates_rows():
	stats = new_phase("prices", 10)
	count_symbol(stats, True, rows=5)
	count_symbol(stats, True, rows=2)
	assert stats["symbols_ok"] == 2
	assert stats["rows_written"] == 7
	assert stats["failed_symbols"] == []


def test_count_symbol_failed_capped_at_20():
	stats = new_phase("prices", 30)
	for i in range(25):
		count_symbol(stats, False, symbol=f"S{i}")
	assert len(stats["failed_symbols"]) == 20
	assert stats["failed_symbols"][0] == "S0"
	assert stats["symbols_ok"] == 0


def test_summary_line_without_failures():
	stats = new_phase("metrics", 100)
	stats["symbols_ok"] = 98
	stats["rows_written"] = 98
	assert summary_line(stats) == "PHASE metrics total=100 ok=98 rows=98 skipped_fresh=0"


def test_summary_line_with_failures():
	stats = new_phase("metrics", 100)
	stats["symbols_ok"] = 98
	stats["failed_symbols"] = ["BAD1", "BAD2"]
	line = summary_line(stats)
	assert line.startswith("PHASE metrics total=100 ok=98 rows=0")
	assert "first=BAD1,BAD2" in line


def test_parse_phase_lines_roundtrip():
	lines = [
		"PHASE market_data total=100 ok=98 rows=1234 first=BAD1",
		"PHASE metrics total=100 ok=100 rows=100",
		"[2026-10-24 08:00:00] [INFO] noise line",
	]
	stats = parse_phase_lines("\n".join(lines))
	assert stats["market_data"] == {"symbols_total": 100, "symbols_ok": 98, "rows_written": 1234}
	assert stats["metrics"] == {"symbols_total": 100, "symbols_ok": 100, "rows_written": 100}
	assert len(stats) == 2


def test_parse_phase_lines_empty_and_malformed():
	assert parse_phase_lines("") == {}
	assert parse_phase_lines("PHASE broken total=x") == {}
