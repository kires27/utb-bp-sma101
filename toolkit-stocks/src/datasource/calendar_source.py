'''Yahoo v1/finance/visualization calendar source (earnings + economic events).

Bypasses yf.Calendars: its wrapper hardcodes the region operand to "us", while
the endpoint accepts a region query operand (verified for gb/jp/de). We reuse
the exact request shape of yfinance.calendars.Calendars._get_data but swap the
region operand, so a single paginated sweep per (region, type) replaces
thousands of per-symbol yf.Ticker(...).calendar calls.

Response rows carry no field names -- values align with the includeFields
request order, so rows are zipped back to internal field names here. Label
parsing (incl. the duplicate "Event Start Date" STRING -> "Timing" quirk) is
avoided entirely. No DB writes.
'''
import time
import traceback

from lib.module.printf import printf, level as lv


PAGE_SIZE = 100   # Yahoo caps size at 100
MAX_PAGES = 10    # per (region, type) sweep; largest caps sort first
MAX_RETRIES = 4
CALENDAR_URL = "https://query1.finance.yahoo.com/v1/finance/visualization"


class CalendarSource:
	'''
	Paginated POST sweep over the visualization endpoint. One request per
	page of <=100 events per (region, event type). Returns raw event dicts
	keyed by the includeFields names, each stamped with _event_type and
	_region for the transform.
	'''

	def __init__(self):
		from yfinance.data import YfData

		self._data = YfData()

	def _fetch_page(self, event_cfg: dict, region: str | None, start: str, end: str, offset: int) -> list[dict]:
		'''Raw rows (keyed by includeFields names) for one page, with backoff on rate limits.'''
		import yfinance as yf
		from yfinance.exceptions import YFRateLimitError

		operands = [
			{"operator": "GTE", "operands": ["startdatetime", start]},
			{"operator": "LTE", "operands": ["startdatetime", end]},
		]
		if region:
			operands.append({"operator": "EQ", "operands": ["region", region]})
		body = {
			"sortType": event_cfg.get("sort_type", "DESC"),
			"entityIdType": event_cfg["entity_id_type"],
			"sortField": event_cfg["sort_field"],
			"includeFields": event_cfg["include_fields"],
			"size": PAGE_SIZE,
			"offset": offset,
			"query": {"operator": "AND", "operands": operands},
		}

		for attempt in range(MAX_RETRIES):
			try:
				resp = self._data.post(CALENDAR_URL, params={"lang": "en-US"}, body=body)
				json_data = resp.json()
				error = json_data.get("finance", {}).get("error")
				if error:
					raise ValueError(f"Yahoo calendar error: {error}")
				return self._zip_rows(json_data, event_cfg["include_fields"])
			except YFRateLimitError as err:
				wait = 2 ** attempt
				printf(f"calendar: rate limited, retry in {wait}s ({err})", lv.WARNING)
				time.sleep(wait)
		printf(f"calendar: giving up after {MAX_RETRIES} retries (offset {offset})", lv.ERROR)
		return []

	@staticmethod
	def _zip_rows(json_data: dict, include_fields: list[str]) -> list[dict]:
		'''finance.result[0].documents[0].rows -> dicts keyed by includeFields names.
		Rows align with the request's includeFields order; a short row keeps its
		prefix (zip truncates).'''
		docs = json_data.get("finance", {}).get("result", [{}])[0].get("documents", [{}])
		rows = docs[0].get("rows") or []
		return [dict(zip(include_fields, row)) for row in rows]

	def fetch(self, config: dict) -> list[dict]:
		'''All events for the config's window across event types and regions.
		Empty regions list = one global sweep. Each event dict is stamped with
		_event_type and _region (None for global sweeps).'''
		start = config["window_start"]
		end = config["window_end"]
		events: list[dict] = []
		for type_name, event_cfg in config["event_types"].items():
			regions = event_cfg.get("regions") or [None]
			for region in regions:
				try:
					swept = self._sweep(event_cfg, region, start, end)
				except Exception as err:
					tb = traceback.extract_tb(err.__traceback__)[-1]
					printf(f"calendar {type_name}/{region} sweep failed: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
					continue
				for event in swept:
					event["_event_type"] = type_name
					event["_region"] = region
				events.extend(swept)
				printf(f"calendar: {type_name}/{region}: {len(swept)} events", lv.INFO)
		printf(f"calendar: {len(events)} events fetched", lv.INFO)
		return events

	def _sweep(self, event_cfg: dict, region: str | None, start: str, end: str) -> list[dict]:
		'''Paginate one (region, type) until a short page or MAX_PAGES.'''
		rows: list[dict] = []
		for page in range(MAX_PAGES):
			page_rows = self._fetch_page(event_cfg, region, start, end, offset=page * PAGE_SIZE)
			rows.extend(page_rows)
			if len(page_rows) < PAGE_SIZE:
				break
		return rows
