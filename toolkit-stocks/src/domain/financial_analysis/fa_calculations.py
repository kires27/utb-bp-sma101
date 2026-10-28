import traceback
from lib.module.printf import printf, level as lv


def _to_float(value) -> float | None:
	"""Convert to float; None (missing data) stays None — expected for non-US / incomplete data."""
	if value is None:
		return None
	return float(value)


def _safe(numerator, denominator, fn=round, digits=4):
	"""
	Shared division wrapper for metric calculations.
	Missing data (None) => None silently; ZeroDivisionError => None silently.
	Unexpected errors => WARNING log, None.
	"""
	try:
		num = _to_float(numerator)
		den = _to_float(denominator)
		if num is None or den is None or den == 0:
			return None
		return fn(num / den, digits)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None


def gross_margin(gross_profit: float, total_revenue: float) -> float | None:
	"""
	income_statement => gross_profit, total_revenue
	"""
	return _safe(gross_profit, total_revenue)


def operating_margin(operating_income: float, total_revenue: float) -> float | None:
	"""
	income_statement => operating_income, total_revenue
	"""
	return _safe(operating_income, total_revenue)


def net_margin(net_income: int, total_revenue: int) -> float | None:
	"""
	income_statement => net_income, revenues
	"""
	return _safe(net_income, total_revenue)


def return_on_equity(net_income: float, stockholders_equity: float) -> float | None:
	"""
	income_statement => net_income
	balance_sheet => stockholders_equity (total_shareholders_equity)
	"""
	return _safe(net_income, stockholders_equity)


def earning_per_share(net_income: float, share_issued: float, dividends_on_preferred_stocks: float | None) -> float | None:
	"""
	income_statement => net_income, dividends_on_preferred_stocks (otherunder_preferred_stock_dividend)
	balance_sheet => share_issued (number of outstanding shares)
	"""
	try:
		num = _to_float(net_income)
		den = _to_float(share_issued)
		if num is None or den is None or den == 0:
			return None
		dops = _to_float(dividends_on_preferred_stocks)
		dops = dops if dops is not None else 0
		return round((num - dops) / den, 4)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None


def debt_to_equity(total_liabilities: float, stockholders_equity: float) -> float | None:
	"""
	balance_sheet => total_liabilities (Total Liabilities Net Minority Interest),
		stockholders_equity
	"""
	return _safe(total_liabilities, stockholders_equity)


def current_ratio(current_assets: float, current_liabilities: float) -> float | None:
	"""
	balance_sheet => current_assets, current_liabilities
	"""
	return _safe(current_assets, current_liabilities)


def revenues_per_share(total_revenue: float, share_issued: float) -> float | None:
	"""
	income_statement => total_revenue
	balance_sheet => number of outstanding shares/share_issued
	"""
	return _safe(total_revenue, share_issued)


def capital_index(net_income: float, capital_expenditure: float) -> float | None:
	"""
	income_statement => net_income
	cash_flow => capital_expenditure
	"""
	try:
		num = _to_float(capital_expenditure)
		den = _to_float(net_income)
		if num is None or den is None or den == 0:
			return None
		return round(-num / den, 4)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None


def payback_period(total_debt: float, free_cash_flow: float):
	"""
	balance_sheet => total_debt
	cash_flow => free_cash_flow
	"""
	return _safe(total_debt, free_cash_flow)


def assets_price(net_tangible_assets: float, total_liabilities: float, market_cap: float) -> float | None:
	"""
	balance_sheet => net_tangible_assets, total_liabilities (total_liabilities_net_minority_interest)
	"""
	try:
		nta = _to_float(net_tangible_assets)
		liab = _to_float(total_liabilities)
		mc = _to_float(market_cap)
		if nta is None or liab is None or mc is None or mc == 0:
			return None
		return round(((nta - liab) * 1.5) / mc, 4)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None


def pe_ratio(price: float, earnings_per_share: float) -> float | None:
	"""
	overview => price
	? => earnings_per_share
	"""
	return _safe(price, earnings_per_share)


def pb_ratio(market_cap: float, total_equity: float) -> float | None:
	"""
	overview => market_cap
	balance_sheet => total_equity (previously was total_assets)
	"""
	return _safe(market_cap, total_equity)


def dividend_yield(dividend_yield) -> float | None:
	"""get dividend yield from yahoo finance and check whether its None type"""
	try:
		value = _to_float(dividend_yield)
		if value is None:
			return None
		return round(value * 100, 4)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None


def growth_calculation(statements: list[dict], key: str) -> float | None:
	"""
	Calculates growth for a given key over a period of years.
	Example: net income growth for 5 years, revenues growth for 5 years, debt growth for 5 years.

	Used for: debt growth, revenue growth, income growth, retained earnings

	:param statements: list of dicts, each representing a statement for a year (most recent first)
	:param key: key in the statement dict to calculate growth for
	:return: average annual growth percentage or None if data missing/invalid
	"""
	try:
		newest = _to_float(statements[0].get(key))
		oldest = _to_float(statements[-1].get(key))
		if newest is None or oldest is None:
			# expected for non-US / incomplete data — no warning noise
			return None
		if oldest == 0 or newest * oldest < 0:
			# TODO add another growth calc method
			return None
		growth = (pow((newest / oldest), 1 / len(statements)) - 1)
		return round(growth, 4)
	except Exception as error:
		tb = traceback.extract_tb(error.__traceback__)[-1]
		printf(f"{error} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		return None
