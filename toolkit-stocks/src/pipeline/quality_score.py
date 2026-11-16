from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_quality_score
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import insert_data_statement
from domain.financial_quality_score.quality_score import reset_quality_cache
import constants.db_tables as dbt
from constants.pipeline import SYMBOL_COL_WIDTH
from .context import valid_symbols


def run_quality_score(ctx):
	'''
	fqs phase: peer-normalized quality score per symbol. Runs strictly after
	fa, so peer normalization reads fresh FA rows for the whole universe -
	this is why scoring is a separate phase, not folded into insert_fa.
	'''
	reset_quality_cache()
	targets = valid_symbols(ctx)
	stats = new_phase("fqs", len(targets))

	printf("-- quality score --", lv.INFO)
	for symbol in targets:
		fqs = build_quality_score(ctx.stock_ids[symbol])
		if not fqs:
			printf(
				f"{symbol:<{SYMBOL_COL_WIDTH}}: no quality score (missing or insufficient FA rows / peer data)",
				lv.WARNING,
			)
			count_symbol(stats, False, symbol)
			continue

		rows = insert_data_statement(fqs["data"], dbt.analysis, update_condition={
			"stock_id": ctx.stock_ids[symbol],
			"fiscal_date": fqs["fiscal_date"],
			"period": fqs["period"],
		}, label=f"{symbol} qs")
		count_symbol(stats, True, rows=rows)

	printf(
		f"quality score: {stats['symbols_ok']}/{len(targets)} symbols scored "
		f"(peer-normalized, sector medians); {len(stats['failed_symbols'])} failed",
		lv.INFO,
	)
	return stats
