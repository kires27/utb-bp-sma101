from dataclasses import dataclass, field

from datasource import YFinanceSource
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_stock_id_map, get_symbols, get_symbol_meta


@dataclass
class RunContext:
	'''Passive shared state for all pipeline phases. Logic lives in module functions.'''
	args: object
	symbols: list[str]
	stock_ids: dict[str, int] = field(default_factory=dict)
	symbol_meta: dict[str, dict] = field(default_factory=dict)
	yfs: YFinanceSource | None = None


def valid_symbols(ctx: RunContext) -> list[str]:
	return [s for s in ctx.symbols if ctx.stock_ids.get(s) is not None]


def refresh_ids(ctx: RunContext):
	ctx.stock_ids.update(get_stock_id_map(ctx.symbols))


def build_context(args: object) -> RunContext:
	manual_symbols = None
	if getattr(args, "dev", False):
		from data.symbols import manual_symbols

	symbols: list[str] = manual_symbols if manual_symbols else get_symbols()
	printf(f"-- All symbols: {len(symbols)} --", lv.INFO)

	return RunContext(
		args=args,
		symbols=symbols,
		stock_ids=get_stock_id_map(symbols),
		symbol_meta=get_symbol_meta(symbols),
		yfs=YFinanceSource(),
	)
