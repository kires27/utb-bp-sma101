import threading

import pytest

from lib.functions.netstats import incr_db, incr_yf, snapshot
from lib.functions.stats import network_line


@pytest.fixture(autouse=True)
def reset_counters(monkeypatch):
	# netstats counters are module-level; give each test a clean slate.
	monkeypatch.setattr("lib.functions.netstats._counters", {"yfinance": 0, "db": 0})
	monkeypatch.setattr("lib.functions.netstats._lock", threading.Lock())


def test_incr_yf_accumulates():
	incr_yf()
	incr_yf(4)
	assert snapshot()["yfinance"] == 5


def test_incr_db_accumulates():
	incr_db()
	incr_db(2)
	assert snapshot()["db"] == 3


def test_snapshot_is_copy():
	inc = snapshot()
	inc["yfinance"] = 99
	assert snapshot()["yfinance"] != 99


def test_incr_yf_thread_safe():
	threads = [threading.Thread(target=incr_yf) for _ in range(50)]
	for t in threads:
		t.start()
	for t in threads:
		t.join()
	assert snapshot()["yfinance"] == 50


def test_network_line_format():
	incr_yf(12)
	incr_db(34)
	assert network_line() == "NETWORK yfinance=12 db=34"


def test_network_line_parses_like_phase_lines():
	# verify.py parse_phase_lines must ignore the NETWORK line (non-PHASE prefix).
	from verify import parse_phase_lines

	incr_yf(1)
	incr_db(1)
	assert parse_phase_lines(network_line()) == {}
