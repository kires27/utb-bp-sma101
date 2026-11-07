import traceback
from datetime import datetime, timezone, date as dtdate

import domain.financial_analysis.fa_calculations as fac
from lib.supabase.sql_functions import get_statements_by_stock, get_ttm_dividends
from lib.module.printf import printf, level as lv
import constants.db_tables as dbt


def make_fx_lookup(rates: dict):
	'''Build a fx(ccy) closure from get_fx_rates() output {(from, to, date): rate}.

	Flattens to {to_ccy: [(date, rate), ...]} once per run (FA transforms many
	symbols; a linear scan per lookup would be quadratic). fx(ccy) returns the
	latest USD->ccy rate on/before today - the vintage rule for TTM rows: FA
	writes only TTM rows with a live price/market_cap, so one "today's" rate
	covers every row. Falling back to the newest available date <= today keeps
	weekend/holiday gaps working (Yahoo {CCY}=X has no Sunday bars).

	USD itself is implicitly 1.0 (1 USD = 1 USD) and is never stored.
	Returns None when the currency has no rates at all.
	'''
	if not rates:
		return None
	by_ccy: dict[str, list] = {}
	for (_frm, to, d), rate in rates.items():
		by_ccy.setdefault(to, []).append((d, rate))
	for series in by_ccy.values():
		series.sort()

	def fx(ccy: str) -> float | None:
		if ccy == "USD":
			return 1.0
		series = by_ccy.get(ccy)
		if not series:
			return None
		today = dtdate.today()
		rate = None
		for d, r in series:
			if d > today:
				break
			rate = r
		return rate

	return fx


def fx_rate_for(trading_ccy: str | None, statement_ccy: str | None, fx) -> float | None:
	'''statement -> trading conversion rate = r(trading) / r(stmt), where r(x)
	is the stored USD->x rate (CCY per 1 USD). 1.0 when the currencies match
	(no-op path). None when either currency or rate is missing -> the ratio
	lands NULL in the row (honest empty beats a number inflated by an FX
	factor). fx is the fx(ccy) closure from make_fx_lookup.'''
	if not trading_ccy or not statement_ccy:
		return None
	if trading_ccy == statement_ccy:
		return 1.0
	if fx is None:
		return None
	r_trading = fx(trading_ccy)
	r_stmt = fx(statement_ccy)
	if r_trading is None or r_stmt in (None, 0):
		return None
	return r_trading / r_stmt


def build_financial_analysis(symbol: str, stock_id: int, quote: dict, fx=None, statement_currency: str | None = None) -> dict:
	'''
	quote: normalized {stock_price, market_cap, currency} from stock_quote
	(written by the quote phase). statement_currency from stock (RunContext
	symbol_meta) = reporting currency of the statements. fx = fx(ccy) closure
	from make_fx_lookup (rates loaded once per run). Statement data comes from
	DB rows written by --balance/--cash/--income; dividend_yield is computed
	from stock_dividend (TTM sum over current price), not from any quote
	source. quality_score is NOT written here - the faqs phase upserts it
	separately (writing NULL here would wipe the score every daily run).
	'''
	try:
		if not isinstance(symbol, str):
			raise TypeError(f"symbol has wrong data type: {type(symbol)}")
		if stock_id is None:
			raise TypeError("stock_id is None")

		balance_sheets = get_statements_by_stock(stock_id, dbt.balance_sheet)
		cash_flows = get_statements_by_stock(stock_id, dbt.cash_flow, 1)
		income_statements = get_statements_by_stock(stock_id, dbt.income_statement)

		price = quote.get("stock_price")
		market_cap = quote.get("market_cap")
		if not price or not market_cap:
			raise ValueError("Quote is empty - no price or market cap")

		fiscal_date = cash_flows[0].get("fiscal_date").isoformat()
		period = "TTM"

		free_cash_flow = cash_flows[0].get("free_cash_flow")
		net_tangible_assets = balance_sheets[0].get("net_tangible_assets")
		net_income = income_statements[0].get("net_income")
		capital_expenditure = cash_flows[0].get("capital_expenditure")
		current_assets = balance_sheets[0].get("current_assets")
		current_liabilities = balance_sheets[0].get("current_liabilities")
		total_liabilities = balance_sheets[0].get("total_liabilities_net_minority_interest")
		stockholders_equity = balance_sheets[0].get("stockholders_equity")
		share_issued = balance_sheets[0].get("share_issued")
		dividends_on_preferred_stocks = income_statements[0].get("otherunder_preferred_stock_dividend")
		gross_profit = income_statements[0].get("gross_profit")
		total_revenue = income_statements[0].get("total_revenue")
		operating_income = income_statements[0].get("operating_income")
		total_debt = balance_sheets[0].get("total_debt")

		earnings_per_share = fac.earning_per_share(net_income, share_issued, dividends_on_preferred_stocks)
		ttm_dividends = get_ttm_dividends(stock_id)

		# FX: price-side numbers (price, market_cap) are always trading ccy
		# (Yahoo normalizes), statement-side (EPS, equity, NTA, liabilities)
		# are statement ccy. Convert the statement side at ratio-compute time
		# (fx_rate_for); missing rate -> the ratio lands NULL, never wrong.
		rate = fx_rate_for(quote.get("currency"), statement_currency, fx)

		def stmt_side(value):
			# statement-ccy value -> trading ccy. None value stays None;
			# unknown rate -> None so the ratio lands NULL, never wrong;
			# rate 1.0 -> untouched (byte-identical to the pre-fx path).
			if value is None or rate is None:
				return None
			if rate == 1.0:
				return value
			return float(value) * rate

		# dividend_yield NOT touched here: stock_dividend amounts are
		# Yahoo-reported and likely already trading-ccy; revisit if pence
		# storage ever lands.

		return {
			"data": {
				"stock_id": stock_id,
				"fiscal_date": fiscal_date,
				"period": period,
				"maintenance_update": datetime.now(timezone.utc).isoformat(),

				"revenue_growth": fac.growth_calculation(income_statements, "total_revenue"),
				"gross_income_growth": fac.growth_calculation(income_statements, "gross_profit"),
				"net_income_growth": fac.growth_calculation(income_statements, "net_income"),
				"retained_earning_growth": fac.growth_calculation(balance_sheets, "retained_earnings"),
				"debt_growth": fac.growth_calculation(balance_sheets, "total_debt"),
				"assets_price": fac.assets_price(stmt_side(net_tangible_assets), stmt_side(total_liabilities), market_cap),
				"capital_index": fac.capital_index(net_income, capital_expenditure),
				"current_ratio": fac.current_ratio(current_assets, current_liabilities),
				"debt_to_equity": fac.debt_to_equity(total_liabilities, stockholders_equity),
				"dividend_yield": fac.dividend_yield(ttm_dividends, price),
				"earning_per_share": earnings_per_share,
				"gross_margin": fac.gross_margin(gross_profit, total_revenue),
				"net_margin": fac.net_margin(net_income, total_revenue),
				"operating_margin": fac.operating_margin(operating_income, total_revenue),
				"pb_ratio": fac.pb_ratio(market_cap, stmt_side(stockholders_equity)),
				"pe_ratio": fac.pe_ratio(price, stmt_side(earnings_per_share)),
				"payback_period": fac.payback_period(total_debt, free_cash_flow),
				"return_on_equity": fac.return_on_equity(net_income, stockholders_equity),
				"revenues_per_share": fac.revenues_per_share(total_revenue, share_issued),
			},
			"fiscal_date": fiscal_date,
			"period": period,
		}
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
