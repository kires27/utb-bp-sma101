from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_metric_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import insert_data_statement
import constants.db_tables as dbt
from .context import valid_symbols


def run_metrics(ctx):
	yfs = ctx.yfs
	targets = valid_symbols(ctx)
	stats = new_phase("metrics", len(targets))

	def yf_quote(sym):
		return yfs.quote(sym)

	quotes = yfs.map_symbols(yf_quote, targets, "metrics")
	for symbol in targets:
		quote = quotes.get(symbol)
		if quote is None:
			count_symbol(stats, False, symbol)
			continue
		printf(f"---- {symbol} METRICS (yf) --", lv.INFO)
		rows = insert_data_statement(
			build_metric_row(symbol, ctx.stock_ids[symbol], quote),
			dbt.metric,
			update_condition={"stock_id": ctx.stock_ids[symbol]}
		)
		count_symbol(stats, True, rows=rows)

	return stats
