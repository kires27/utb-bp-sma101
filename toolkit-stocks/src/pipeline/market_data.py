import datetime as dt

from lib.functions.stats import count_symbol, new_phase
from lib.functions.data_types import map_latest_yahoo_historical, PRICE_HISTORY_PERIOD
from lib.transforms import build_price_rows, build_dividend_rows, build_split_rows
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_latest_dates, RowFlusher
import constants.db_tables as dbt
from .context import valid_symbols

EPOCH = dt.date(2000, 1, 1)

# Per-phase flush sizes: prices dominate (incremental ~1 row/symbol, backfill
# can be 5000+ per symbol); dividends/splits are small.
PRICE_FLUSH_SIZE = 5000
DIV_FLUSH_SIZE = 2000
SPLIT_FLUSH_SIZE = 200


def run_market_data(ctx):
	'''Prices + splits + dividends for all symbols via yfinance history_payload.'''
	stats = new_phase("market_data", len(valid_symbols(ctx)))
	run_yf(ctx, stats)
	return stats


def _want(ctx):
	'''Which market-data phases the current run asked for.'''
	args = ctx.args
	return {
		"prices": bool(getattr(args, "prices", False)),
		"splits": bool(getattr(args, "splits", False)),
		"dividends": bool(getattr(args, "dividends", False)),
	}


def run_yf(ctx, stats):
	yfs = ctx.yfs
	targets = valid_symbols(ctx)
	if not targets:
		return

	want = _want(ctx)
	force = getattr(ctx.args, "force", False)
	full = force or getattr(ctx.args, "full", False)
	# prices/dividends: DO UPDATE re-pull on force, plain insert otherwise.
	# Splits never receive conflict keys (rebase trigger guardrail).
	conflict = ["stock_id", "date"] if force else None
	flushers = {
		"prices": RowFlusher(dbt.historical_price, PRICE_FLUSH_SIZE, conflict_keys=conflict) if want["prices"] else None,
		"dividends": RowFlusher(dbt.dividend, DIV_FLUSH_SIZE, conflict_keys=conflict, null_tolerance=0.0) if want["dividends"] else None,
		"splits": RowFlusher(dbt.stock_split, SPLIT_FLUSH_SIZE) if want["splits"] else None,
	}

	# One batched freshness lookup for the whole run (was per-symbol: 1 query
	# per symbol). Empty in --full mode, where history is fetched anyway.
	latest_map: dict = {}
	if not full:
		latest_map = get_latest_dates(dbt.historical_price, [ctx.stock_ids[s] for s in targets])

	def yf_market(sym):
		stock_id = ctx.stock_ids[sym]
		if full:
			latest = None
			period = PRICE_HISTORY_PERIOD
		else:
			latest = latest_map.get(stock_id) or EPOCH
			period = map_latest_yahoo_historical(latest) or PRICE_HISTORY_PERIOD
		payload = yfs.history_payload(sym, period)
		if payload is None:
			# Transient empty-payload blips (Yahoo throttling / hiccup):
			# one immediate re-fetch, no backoff loop. Doubles cost only
			# for symbols that return empty twice.
			payload = yfs.history_payload(sym, period)
		if payload is None:
			return None
		payload["stock_id"] = stock_id
		payload["latest"] = latest
		return payload

	results = yfs.map_symbols(yf_market, targets, "prices/dividends/splits")

	for symbol in targets:
		payload = results.get(symbol)
		if payload is None:
			count_symbol(stats, False, symbol)
			continue
		if want["prices"]:
			printf(f"---- {symbol} HISTORICAL PRICES --", lv.INFO)
			flushers["prices"].add(build_price_rows(symbol, payload["stock_id"], payload["price_rows"], payload["latest"]))
		if want["dividends"]:
			flushers["dividends"].add(build_dividend_rows(symbol, payload["stock_id"], payload["div_events"], payload["latest"]))
		if want["splits"]:
			flushers["splits"].add(build_split_rows(symbol, payload["stock_id"], payload["split_events"]))
		count_symbol(stats, True)

	stats["rows_written"] = sum(f.finish() for f in flushers.values() if f is not None)
