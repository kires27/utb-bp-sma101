"""Per-run network request counters (logical calls, not raw wire requests).

yfinance: one increment per API call site (with_backoff attempts, quote
chunks, calendar pages, screener pages). DB: one increment per cursor
execute/executemany via CountingCursor (lib.supabase.init).
"""
import threading

_lock = threading.Lock()
_counters = {"yfinance": 0, "db": 0}


def incr_yf(n: int = 1):
	'''Count n yfinance requests (thread-safe: with_backoff runs in workers).'''
	with _lock:
		_counters["yfinance"] += n


def incr_db(n: int = 1):
	'''Count n DB requests (main-thread only, lock kept for symmetry).'''
	with _lock:
		_counters["db"] += n


def snapshot() -> dict:
	'''Copy of current counters: {"yfinance": int, "db": int}.'''
	with _lock:
		return dict(_counters)
