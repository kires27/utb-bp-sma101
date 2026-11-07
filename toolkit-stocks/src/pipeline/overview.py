import json
from datetime import datetime, timezone

from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_overview_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import (
	get_stock_overview_rows, get_stale_stock_ids, insert_data_statement,
)
import constants.db_tables as dbt
from constants.pipeline import OVERVIEW_MAX_AGE_DAYS
from .context import refresh_ids

# Never diffed: maintenance_update is the freshness stamp itself (moves only
# on a real change), and logo is always None on the fetched side (the old
# suppress trigger never compared it either).
DIFF_SKIP_KEYS = {"maintenance_update", "logo"}


def _differs(new, old) -> bool:
	'''True when the fetched overview value differs from the stored one.
	Handles type quirks of the Postgres round-trip: numeric columns come
	back as Decimal, jsonb (key_executives) comes back as a list while the
	fetched side carries a JSON string.'''
	if isinstance(new, (int, float)) or isinstance(old, (int, float)):
		try:
			return float(new) != float(old)
		except (TypeError, ValueError):
			pass
	if isinstance(new, str) and isinstance(old, (list, dict)):
		try:
			new = json.loads(new)
		except ValueError:
			return True
	elif isinstance(old, str) and isinstance(new, (list, dict)):
		try:
			old = json.loads(old)
		except ValueError:
			return True
	return new != old


def run_overview(ctx):
	yfs = ctx.yfs
	stats = new_phase("overview", len(ctx.symbols))

	force = getattr(ctx.args, "force", False)
	full = getattr(ctx.args, "full", False)
	targets = ctx.symbols
	if not force and not full:
		# Fresh = maintenance_update within OVERVIEW_MAX_AGE_DAYS (overview
		# only writes rows whose cells changed -> recent stamp = profile
		# already synced).
		stale_ids = get_stale_stock_ids(
			[ctx.stock_ids[s] for s in targets if ctx.stock_ids.get(s) is not None],
			OVERVIEW_MAX_AGE_DAYS,
		)
		targets = [s for s in targets if ctx.stock_ids.get(s) in stale_ids]
		stats["skipped_fresh"] = len(ctx.symbols) - len(targets)
		printf(f"overview: {len(targets)}/{len(ctx.symbols)} symbols stale -> fetch", lv.INFO)
	else:
		printf(f"overview: {'force' if force else 'full'} set, fetching all symbols", lv.INFO)

	# Stored rows for change detection: identical profiles are skipped before
	# any write, changed ones are written as a partial update (changed cells
	# + fresh stamp only).
	existing_rows = get_stock_overview_rows(
		[ctx.stock_ids[s] for s in targets if ctx.stock_ids.get(s) is not None]
	)

	def yf_profile(sym):
		return yfs.profile(sym)

	infos = yfs.map_symbols(yf_profile, targets, "overview")
	rows = []
	for symbol, info in infos.items():
		row = build_overview_row(symbol, info, None, ctx.symbol_meta.get(symbol, {}) or {}, info)
		if not row.get("name"):
			printf(f"{symbol:<10}: no name resolved, skipping overview row", lv.WARNING)
			count_symbol(stats, False, symbol)
			continue
		rows.append(row)

	for row in rows:
		if not row:
			continue
		symbol = row["symbol"]
		existing = existing_rows.get(symbol)
		if existing is not None:
			changed = {
				k: v for k, v in row.items()
				if k not in DIFF_SKIP_KEYS and _differs(v, existing.get(k))
			}
			if not changed:
				stats["skipped_unchanged"] = stats.get("skipped_unchanged", 0) + 1
				continue
			row = {**changed, "symbol": symbol, "maintenance_update": datetime.now(timezone.utc)}
		mode_condition = {} if ctx.stock_ids.get(symbol) is None else {"symbol": symbol}
		rows_written = insert_data_statement(row, dbt.stock, update_condition=mode_condition, label=symbol)
		count_symbol(stats, True, rows=rows_written)

	refresh_ids(ctx)
	return stats
