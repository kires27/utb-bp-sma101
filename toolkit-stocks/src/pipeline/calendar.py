'''Calendar phase: sweep Yahoo's earnings + economic event calendar into
stock_economic_calendar. Standalone (no RunContext) -- it is a universe-wide
reference feed, not per-symbol work. Mirrors exchange.py's shape.

Purpose: tier-2 optimizer for statement fetching -- announced earnings dates
let future runs fetch statements exactly when a company reports, on top of the
self-healing staleness-window gate. The table is also a data source on its own.
'''
import os
from datetime import datetime, timedelta, timezone

import yaml

from lib.module.printf import printf, level as lv
from lib.functions.stats import new_phase
from lib.supabase.sql_functions import get_stock_id_map, RowFlusher
from lib.transforms.calendar import build_calendar_rows
from datasource.calendar_source import CalendarSource
import constants.db_tables as dbt


CONFIG_PATH = os.path.normpath(
	os.path.join(os.path.dirname(__file__), "..", "data", "calendar.yml")
)

CONFLICT_KEYS = ["event_type", "symbol", "event_datetime", "event_name"]
FLUSH_SIZE = 1000


def load_config(path: str = CONFIG_PATH) -> dict:
	'''calendar.yml + derived UTC window (now -> now + window_days).'''
	with open(path, encoding="utf-8") as f:
		config = yaml.safe_load(f)
	window_days = int(config.get("window_days", 14))
	now = datetime.now(timezone.utc)
	config["window_start"] = now.strftime("%Y-%m-%d")
	config["window_end"] = (now + timedelta(days=window_days)).strftime("%Y-%m-%d")
	return config


def run_calendar(force: bool = False) -> dict:
	'''Sweep the calendar and upsert events. force is a no-op: the natural key
	makes every run an idempotent refresh.'''
	config = load_config()
	window_days = int(config.get("window_days", 14))
	# symbols_total = sweeps scheduled (regions x types)
	sweeps = sum(max(len(cfg.get("regions") or []), 1) for cfg in config["event_types"].values())
	stats = new_phase("calendar", sweeps)

	source = CalendarSource()
	events = source.fetch(config)
	if not events:
		printf("calendar: no events fetched", lv.WARNING)
		return stats

	rows = build_calendar_rows(events)
	symbols = sorted({r["symbol"] for r in rows if r["symbol"]})
	stock_ids = get_stock_id_map(symbols) if symbols else {}
	# second pass enriches stock_id now that ids are known
	for row in rows:
		if row["symbol"]:
			row["stock_id"] = stock_ids.get(row["symbol"])
	# only macro events + earnings for stocks we track; unknown-symbol earnings
	# belong to stocks not in DB (backfill adds them later, next sweep picks up)
	rows = [r for r in rows if not r["symbol"] or r["stock_id"] is not None]

	flusher = RowFlusher(dbt.economic_calendar, flush_size=FLUSH_SIZE, conflict_keys=CONFLICT_KEYS)
	flusher.add(rows)
	written = flusher.finish()
	printf(f"calendar: {written} rows written ({window_days}-day window)", lv.INFO)
	stats["symbols_ok"] = sweeps
	stats["rows_written"] = written
	return stats
