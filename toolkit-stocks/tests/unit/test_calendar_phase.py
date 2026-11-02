'''Calendar phase wiring: config load, source->transform->flusher plumbing,
stats accounting. DB and network faked out.'''
import pytest

import pipeline.calendar as pc
from pipeline.calendar import load_config, run_calendar


class FakeSource:
	def __init__(self, events):
		self.events = events
		self.fetched_with = None

	def fetch(self, config):
		self.fetched_with = config
		return self.events


class FakeFlusher:
	instances = []

	def __init__(self, table, flush_size=None, conflict_keys=None, null_tolerance=None):
		self.table = table
		self.conflict_keys = conflict_keys
		self.rows = []
		FakeFlusher.instances.append(self)

	def add(self, rows):
		self.rows.extend(rows)

	def finish(self):
		return len(self.rows)


def _event(symbol="AAPL", event_type="earnings"):
	return {
		"ticker": symbol,
		"eventname": "Q3 2026 Earnings",
		"startdatetime": "2026-11-04T12:30:00.000Z",
		"_event_type": event_type,
		"_region": "us",
	}


@pytest.fixture(autouse=True)
def _reset():
	FakeFlusher.instances.clear()
	yield


# ---- config ----

def test_repo_config_loads():
	config = load_config()
	assert config["window_days"] == 14
	assert config["window_start"] and config["window_end"]
	assert set(config["event_types"]) == {"earnings", "economic_event"}
	earnings = config["event_types"]["earnings"]
	assert earnings["entity_id_type"] == "sp_earnings"
	assert "us" in earnings["regions"]
	# economic events sweep globally (no per-region pages)
	assert config["event_types"]["economic_event"]["regions"] == []


def test_window_is_window_days_long():
	from datetime import date

	config = load_config()
	start = date.fromisoformat(config["window_start"])
	end = date.fromisoformat(config["window_end"])
	assert (end - start).days == config["window_days"]


# ---- run_calendar ----

def test_run_calendar_wires_source_transform_flusher(monkeypatch):
	source = FakeSource([_event(), _event(symbol="MSFT"), _event(symbol="", event_type="economic_event")])
	monkeypatch.setattr(pc, "CalendarSource", lambda: source)
	monkeypatch.setattr(pc, "get_stock_id_map", lambda symbols: {"AAPL": 1, "MSFT": 2})
	monkeypatch.setattr(pc, "RowFlusher", FakeFlusher)

	stats = run_calendar()

	assert stats["phase"] == "calendar"
	assert stats["symbols_ok"] == stats["symbols_total"]  # all sweeps succeeded
	assert stats["rows_written"] == 3
	flusher = FakeFlusher.instances[0]
	assert flusher.table == "stock_economic_calendar"
	assert flusher.conflict_keys == pc.CONFLICT_KEYS
	# enrichment: earnings got stock_ids, econ event kept None
	assert flusher.rows[0]["stock_id"] == 1
	assert flusher.rows[1]["stock_id"] == 2
	assert flusher.rows[2]["stock_id"] is None


def test_run_calendar_no_events_is_clean_noop(monkeypatch):
	monkeypatch.setattr(pc, "CalendarSource", lambda: FakeSource([]))
	monkeypatch.setattr(pc, "get_stock_id_map", lambda symbols: {})
	monkeypatch.setattr(pc, "RowFlusher", FakeFlusher)

	stats = run_calendar()

	assert stats["rows_written"] == 0
	assert FakeFlusher.instances == []


def test_run_calendar_drops_unknown_symbol_earnings(monkeypatch):
	# macro events always kept; earnings only when the stock is in the DB
	source = FakeSource([
		_event(),                                   # AAPL, known
		_event(symbol="NOPE"),                      # earnings, not in DB -> dropped
		_event(symbol="", event_type="economic_event"),  # macro, always kept
	])
	monkeypatch.setattr(pc, "CalendarSource", lambda: source)
	monkeypatch.setattr(pc, "get_stock_id_map", lambda symbols: {"AAPL": 1})
	monkeypatch.setattr(pc, "RowFlusher", FakeFlusher)

	stats = run_calendar()

	assert stats["rows_written"] == 2
	written_symbols = [r["symbol"] for r in FakeFlusher.instances[0].rows]
	assert written_symbols == ["AAPL", ""]


def test_sweeps_counted_from_config(monkeypatch):
	monkeypatch.setattr(pc, "CalendarSource", lambda: FakeSource([_event()]))
	monkeypatch.setattr(pc, "get_stock_id_map", lambda symbols: {})
	monkeypatch.setattr(pc, "RowFlusher", FakeFlusher)

	stats = run_calendar()

	# earnings: 5 regions, economic: 1 global sweep
	assert stats["symbols_total"] == 6
