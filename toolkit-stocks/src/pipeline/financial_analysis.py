from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_financial_analysis, make_fx_lookup
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import get_fx_rates, get_quotes, insert_data_statement
import constants.db_tables as dbt
from .context import valid_symbols


def run_financial_analysis(ctx):
	targets = valid_symbols(ctx)
	stats = new_phase("financial_analysis", len(targets))

	# Market data comes from stock_quote (written by the quote phase, hourly
	# cron), not from per-symbol yfinance calls. No fallback fetch: a missing
	# row or null price/market_cap skips the symbol - refetching is not FA's job.
	stock_ids = [ctx.stock_ids[s] for s in targets]
	quotes = get_quotes(stock_ids)
	# FX rates loaded once per run (fx phase writes them BEFORE fa): the
	# statement->trading-currency conversion for ADR / cross-listed stocks.
	fx = make_fx_lookup(get_fx_rates())
	printf("-- financial analysis --", lv.INFO)
	for symbol in targets:
		quote = quotes.get(ctx.stock_ids[symbol]) or {}
		missing = [f for f in ("stock_price", "market_cap") if not quote.get(f)]
		if missing:
			printf(f"{symbol}: skipped, missing {', '.join(missing)} in stock_quote", lv.ERROR)
			count_symbol(stats, False, symbol)
			continue
		insert_fa(ctx, symbol, quote, fx, stats)

	return stats


def insert_fa(ctx, symbol, quote, fx, stats):
	stock_id = ctx.stock_ids[symbol]

	fa = build_financial_analysis(
		symbol, stock_id, quote, fx=fx,
		statement_currency=ctx.symbol_meta.get(symbol, {}).get("statement_currency"),
	)
	if not fa:
		count_symbol(stats, False, symbol)
		return

	# quality_score deliberately absent: the faqs phase upserts it after all
	# FA rows are written, so peer normalization sees fresh data.
	rows = insert_data_statement(fa["data"], dbt.analysis, update_condition={
		"stock_id": stock_id,
		"fiscal_date": fa["fiscal_date"],
		"period": fa["period"],
	}, label=f"{symbol} fa")
	count_symbol(stats, True, rows=rows)
