from datetime import date, timedelta

from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_statement_rows
from lib.transforms.statements import group_statement_records
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import (
	get_quarterly_fetch_ids, get_stamped_stock_ids, get_fresh_stock_ids,
	get_stock_ids_with_annual, touch_statement_rows, RowFlusher,
)
from constants.pipeline import (
	EARNINGS_EVENT_LOOKAHEAD_DAYS, MAX_SUPPRESSION_GAP_DAYS, QUARTERLY_FISCAL_WINDOW_DAYS,
	QUARTERLY_SWEEP_BUCKETS, QUARTERLY_SWEEP_WINDOW_DAYS, QUARTERLY_STAGGER_BUCKETS,
)
import constants.db_tables as dbt
from .context import valid_symbols


# Newest annual fiscal_date must be at least this recent for a symbol to count
# as "has current data" (~covers FY ending last year without one 400+ days old).
FRESH_FISCAL_WINDOW_DAYS = 380

# Tables scanned together for the cross-table quarterly staleness gap.
QUARTERLY_STATEMENT_TABLES = [dbt.balance_sheet, dbt.cash_flow, dbt.income_statement]

# Streaming flush size for statement upserts: conflict on the natural key so
# restated figures DO UPDATE instead of being dropped as duplicates.
STATEMENT_FLUSH_SIZE = 2000
STATEMENT_CONFLICT_KEYS = ["stock_id", "fiscal_date", "period"]


def fresh_symbols(ctx, db_table: str, targets: list[str], period_type: str) -> set[str]:
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
	printf(f"{db_table} ({period_type}): {skipped}/{len(targets)} symbols stale/unknown -> fetch", lv.INFO)
	return fresh


def quarterly_fetch_decision(
	gap_days: int | None, next_event_days_out: int | None, swept: bool = False,
	staggered: bool = False,
) -> bool:
	'''True = fetch quarterly statement data for the symbol.

	Pure counterpart of the SQL in get_quarterly_fetch_ids.

	gap_days: today - newest fiscal_date across the three statement tables.
		None = no rows at all -> unknown -> fetch (COALESCE fallback).
	next_event_days_out: days until the nearest known future earnings event.
		None = no known event -> gap-trigger fallback.
	swept: symbol is in today's revision-sweep shard (stock_id mod N == day
		bucket). Sweep overrides suppression and the fresh window for known
		rows within the sweep window.
	staggered: symbol is in today's stagger shard for stale-and-not-suppressed
		symbols with no calendar signal (they would otherwise fetch daily).

	Fetch iff (swept AND gap known AND gap <= sweep window) OR (unknown gap)
	OR (stale AND NOT suppressed AND staggered):
	- swept and gap <= QUARTERLY_SWEEP_WINDOW_DAYS -> fetch (restatement check);
	- fresh (gap <= QUARTERLY_FISCAL_WINDOW_DAYS) -> no fetch;
	- suppressed (event beyond lookahead AND gap < MAX_SUPPRESSION_GAP_DAYS)
		-> no fetch (dead-fetch elimination);
	- unknown gap (no rows at all) -> fetch immediately, never staggered;
	- everything else -> fetch only when today's stagger shard hits:
		no event, event within lookahead, event postponed until near-term,
		or gap too old for suppression to be safe.
	'''
	gap = gap_days if gap_days is not None else 999_999	# unknown -> maximally stale
	if swept and gap_days is not None and gap <= QUARTERLY_SWEEP_WINDOW_DAYS:
		return True	# sweep shard: revision-prone rows, check for restatements
	if gap <= QUARTERLY_FISCAL_WINDOW_DAYS:
		return False	# fresh
	if next_event_days_out is not None and next_event_days_out > EARNINGS_EVENT_LOOKAHEAD_DAYS \
			and gap < MAX_SUPPRESSION_GAP_DAYS:
		return False	# suppressed: known far-future earnings, data not too old
	if gap_days is None:
		return True	# no rows at all -> first fetch, always immediate
	return staggered


def quarterly_targets(ctx, db_table: str, targets: list[str], period_type: str) -> list[str]:
	'''Quarterly fetch targets: stale-and-not-suppressed symbols in today's
	stagger shard, today's revision-sweep shard, legacy NULL-stamp rows in
	this table (refetched and stamped once), and never-fetched symbols.'''
	stock_ids = [ctx.stock_ids[s] for s in targets]
	sweep_bucket = date.today().toordinal() % QUARTERLY_SWEEP_BUCKETS
	fetch_ids, reasons = get_quarterly_fetch_ids(
		QUARTERLY_STATEMENT_TABLES, stock_ids, sweep_bucket,
	)
	stamped_ids = get_stamped_stock_ids(db_table, stock_ids)
	needed = [
		s for s in targets
		if ctx.stock_ids[s] in fetch_ids or ctx.stock_ids[s] not in stamped_ids
	]
	reason_txt = ", ".join(f"{k}={v}" for k, v in sorted(reasons.items()))
	printf(
		f"{db_table} ({period_type}): {len(needed)}/{len(targets)} symbols stale/unknown "
		f"-> fetch (sweep shard {sweep_bucket}/{QUARTERLY_SWEEP_BUCKETS}: {reason_txt})",
		lv.INFO,
	)
	return needed


