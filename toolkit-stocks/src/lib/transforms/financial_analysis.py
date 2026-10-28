import traceback
from datetime import datetime, timezone

import domain.financial_analysis.fa_calculations as fac
from lib.supabase.sql_functions import get_statements_by_stock
from lib.module.printf import printf, level as lv
import constants.db_tables as dbt


def build_financial_analysis(symbol: str, stock_id: int, quote: dict) -> dict:
	'''
	quote: normalized {stock_price, market_cap, dividend_yield} from the
	routed datasource (DefeatBeta EOD for US, yfinance info for non-US).
	Statement data comes from DB rows written by --balance/--cash/--income.
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
		dividend_yield = quote.get("dividend_yield")

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
				"assets_price": fac.assets_price(net_tangible_assets, total_liabilities, market_cap),
				"capital_index": fac.capital_index(net_income, capital_expenditure),
				"current_ratio": fac.current_ratio(current_assets, current_liabilities),
				"debt_to_equity": fac.debt_to_equity(total_liabilities, stockholders_equity),
				"dividend_yield": fac.dividend_yield(dividend_yield),
				"earning_per_share": earnings_per_share,
				"gross_margin": fac.gross_margin(gross_profit, total_revenue),
				"net_margin": fac.net_margin(net_income, total_revenue),
				"operating_margin": fac.operating_margin(operating_income, total_revenue),
				"pb_ratio": fac.pb_ratio(market_cap, stockholders_equity),
				"pe_ratio": fac.pe_ratio(price, earnings_per_share),
				"payback_period": fac.payback_period(total_debt, free_cash_flow),
				"return_on_equity": fac.return_on_equity(net_income, stockholders_equity),
				"revenues_per_share": fac.revenues_per_share(total_revenue, share_issued),
				"quality_score": None
			},
			"fiscal_date": fiscal_date,
			"period": period,
		}
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
