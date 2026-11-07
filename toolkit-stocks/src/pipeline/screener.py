'''Screener discovery: YAML config -> EquityQuery -> paginated screen().

Design (PLAN-rewrite-toolkit.md, discovery section):
- Config maps 1:1 onto the screener vocabulary. Operators are a closed set
  (eq, is-in, btwn, gt, lt, gte, lte, and, or); fields/values validated
  against yfinance's own maps. Unknown fields/operators/values fail loudly
  at startup (ValueError) — never run with a half-understood universe.
- screen() paginates at PAGE_SIZE (250/page, API limit).
- Discovery is insert-only: new symbols go into `stock` (ON CONFLICT DO
  NOTHING); existing symbols untouched. Returns the new symbols = backfill
  queue for the current run.
'''
import os
from collections.abc import Iterable

import yaml
from yfinance import EquityQuery, screener

import constants.db_tables as dbt
from lib.functions.netstats import incr_yf
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_symbols, RowFlusher

PAGE_SIZE = 250
NEW_FLUSH_SIZE = 500

CONFIG_PATH = os.path.normpath(
	os.path.join(os.path.dirname(__file__), "..", "data", "screener.yml")
)

# Fields with a closed value set in the screener vocabulary.
EQ_VALUE_FIELDS = ("region", "exchange", "sector", "industry", "peer_group")

# Composite operators take EquityQuery children, leaves take [field, *values].
COMPOSITE_OPS = ("and", "or")
LEAF_OPS = ("eq", "is-in", "btwn", "gt", "lt", "gte", "lte")


def _flatten(value) -> set:
	'''Recursively flatten nested dicts/lists/sets into a flat set of leaves.
	Handles the map's mixed shapes: region is aliased to exchange dict_keys,
	exchange/industry are dicts of sets, sector/peer_group are plain sets.'''
	if isinstance(value, dict):
		flat = set()
		for sub in value.values():
			flat.update(_flatten(sub))
		return flat
	if isinstance(value, (list, set)):
		flat = set()
		for sub in value:
			flat.update(_flatten(sub))
		return flat
	if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
		# dict_keys (region is aliased to exchange keys) and other iterables
		flat = set()
		for sub in value:
			flat.update(_flatten(sub))
		return flat
	return {value}


def _eq_map() -> dict[str, set]:
	'''Screener field -> allowed values, normalized from EQUITY_SCREENER_EQ_MAP.'''
	from yfinance.const import EQUITY_SCREENER_EQ_MAP

	return {field: _flatten(values) for field, values in EQUITY_SCREENER_EQ_MAP.items()}


def _field_names() -> set[str]:
	'''All screener field names across EQUITY_SCREENER_FIELDS groups.'''
	from yfinance.const import EQUITY_SCREENER_FIELDS

	fields = set()
	for group in EQUITY_SCREENER_FIELDS.values():
		fields.update(group if isinstance(group, (list, set)) else group.keys())
	return fields


def _validate_leaf(op: str, field: str, values: list):
	'''Fail loudly on unknown fields or invalid eq/is-in values.'''
	if field not in _field_names():
		raise ValueError(f"Unknown screener field '{field}'")
	if op in ("eq", "is-in") and field in EQ_VALUE_FIELDS:
		allowed = _eq_map().get(field, set())
		for value in values:
			if value not in allowed:
				raise ValueError(f"Invalid {field} value '{value}'")


def _build_leaf(op: str, field: str, value) -> EquityQuery:
	'''One leaf condition -> EquityQuery([field, *values]).'''
	if op == "btwn":
		if not isinstance(value, list) or len(value) != 2:
			raise ValueError(f"btwn needs a 2-value list: {{btwn: [lo, hi]}}")
		try:
			values = [float(v) for v in value]  # EquityQuery validates Real
		except (TypeError, ValueError):
			raise ValueError(f"btwn needs numeric bounds, got {value}")
	elif op == "is-in":
		if not isinstance(value, list) or not value:
			raise ValueError(f"is-in needs a non-empty list for field '{field}'")
		values = value
	else:  # eq, gt, lt, gte, lte
		if isinstance(value, list):
			raise ValueError(f"'{op}' takes one value, got a list for field '{field}'")
		values = [value]

	_validate_leaf(op, field, values)
	return EquityQuery(op, [field, *values])


