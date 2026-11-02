def run_mode(mode: str, args, symbols: list[str], stock_ids: dict[str, int], force: bool = False) -> list[dict]:
	'''
	Composition table: run mode -> ordered phase list.
	hourly: standalone (symbols, stock_ids) signature.
	daily:  ctx phases in the fixed phase order.
	New phases plug in here.
	'''
	from .prices import run_hourly_prices
	from .context import RunContext
	from datasource import YFinanceSource
	from lib.supabase.sql_functions import get_symbol_meta
	import constants.db_tables as dbt

	def run_ctx_mode(mode: str, args, symbols: list[str], stock_ids: dict[str, int]) -> list[dict]:
		'''Run a ctx-based mode. daily and backfill share the phase order; backfill
		fetches full history (args.full=True) and skips metrics (next hourly run
		covers those).'''
		ctx = RunContext(
			args=args,
			symbols=symbols,
			stock_ids=stock_ids,
			symbol_meta=get_symbol_meta(symbols),
			yfs=YFinanceSource(),
		)
		from .overview import run_overview
		from .statements import run_statements
		from .market_data import run_market_data
		from .metrics import run_metrics
		from .financial_analysis import run_financial_analysis

		phases = [
			run_overview(ctx),
			run_statements(ctx, "balance_sheet", dbt.balance_sheet, 0.6),
			run_statements(ctx, "cash_flow", dbt.cash_flow, 0.17),
			run_statements(ctx, "income_statement", dbt.income_statement, 0.4),
			run_market_data(ctx),
		]
		if mode == "daily":
			phases.append(run_metrics(ctx))
		phases.append(run_financial_analysis(ctx))
		return phases

	if mode == "hourly":
		return [run_hourly_prices(symbols, stock_ids, force=force)]

	if mode == "exchange":
		from .exchange import run_exchange
		return [run_exchange(force=force)]

	if mode == "calendar":
		from .calendar import run_calendar
		return [run_calendar(force=force)]

	if mode in ("daily", "backfill"):
		phases = run_ctx_mode(mode, args, symbols, stock_ids)
		if mode == "daily":
			# calendar refresh rides on daily: announced earnings dates feed the
			# future tier-2 statement optimizer
			from .calendar import run_calendar
			phases.append(run_calendar())
		return phases

	raise ValueError(f"Unknown run mode: {mode}")
