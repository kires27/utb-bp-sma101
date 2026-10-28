from datetime import date, timedelta

from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_statement_rows
from lib.transforms.statements import group_statement_records
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_fresh_stock_ids, get_stamped_stock_ids, insert_data_statement, touch_statement_rows
from .context import valid_us, valid_intl


# Newest annual fiscal_date must be at least this recent for a symbol to count
# as "has current data" (~covers FY ending last year without one 400+ days old).
FRESH_FISCAL_WINDOW_DAYS = 380


def fresh_symbols(ctx, db_table: str, targets: list[str]) -> set[str]:
	'''Symbols whose statement data is fresh enough to skip fetching.

	Fresh = newest fiscal_date within FRESH_FISCAL_WINDOW_DAYS AND rows carry an
	updated_at stamp (NULL stamps = legacy rows, treated as stale so they get
	refetched and stamped once).
	'''
	stock_ids = [ctx.stock_ids[s] for s in targets]
	fiscal_cutoff = date.today() - timedelta(days=FRESH_FISCAL_WINDOW_DAYS)
	fresh_ids = get_fresh_stock_ids(db_table, stock_ids, fiscal_cutoff)
	stamped_ids = get_stamped_stock_ids(db_table, stock_ids)
	fresh = {s for s in targets if ctx.stock_ids[s] in fresh_ids and ctx.stock_ids[s] in stamped_ids}
	skipped = len(targets) - len(fresh)
	printf(f"{db_table}: {skipped}/{len(targets)} symbols stale/unknown -> fetch", lv.INFO)
	return fresh


def run_statements(ctx, finance_type: str, db_table: str, null_tolerance: float):
	'''One statement kind: balance_sheet | cash_flow | income_statement. Annual only.'''
	yfs = ctx.yfs
	period_type = "annual"
	stats = new_phase(finance_type, len(valid_us(ctx)) + len(valid_intl(ctx)))

	force = getattr(ctx.args, "force", False)

	us_targets = valid_us(ctx)
	intl_targets = valid_intl(ctx)

	if force:
		printf(f"{finance_type}: --force set, fetching all symbols", lv.INFO)
		us_needed, intl_needed = us_targets, intl_targets
	else:
		fresh = fresh_symbols(ctx, db_table, us_targets + intl_targets)
		us_needed = [s for s in us_targets if s not in fresh]
		intl_needed = [s for s in intl_targets if s not in fresh]
		stats["skipped_fresh"] = len(fresh)

	grouped_us = {
		symbol: group_statement_records(records)
		for symbol, records in ctx.ds.statements(us_needed, finance_type, period_type).items()
	} if us_needed else {}

	def yf_records(sym):
		return yfs.statements_payload(sym, finance_type, period_type)

	grouped_intl = yfs.map_symbols(yf_records, intl_needed, finance_type) if intl_needed else {}

	for grouped, targets in ((grouped_us, us_needed), (grouped_intl, intl_needed)):
		for symbol in targets:
			records = grouped.get(symbol)
			if records is None:
				count_symbol(stats, False, symbol)
				continue
			printf(f"---- {symbol} {finance_type} ----", lv.INFO)
			rows = build_statement_rows(symbol, ctx.stock_ids[symbol], records, period_type, finance_type)
			written = insert_data_statement(rows, db_table, null_tolerance=null_tolerance)
			# Stamp even when every row was a duplicate (rows=0): the fetch
			# happened, so the freshness check must treat the symbol as fresh.
			# Unstamped legacy rows would otherwise trigger a refetch every run.
			if rows:
				touch_statement_rows(db_table, [ctx.stock_ids[symbol]])
			count_symbol(stats, True, rows=written)

	# Fresh symbols skipped: bump updated_at so their staleness clock restarts
	# without refetching.
	if not force and stats.get("skipped_fresh"):
		fresh_ids = [ctx.stock_ids[s] for s in us_targets + intl_targets if s in fresh]
		touch_statement_rows(db_table, fresh_ids)

	return stats
