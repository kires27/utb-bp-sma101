from lib.module.printf import printf, level as lv
from lib.functions.stats import report
from lib.supabase.init import get_connection
import constants.db_tables as dbt
from .context import build_context, market_data
from .overview import run_overview
from .statements import run_statements
from .market_data import run_market_data
from .metrics import run_metrics
from .financial_analysis import run_financial_analysis


def run(args):
	'''Run requested phases in fixed order: overview, statements, market data, metrics, FA.'''
	conn = get_connection()
	phases = []
	try:
		ctx = build_context(args)

		if args.overview:
			printf("-- OVERVIEW --", lv.INFO)
			phases.append(run_overview(ctx))

		if args.balance:
			printf("-- BALANCE SHEET --", lv.INFO)
			phases.append(run_statements(ctx, "balance_sheet", dbt.balance_sheet, 0.6))

		if args.cash:
			printf("-- CASH FLOW --", lv.INFO)
			phases.append(run_statements(ctx, "cash_flow", dbt.cash_flow, 0.17))

		if args.income:
			printf("-- INCOME STATEMENT --", lv.INFO)
			phases.append(run_statements(ctx, "income_statement", dbt.income_statement, 0.4))

		if args.prices or args.splits or args.dividends or args.metrics or args.fa:
			if ctx.us_symbols:
				market_data(ctx)  # fetch once, shared by all market-data phases

		if args.dividends:
			printf("-- DIVIDENDS --", lv.INFO)

		if args.prices or args.splits or args.dividends:
			phases.append(run_market_data(ctx))

		if args.metrics:
			printf("-- METRICS --", lv.INFO)
			phases.append(run_metrics(ctx))

		if args.fa:
			printf("-- FINANCIAL ANALYSIS --", lv.INFO)
			phases.append(run_financial_analysis(ctx))
	finally:
		report(phases, prod=getattr(args, "prod", False))
		conn.cursor().close()
		conn.close()
		printf("Disconnected from the database", lv.INFO)
		printf.close()
