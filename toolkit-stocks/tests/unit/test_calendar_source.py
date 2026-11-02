'''CalendarSource: request body shape, row zipping (includeFields order),
pagination cap, region sweep, rate-limit retry.'''
import pytest
from yfinance.exceptions import YFRateLimitError

import datasource.calendar_source as cs
from datasource.calendar_source import CalendarSource


EARNINGS_FIELDS = ["ticker", "companyshortname", "eventname", "startdatetime", "startdatetimetype"]
EVENT_CFG = {
	"entity_id_type": "sp_earnings",
	"sort_field": "intradaymarketcap",
	"sort_type": "DESC",
	"regions": ["us"],
	"include_fields": EARNINGS_FIELDS,
}


class FakeResponse:
	def __init__(self, payload):
		self._payload = payload

	def json(self):
		return self._payload


class FakeData:
	'''YfData.post stand-in: returns queued pages in order, repeating the last.'''

	def __init__(self, pages, error=None):
		self.pages = list(pages)
		self.error = error
		self.calls = []

	def post(self, url, params=None, body=None):
		self.calls.append((url, params, body))
		if self.error:
			return FakeResponse(self.error)
		page = self.pages.pop(0) if len(self.pages) > 1 else self.pages[0]
		return FakeResponse(page)


def _payload(rows):
	return {"finance": {"result": [{"documents": [{"columns": [], "rows": rows}]}]}}


def _row(symbol, dt="2026-11-04T12:30:00.000Z"):
	return [symbol, f"{symbol} Co", "Q3 2026 Earnings", dt, "AM"]


def _source(data):
	src = CalendarSource.__new__(CalendarSource)  # skip YfData construction
	src._data = data
	return src


# ---- request shape ----

def test_request_body_matches_yfinance_shape():
	data = FakeData([_payload([_row("AAPL")])])
	src = _source(data)

	src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": EVENT_CFG},
	})

	url, params, body = data.calls[0]
	assert url == cs.CALENDAR_URL
	assert params == {"lang": "en-US"}
	assert body["entityIdType"] == "sp_earnings"
	assert body["sortField"] == "intradaymarketcap"
	assert body["sortType"] == "DESC"
	assert body["size"] == cs.PAGE_SIZE
	assert body["offset"] == 0
	assert body["includeFields"] == EARNINGS_FIELDS
	# region operand (not the hardcoded wrapper param) + datetime window
	ops = body["query"]["operands"]
	region_op = [o for o in ops if o["operands"][0] == "region"]
	assert region_op == [{"operator": "EQ", "operands": ["region", "us"]}]
	assert {"operator": "GTE", "operands": ["startdatetime", "2026-11-02"]} in ops
	assert {"operator": "LTE", "operands": ["startdatetime", "2026-11-16"]} in ops


def test_rows_zipped_by_include_fields():
	data = FakeData([_payload([_row("AAPL"), _row("MSFT", "2026-11-05T14:00:00.000Z")])])
	src = _source(data)

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": EVENT_CFG},
	})

	assert len(events) == 2
	assert events[0]["ticker"] == "AAPL"
	assert events[0]["eventname"] == "Q3 2026 Earnings"
	assert events[0]["startdatetime"] == "2026-11-04T12:30:00.000Z"
	assert events[0]["_event_type"] == "earnings"
	assert events[0]["_region"] == "us"
	assert events[1]["ticker"] == "MSFT"
	assert events[1]["startdatetimetype"] == "AM"


def test_short_row_keeps_prefix():
	rows = _payload([["AAPL", "Apple"]])  # fewer values than include_fields
	assert CalendarSource._zip_rows(rows, EARNINGS_FIELDS) == [
		{"ticker": "AAPL", "companyshortname": "Apple"}
	]


# ---- pagination ----

def test_paginates_until_short_page():
	full = _payload([_row(f"S{i}") for i in range(cs.PAGE_SIZE)])
	data = FakeData([full, _payload([_row("TAIL")])])
	src = _source(data)

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": EVENT_CFG},
	})

	assert len(events) == cs.PAGE_SIZE + 1
	assert events[-1]["ticker"] == "TAIL"
	assert [(body["offset"]) for _, _, body in data.calls] == [0, cs.PAGE_SIZE]


def test_max_pages_cap():
	full = _payload([_row(f"S{i}") for i in range(cs.PAGE_SIZE)])
	data = FakeData([full])
	src = _source(data)

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": EVENT_CFG},
	})

	assert len(data.calls) == cs.MAX_PAGES
	assert len(events) == cs.PAGE_SIZE * cs.MAX_PAGES


# ---- sweeps ----

def test_empty_regions_means_one_global_sweep(monkeypatch):
	data = FakeData([_payload([_row("AAPL")])])
	src = _source(data)
	cfg = dict(EVENT_CFG, regions=[])

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"econ": cfg},
	})

	assert len(data.calls) == 1
	assert events[0]["_region"] is None


def test_sweep_failure_does_not_kill_other_regions():
	data = FakeData([
		{"finance": {"error": {"code": "Bad Request", "description": "nope"}}},
		_payload([_row("HSBA")]),
	])
	src = _source(data)
	gb_cfg = dict(EVENT_CFG, regions=["us", "gb"])

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": gb_cfg},
	})

	assert len(events) == 1
	assert events[0]["_region"] == "gb"


def test_rate_limit_retries_then_succeeds(monkeypatch):
	monkeypatch.setattr(cs.time, "sleep", lambda s: None)
	data = FakeData([_payload([_row("AAPL")])])
	attempts = {"n": 0}
	original_post = data.post

	def flaky_post(*args, **kwargs):
		attempts["n"] += 1
		if attempts["n"] == 1:
			raise YFRateLimitError()
		return original_post(*args, **kwargs)

	data.post = flaky_post
	src = _source(data)

	events = src.fetch({
		"window_start": "2026-11-02",
		"window_end": "2026-11-16",
		"event_types": {"earnings": EVENT_CFG},
	})

	assert attempts["n"] == 2
	assert len(events) == 1
