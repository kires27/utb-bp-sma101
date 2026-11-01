from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_overview_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import insert_data_statement
import constants.db_tables as dbt
from .context import refresh_ids


def run_overview(ctx):
	yfs = ctx.yfs
	stats = new_phase("overview", len(ctx.symbols))

	def yf_profile(sym):
		return yfs.profile(sym)

	infos = yfs.map_symbols(yf_profile, ctx.symbols, "overview")
	rows = []
	for symbol, info in infos.items():
		row = build_overview_row(symbol, info, None, ctx.symbol_meta.get(symbol, {}) or {}, info)
		if not row.get("name"):
			printf(f"{symbol}: no name resolved, skipping overview row", lv.WARNING)
			count_symbol(stats, False, symbol)
			continue
		rows.append(row)

	for row in rows:
		if not row:
			continue
		symbol = row["symbol"]
		mode_condition = {} if ctx.stock_ids.get(symbol) is None else {"symbol": symbol}
		rows_written = insert_data_statement(row, dbt.stock, update_condition=mode_condition)
		count_symbol(stats, True, rows=rows_written)

	refresh_ids(ctx)
	return stats
