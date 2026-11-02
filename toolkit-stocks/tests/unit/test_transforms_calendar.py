'''build_calendar_rows: raw calendar events -> stock_economic_calendar rows.
Natural-key sentinels (symbol/event_name never NULL), stock_id enrichment,
raw passthrough as json string.'''
import json
from datetime import datetime, timezone

from lib.transforms.calendar import build_calendar_rows


def _earnings(**overrides):
	event = {
		"ticker": "AAPL",
		"companyshortname": "Apple",
		"intradaymarketcap": 3.4e12,
		"eventname": "Q3 2026 Earnings",
		"startdatetime": "2026-11-04T12:30:00.000Z",
		"startdatetimetype": "AM",
		"epsestimate": 1.6,
		"epsactual": None,
		"epssurprisepct": None,
		"_event_type": "earnings",
		"_region": "us",
	}
	event.update(overrides)
	return event


def _econ(**overrides):
	event = {
		"econ_release": "Nonfarm Payrolls",
		"country_code": "US",
		"startdatetime": "2026-11-06T13:30:00.000Z",
		"period": "Oct 2026",
		"after_release_actual": None,
		"consensus_estimate": "150K",
		"prior_release_actual": "120K",
		"originally_reported_actual": None,
		"_event_type": "economic_event",
		"_region": None,
	}
	event.update(overrides)
	return event


# ---- earnings events ----

def test_earnings_row_shape():
	rows = build_calendar_rows([_earnings()], {"AAPL": 42})

	assert len(rows) == 1
	row = rows[0]
	assert row["event_type"] == "earnings"
	assert row["symbol"] == "AAPL"
	assert row["stock_id"] == 42
	assert row["region"] == "us"
	assert row["event_name"] == "Q3 2026 Earnings"
	assert row["event_datetime"] == datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc)
	assert row["timing"] == "AM"
	assert row["country_code"] is None
	assert row["period"] is None


def test_eps_fields_stay_in_raw_only():
	row = build_calendar_rows([_earnings()])[0]
	raw = json.loads(row["raw"])
	assert raw["epsestimate"] == 1.6
	for col in ("eps_estimate", "eps_actual", "eps_surprise_pct"):
		assert col not in row


def test_unknown_symbol_keeps_null_stock_id():
	row = build_calendar_rows([_earnings(ticker="NOPE")], {"AAPL": 42})[0]
	assert row["stock_id"] is None


# ---- economic events ----

def test_econ_row_uses_sentinel_symbol():
	rows = build_calendar_rows([_econ()], {"AAPL": 42})

	row = rows[0]
	assert row["event_type"] == "economic_event"
	assert row["symbol"] == ""  # sentinel: NULL would defeat the unique key
	assert row["stock_id"] is None
	assert row["event_name"] == "Nonfarm Payrolls"
	assert row["country_code"] == "US"
	assert row["period"] == "Oct 2026"
	assert row["timing"] is None


def test_econ_region_falls_back_to_country_code():
	# global sweep (_region None): region derived from the event's country
	row = build_calendar_rows([_econ()])[0]
	assert row["region"] == "us"


def test_econ_region_falls_back_to_global_without_country():
	row = build_calendar_rows([_econ(country_code=None)])[0]
	assert row["region"] == "global"


# ---- robustness ----

def test_missing_datetime_dropped():
	assert build_calendar_rows([_earnings(startdatetime=None)]) == []


def test_bad_datetime_dropped():
	assert build_calendar_rows([_earnings(startdatetime="not-a-date")]) == []


def test_unknown_event_type_dropped():
	assert build_calendar_rows([_earnings(_event_type="ipo_info")]) == []


def test_missing_event_name_becomes_sentinel():
	row = build_calendar_rows([_earnings(eventname=None)])[0]
	assert row["event_name"] == ""


def test_updated_at_is_stamped_per_row():
	before = datetime.now(timezone.utc)
	row = build_calendar_rows([_earnings()])[0]
	assert before <= row["updated_at"] <= datetime.now(timezone.utc)


# ---- dedupe ----

def test_duplicate_conflict_keys_deduped():
	# Yahoo sweeps repeat the same event across pages/sweeps; the upsert
	# conflict key must appear at most once per batch.
	dup = _earnings()
	rows = build_calendar_rows([dup, _earnings(), _econ(), _econ()])

	assert len(rows) == 2
	assert {r["event_type"] for r in rows} == {"earnings", "economic_event"}


def test_dedupe_keeps_first_occurrence():
	first = _earnings(epsestimate=1.6)
	second = _earnings(epsestimate=9.9)  # stale/same key, different payload
	rows = build_calendar_rows([first, second])

	assert len(rows) == 1
	assert json.loads(rows[0]["raw"])["epsestimate"] == 1.6


def test_dedupe_treats_different_keys_as_distinct():
	# same symbol+datetime but different event_name -> both kept
	rows = build_calendar_rows([
		_earnings(eventname="Q3 2026 Earnings"),
		_earnings(eventname="Q4 2026 Earnings"),
	])
	assert len(rows) == 2