def build_query(condition) -> EquityQuery:
	'''YAML condition -> EquityQuery. Accepts nested and/or composites.'''
	if not isinstance(condition, dict) or len(condition) != 1:
		raise ValueError(f"Condition must be a single-key mapping: {condition}")

	key, value = next(iter(condition.items()))
	if key in COMPOSITE_OPS:
		if not isinstance(value, list) or len(value) < 2:
			raise ValueError(f"'{key}' needs a list of 2+ conditions: {condition}")
		return EquityQuery(key, [build_query(child) for child in value])

	if isinstance(value, dict):
		if len(value) != 1:
			raise ValueError(f"Field '{key}' must map to exactly one operator: {value}")
		op, op_value = next(iter(value.items()))
		if op not in LEAF_OPS:
			raise ValueError(f"Unknown operator '{op}' for field '{key}'")
		return _build_leaf(op, key, op_value)

	return _build_leaf("is-in" if isinstance(value, list) else "eq", key, value)


def load_queries(config_path: str = CONFIG_PATH) -> list[tuple[str, EquityQuery]]:
	'''Parse the YAML config into (name, EquityQuery) pairs. Fails loudly.'''
	with open(config_path) as fh:
		config = yaml.safe_load(fh)

	universe = (config or {}).get("universe")
	if not universe:
		raise ValueError(f"{config_path}: no 'universe' entries defined")

	queries = []
	for i, entry in enumerate(universe):
		name = entry.get("name") if isinstance(entry, dict) else None
		if not name:
			raise ValueError(f"{config_path}: universe entry {i} missing 'name'")
		conditions = entry.get("conditions") or []
		if not conditions:
			raise ValueError(f"{config_path}: query '{name}' has no conditions")
		if not isinstance(conditions, list) or len(conditions) < 1:
			raise ValueError(f"{config_path}: query '{name}' needs a list of conditions")
		queries.append((name, build_query({"and": conditions}) if len(conditions) > 1 else build_query(conditions[0])))
	return queries


def screen_all(query: EquityQuery) -> list[dict]:
	'''Paginate screener.screen() at PAGE_SIZE until total is collected.'''
	quotes: list[dict] = []
	offset = 0
	while True:
		incr_yf()
		page = screener.screen(query, size=PAGE_SIZE, offset=offset)
		page_quotes = page.get("quotes") or []
		quotes.extend(page_quotes)
		total = page.get("total") or 0
		offset += len(page_quotes)
		if not page_quotes or offset >= total:
			break
	return quotes


def _stock_row(quote: dict) -> dict:
	'''Minimal stock row from a screener quote. Insert-only, no upsert.'''
	from datetime import datetime, timezone

	row = {
		"symbol": quote.get("symbol"),
		"maintenance_update": datetime.now(timezone.utc),
	}
	name = quote.get("longName") or quote.get("shortName")
	if name:
		row["name"] = name
	if quote.get("fullExchangeName"):
		row["exchange"] = quote["fullExchangeName"]
	return row


def discover(config_path: str = CONFIG_PATH) -> dict:
	'''Run every query in the config, diff against DB, insert-only new symbols.

	Returns {queries, screened, new_symbols} — new_symbols is the backfill
	queue the caller (backfill run mode) ingests with full history.
	'''
	stats = {"queries": 0, "screened": 0, "new_symbols": []}

	seen: dict[str, dict] = {}
	for name, query in load_queries(config_path):
		stats["queries"] += 1
		quotes = screen_all(query)
		printf(f"query '{name}': {len(quotes)} symbols", lv.INFO)
		for quote in quotes:
			symbol = quote.get("symbol")
			if symbol and symbol not in seen:
				seen[symbol] = quote

	stats["screened"] = len(seen)
	existing = set(get_symbols())
	new_quotes = [q for sym, q in seen.items() if sym not in existing]
	stats["new_symbols"] = [q["symbol"] for q in new_quotes]

	if new_quotes:
		rows = [_stock_row(q) for q in new_quotes]
		flusher = RowFlusher(dbt.stock, NEW_FLUSH_SIZE)
		flusher.add(rows)
		written = flusher.finish()
		printf(f"screener: {len(seen)} screened, {written} new -> stock", lv.INFO)
	else:
		printf(f"screener: {len(seen)} screened, 0 new", lv.INFO)

	return stats