def run_statements(ctx, finance_type: str, db_table: str, null_tolerance: float, period_type: str = "annual"):
	'''One statement kind: balance_sheet | cash_flow | income_statement.

	period_type selects the fetch strategy: "annual" uses the 380-day window
	per table; "quarterly" uses the calendar-suppressed staleness window and
	fetches quarterly payloads for stale-and-not-suppressed symbols only.
	'''
	yfs = ctx.yfs
	targets = valid_symbols(ctx)
	phase_name = finance_type if period_type == "annual" else f"{finance_type}_{period_type}"
	stats = new_phase(phase_name, len(targets))

	force = getattr(ctx.args, "force", False)
	full = getattr(ctx.args, "full", False)
	skipped_symbols: list[str] = []

	if force or full:
		printf(f"{finance_type}: {'force' if force else 'full'} set, fetching all symbols", lv.INFO)
		needed = targets
	elif period_type == "annual":
		fresh = fresh_symbols(ctx, db_table, targets, period_type)
		needed = [s for s in targets if s not in fresh]
		skipped_symbols = sorted(fresh)
		stats["skipped_fresh"] = len(fresh)
	else:
		needed = quarterly_targets(ctx, db_table, targets, period_type)
		skipped_symbols = [s for s in targets if s not in needed]
		stats["skipped_fresh"] = len(skipped_symbols)

	def yf_records(sym):
		return yfs.statements_payload(sym, finance_type, period_type)

	grouped = yfs.map_symbols(yf_records, needed, finance_type) if needed else {}

	flusher = RowFlusher(
		db_table,
		STATEMENT_FLUSH_SIZE,
		conflict_keys=STATEMENT_CONFLICT_KEYS,
		null_tolerance=null_tolerance,
	)

	no_q_symbols: list[str] = []		# quarterly fetch ok, but payload empty

	for symbol in needed:
		records = grouped.get(symbol)
		if records is None:
			if period_type == "quarterly":
				# Empty quarterly payload: could be a fetch failure OR a
				# half-yearly reporter (HK/LSE/Swiss) with no quarterly data
				# at all. Resolved below via annual-row existence check.
				no_q_symbols.append(symbol)
			else:
				count_symbol(stats, False, symbol)
			continue
		printf(f"---- {symbol:<10} {finance_type} {period_type} ----", lv.INFO)
		rows = build_statement_rows(symbol, ctx.stock_ids[symbol], records, period_type, finance_type)
		flusher.add(rows)
		# Stamp even when every row was a duplicate (rows=0): the fetch
		# happened, so the freshness check must treat the symbol as fresh.
		# Unstamped legacy rows would otherwise trigger a refetch every run.
		if rows:
			touch_statement_rows(db_table, [ctx.stock_ids[symbol]])
		count_symbol(stats, True)

	# No-quarterly resolution: annual rows present -> the company simply does
	# not report quarterly; count as skip (ok). No annual rows either -> the
	# fetch itself failed; count as failure.
	if no_q_symbols:
		annual_ids = get_stock_ids_with_annual(db_table, [ctx.stock_ids[s] for s in no_q_symbols])
		no_q_skipped = [s for s in no_q_symbols if ctx.stock_ids[s] in annual_ids]
		for symbol in no_q_skipped:
			stats["skipped_no_q"] = stats.get("skipped_no_q", 0) + 1
			count_symbol(stats, True)
		for symbol in no_q_symbols:
			if ctx.stock_ids[symbol] not in annual_ids:
				count_symbol(stats, False, symbol)
		# Touch annual rows so half-yearly reporters are not re-targeted as
		# unstamped every single day (fetch only re-fires when annual stale).
		if not force and no_q_skipped:
			skipped_symbols.extend(no_q_skipped)

	stats["rows_written"] = flusher.finish()

	# Skipped symbols (fresh / suppressed): bump updated_at so the staleness
	# clock restarts and legacy NULL stamps migrate to stamped
	if not force and skipped_symbols:
		touch_statement_rows(db_table, [ctx.stock_ids[s] for s in skipped_symbols])

	return stats
