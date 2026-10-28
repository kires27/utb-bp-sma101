from dataclasses import dataclass, field

from datasource import DefeatBetaSource, YFinanceSource, FailoverSource, route_symbols
from datasource.base import US_EXCHANGE_FALLBACK
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_stock_id_map, get_symbols, get_symbol_meta


@dataclass
class RunContext:
	'''Passive shared state for all pipeline phases. Logic lives in module functions.'''
	args: object
	symbols: list[str]
	us_symbols: list[str]
	intl_symbols: list[str]
	stock_ids: dict[str, int] = field(default_factory=dict)
	symbol_meta: dict[str, dict] = field(default_factory=dict)
	ds: DefeatBetaSource | None = None
	yfs: YFinanceSource | None = None
	market_data_cache: dict | None = None


def valid_us(ctx: RunContext) -> list[str]:
	return [s for s in ctx.us_symbols if ctx.stock_ids.get(s) is not None]


def valid_intl(ctx: RunContext) -> list[str]:
	return [s for s in ctx.intl_symbols if ctx.stock_ids.get(s) is not None]


def refresh_ids(ctx: RunContext):
	ctx.stock_ids.update(get_stock_id_map(ctx.symbols))


def market_data(ctx: RunContext) -> dict | None:
	'''Lazy batched EOD market data (prices, shares, dividends, splits) for US
	symbols. Fetches only the datasets the requested phases need.'''
	if ctx.market_data_cache is None and ctx.us_symbols:
		args = ctx.args
		metrics = bool(getattr(args, "metrics", False)) or bool(getattr(args, "fa", False))
		want = {
			"prices": bool(getattr(args, "prices", False)) or metrics,
			"shares": metrics,
			"dividends": bool(getattr(args, "dividends", False)) or metrics,
			"splits": bool(getattr(args, "splits", False)),
		}
		printf("-- Fetching market data --", lv.INFO)
		ctx.market_data_cache = {
			"prices": ctx.ds.prices(ctx.us_symbols) if want["prices"] else {},
			"shares": ctx.ds.shares_outstanding(ctx.us_symbols) if want["shares"] else {},
			"dividends": ctx.ds.dividends(ctx.us_symbols) if want["dividends"] else {},
			"splits": ctx.ds.splits(ctx.us_symbols) if want["splits"] else {},
		}
	return ctx.market_data_cache


def build_context(args: object) -> RunContext:
	manual_symbols = None
	if getattr(args, "dev", False):
		from data.symbols import manual_symbols

	symbols: list[str] = manual_symbols if manual_symbols else get_symbols()
	printf(f"-- All symbols: \n{symbols}\n--", lv.INFO)

	ctx = RunContext(
		args=args,
		symbols=symbols,
		us_symbols=[],
		intl_symbols=[],
		stock_ids=get_stock_id_map(symbols),
		symbol_meta=get_symbol_meta(symbols),
		ds=FailoverSource(DefeatBetaSource(), YFinanceSource(max_workers=1)),
		yfs=YFinanceSource(),
	)

	partition_symbols(ctx)
	return ctx


def partition_symbols(ctx: RunContext):
	'''US symbols (DefeatBeta dataset membership) vs the rest (yfinance).'''
	try:
		us_members = ctx.ds.us_members(ctx.symbols)
	except Exception as err:
		printf(f"DefeatBeta membership probe failed ({err}), falling back to exchange heuristic", lv.WARNING)
		us_members = {
			s for s in ctx.symbols
			if (ctx.symbol_meta.get(s, {}) or {}).get("exchange") in US_EXCHANGE_FALLBACK
		}

	ctx.us_symbols, ctx.intl_symbols = route_symbols(ctx.symbols, us_members)
	printf(f"-- Routed: {len(ctx.us_symbols)} DefeatBeta (US), {len(ctx.intl_symbols)} yfinance --", lv.INFO)
