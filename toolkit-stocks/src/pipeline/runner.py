def run_phases(args, symbols: list[str], stock_ids: dict[str, int], force: bool = False) -> list[dict]:
	'''
	Ordered phase execution, each gated on its args flag (set by main.py from
	--phases). CLI order is irrelevant; this order is the dependency order.
	New phases plug in here.
	'''
	from lib.functions.netstats import snapshot

	def _with_net(fn, *fn_args, **fn_kwargs):
		'''Run one phase and stamp its network-request deltas onto the stats.'''
		start = snapshot()
		stats = fn(*fn_args, **fn_kwargs)
		end = snapshot()
		stats["db_requests"] = end["db"] - start["db"]
		stats["yf_requests"] = end["yfinance"] - start["yfinance"]
		return stats

	phases = []

	if args.quote:
		from .prices import run_quote
		phases.append(_with_net(run_quote, symbols, stock_ids, force=force))

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
		phases.append(_with_net(run_overview, get_ctx()))

	if args.statements:
		import constants.db_tables as dbt
		from .statements import run_statements
		# Annual statements: 380-day freshness window per table.
		phases.append(_with_net(run_statements, get_ctx(), "balance_sheet", dbt.balance_sheet, 0.6))
		phases.append(_with_net(run_statements, get_ctx(), "cash_flow", dbt.cash_flow, 0.17))
		phases.append(_with_net(run_statements, get_ctx(), "income_statement", dbt.income_statement, 0.4))
		# Quarterly statements: calendar-suppressed staleness window; only
		# stale-and-not-suppressed symbols fetch, so daily cost stays small.
		phases.append(_with_net(run_statements, get_ctx(), "balance_sheet", dbt.balance_sheet, 0.6, "quarterly"))
		phases.append(_with_net(run_statements, get_ctx(), "cash_flow", dbt.cash_flow, 0.17, "quarterly"))
		phases.append(_with_net(run_statements, get_ctx(), "income_statement", dbt.income_statement, 0.4, "quarterly"))

	if args.prices or args.dividends or args.splits:
		from .market_data import run_market_data
		phases.append(_with_net(run_market_data, get_ctx()))

	# fx feeds fx_rate used by the fa transform (statement->trading ccy);
	# must run before fa in the daily set.
	if args.fx:
		from .fx import run_fx
		phases.append(_with_net(run_fx, force=force))

	if args.fa:
		from .financial_analysis import run_financial_analysis
		phases.append(_with_net(run_financial_analysis, get_ctx()))

	if args.fqs:
		from .quality_score import run_quality_score
		phases.append(_with_net(run_quality_score, get_ctx()))

	if args.calendar:
		from .calendar import run_calendar
		phases.append(_with_net(run_calendar, force=force))

	if args.exchange:
		from .exchange import run_exchange
		phases.append(_with_net(run_exchange, force=force))

	return phases
