'''Normalized calendar events -> stock_economic_calendar rows.

EPS fields (epsestimate/epsactual/epssurprisepct and the economic actual/
estimate columns) have no dedicated columns -- they stay inside `raw` jsonb.

Sentinels: symbol and event_name are NOT NULL (they form the natural key
alongside event_type + event_datetime, and NULL would defeat the unique
constraint). Missing values become '' so upsert conflict detection works.
'''
import json
import traceback
from datetime import datetime, timezone

from lib.module.printf import printf, level as lv


def _parse_datetime(value) -> datetime | None:
	'''ISO 8601 ("2026-11-04T12:30:00.000Z") -> aware datetime.'''
	if not value:
		return None
	try:
		return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
	except (TypeError, ValueError):
		return None


def _text(value) -> str | None:
	'''None -> None (dropped), everything else -> stripped string or ''.'''
	if value is None:
		return None
	return str(value).strip()


KNOWN_EVENT_TYPES = ("earnings", "economic_event")


def build_calendar_rows(events: list[dict], stock_ids: dict[str, int] | None = None) -> list[dict]:
	'''
	events: raw dicts from CalendarSource (includeFields keys + _event_type/_region).
	stock_ids: symbol -> stock.id for enrichment; unknown symbols keep NULL.
	Returns DB rows for upsert on (event_type, symbol, event_datetime, event_name).
	'''
	stock_ids = stock_ids or {}
	try:
		rows = []
		for event in events:
			event_type = event.get("_event_type")
			if event_type not in KNOWN_EVENT_TYPES:
				continue  # defensive: source config decides what is fetched
			dt = _parse_datetime(event.get("startdatetime"))
			if dt is None:
				continue

			if event_type == "earnings":
				symbol = _text(event.get("ticker")) or ""
				event_name = _text(event.get("eventname")) or ""
				timing = _text(event.get("startdatetimetype"))
				country_code = None
				period = None
			else:
				# economic events are keyed by release name, not ticker
				symbol = ""
				event_name = _text(event.get("econ_release")) or ""
				timing = None
				country_code = _text(event.get("country_code"))
				period = _text(event.get("period"))

			region = event.get("_region")
			if region is None:
				# global sweep: fall back to the event's own country
				region = (country_code or "global").lower()

			rows.append({
				"event_type": event_type,
				"symbol": symbol,
				"stock_id": stock_ids.get(symbol) if symbol else None,
				"region": region,
				"event_name": event_name,
				"event_datetime": dt,
				"timing": timing,
				"country_code": country_code,
				"period": period,
				"raw": json.dumps(event, default=str),
				"updated_at": datetime.now(timezone.utc),
			})
		# Yahoo sweeps return duplicates (same event across pages/sweeps); the
		# upsert conflict key would hit the same row twice in one command and
		# fail with "cannot affect row a second time". Keep first occurrence.
		seen = set()
		deduped = []
		for row in rows:
			key = (row["event_type"], row["symbol"], row["event_datetime"], row["event_name"])
			if key in seen:
				continue
			seen.add(key)
			deduped.append(row)
		return deduped
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"build_calendar_rows: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []
