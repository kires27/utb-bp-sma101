from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_metric_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import insert_data_statement
import constants.db_tables as dbt
from .context import valid_us, valid_intl
from .quotes import build_us_quote


def run_metrics(ctx):
	yfs = ctx.yfs
	stats = new_phase("metrics", len(valid_us(ctx)) + len(valid_intl(ctx)))

	for symbol in valid_us(ctx):
		printf(f"---- {symbol} METRICS (DefeatBeta) --", lv.INFO)
		quote = build_us_quote(ctx, symbol)
		if quote:
			rows = insert_data_statement(
				build_metric_row(symbol, ctx.stock_ids[symbol], quote),
				dbt.metric,
				update_condition={"stock_id": ctx.stock_ids[symbol]}
			)
			count_symbol(stats, True, rows=rows)
		else:
			count_symbol(stats, False, symbol)

	def yf_quote(sym):
		return yfs.quote(sym)

	quotes = yfs.map_symbols(yf_quote, valid_intl(ctx), "metrics") if ctx.intl_symbols else {}
	for symbol in valid_intl(ctx):
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
