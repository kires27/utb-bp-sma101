import datetime as dt

from lib.functions.stats import count_symbol, new_phase
from lib.functions.data_types import map_latest_yahoo_historical
from lib.transforms import build_price_rows, build_dividend_rows, build_split_rows
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_latest_dates, insert_data_statement
import constants.db_tables as dbt
from .context import valid_us, valid_intl, market_data

EPOCH = dt.date(2000, 1, 1)


def run_market_data(ctx):
	'''Prices + splits + dividends for US (DefeatBeta bulk) and non-US (yfinance).'''
	stats = new_phase("market_data", len(valid_us(ctx)) + len(valid_intl(ctx)))
	run_us(ctx, stats)
	run_intl(ctx, stats)
	return stats


def _want(ctx):
	'''Which market-data phases the current run asked for.'''
	args = ctx.args
	return {
		"prices": bool(getattr(args, "prices", False)),
		"splits": bool(getattr(args, "splits", False)),
		"dividends": bool(getattr(args, "dividends", False)),
	}


def run_us(ctx, stats):
	targets = valid_us(ctx)
	if not targets:
		return

	md = market_data(ctx) or {}
	want = _want(ctx)
	force = getattr(ctx.args, "force", False)
	conflict_keys = ["stock_id", "date"] if force else None
	prices = md.get("prices") or {}
	dividends = md.get("dividends") or {}
	splits = md.get("splits") or {}

	latest_price_dates = {}
	latest_div_dates = {}
	if not force and want["prices"]:
		latest_price_dates = get_latest_dates(dbt.historical_price, [ctx.stock_ids[s] for s in targets if s in prices])
	if not force and want["dividends"]:
		latest_div_dates = get_latest_dates(dbt.dividend, [ctx.stock_ids[s] for s in targets if s in dividends])

	if want["prices"]:
		for symbol in targets:
			if symbol not in prices:
				count_symbol(stats, False, symbol)
				continue
			printf(f"---- {symbol} HISTORICAL PRICES --", lv.INFO)
			rows = insert_data_statement(
				build_price_rows(
					symbol, ctx.stock_ids[symbol], prices[symbol],
					latest_price_dates.get(ctx.stock_ids[symbol]),
				),
				dbt.historical_price,
				conflict_keys=conflict_keys,
			)
			count_symbol(stats, True, rows=rows)

	if want["splits"]:
		printf("---- SPLITS (US) --", lv.INFO)
		for symbol in targets:
			rows = insert_data_statement(
				build_split_rows(symbol, ctx.stock_ids[symbol], splits.get(symbol, [])),
				dbt.stock_split,
				conflict_keys=conflict_keys,
			)
			count_symbol(stats, True, symbol, rows=rows)

	if want["dividends"]:
		printf("---- DIVIDENDS (US) --", lv.INFO)
		for symbol in targets:
			if symbol not in dividends:
				count_symbol(stats, False, symbol)
				continue
			rows = insert_data_statement(
				build_dividend_rows(
					symbol, ctx.stock_ids[symbol], dividends[symbol],
					latest_div_dates.get(ctx.stock_ids[symbol]),
				),
				dbt.dividend,
				null_tolerance=0.0,
				conflict_keys=conflict_keys,
			)
			count_symbol(stats, True, symbol, rows=rows)


def run_intl(ctx, stats):
	yfs = ctx.yfs
	targets = valid_intl(ctx)
	if not targets:
		return

	want = _want(ctx)
	force = getattr(ctx.args, "force", False)
	conflict_keys = ["stock_id", "date"] if force else None

	def yf_market(sym):
		stock_id = ctx.stock_ids[sym]
		if force:
			latest = None
			period = "max"
		else:
			latest = get_latest_dates(dbt.historical_price, [stock_id]).get(stock_id) or EPOCH
			period = map_latest_yahoo_historical(latest) or "10y"
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
		rows = 0
		if want["prices"]:
			printf(f"---- {symbol} HISTORICAL PRICES (yf) --", lv.INFO)
			rows += insert_data_statement(
				build_price_rows(symbol, payload["stock_id"], payload["price_rows"], payload["latest"]),
				dbt.historical_price,
				conflict_keys=conflict_keys,
			)
		if want["dividends"]:
			rows += insert_data_statement(
				build_dividend_rows(symbol, payload["stock_id"], payload["div_events"], payload["latest"]),
				dbt.dividend,
				null_tolerance=0.0,
				conflict_keys=conflict_keys,
			)
		if want["splits"]:
			rows += insert_data_statement(
				build_split_rows(symbol, payload["stock_id"], payload["split_events"]),
				dbt.stock_split,
				conflict_keys=conflict_keys,
			)
		count_symbol(stats, True, rows=rows)
