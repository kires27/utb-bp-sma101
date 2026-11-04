def run_phases(args, symbols: list[str], stock_ids: dict[str, int], force: bool = False) -> list[dict]:
	'''
	Ordered phase execution, each gated on its args flag (set by main.py from
	--phases). CLI order is irrelevant; this order is the dependency order.
	New phases plug in here.
	'''
	phases = []

	if args.quote:
		from .prices import run_quote
		phases.append(run_quote(symbols, stock_ids, force=force))

	# ctx phases share one RunContext; built lazily so symbol-independent
	# phases (quote/exchange/calendar) don't pay for meta lookup + source init.
	ctx = None

	def get_ctx():
		nonlocal ctx
		if ctx is None:
			from .context import RunContext
			from datasource import YFinanceSource
			from lib.supabase.sql_functions import get_symbol_meta
			ctx = RunContext(
				args=args,
				symbols=symbols,
				stock_ids=stock_ids,
				symbol_meta=get_symbol_meta(symbols),
				yfs=YFinanceSource(),
			)
		return ctx

	if args.overview:
		from .overview import run_overview
		phases.append(run_overview(get_ctx()))

	if args.statements:
		import constants.db_tables as dbt
		from .statements import run_statements
		phases.append(run_statements(get_ctx(), "balance_sheet", dbt.balance_sheet, 0.6))
		phases.append(run_statements(get_ctx(), "cash_flow", dbt.cash_flow, 0.17))
		phases.append(run_statements(get_ctx(), "income_statement", dbt.income_statement, 0.4))

	if args.prices or args.dividends or args.splits:
		from .market_data import run_market_data
		phases.append(run_market_data(get_ctx()))

	if args.fa:
		from .financial_analysis import run_financial_analysis
		phases.append(run_financial_analysis(get_ctx()))

	if args.fqs:
		from .quality_score import run_quality_score
		phases.append(run_quality_score(get_ctx()))

	if args.calendar:
		from .calendar import run_calendar
		phases.append(run_calendar(force=force))

	if args.exchange:
		from .exchange import run_exchange
		phases.append(run_exchange(force=force))

	return phases
