import re


# DB statement fields and the statement line-item titles that feed them.
# DefeatBeta uses snake_case item_names, yfinance uses Title Case row labels
# (both derive from the same Yahoo taxonomy), so one alias map serves both.
STATEMENT_FIELD_MAP: dict[str, list[str]] = {
	"total_revenue": ["total_revenue"],
	"gross_profit": ["gross_profit"],
	"net_income": ["net_income", "net_income_common_stockholders"],
	"operating_income": ["operating_income"],
	"basic_average_shares": ["basic_average_shares"],
	"otherunder_preferred_stock_dividend": ["otherunder_preferred_stock_dividend"],
	"total_assets": ["total_assets"],
	"current_assets": ["current_assets"],
	"total_liabilities_net_minority_interest": ["total_liabilities_net_minority_interest"],
	"current_liabilities": ["current_liabilities"],
	"net_tangible_assets": ["net_tangible_assets"],
	"stockholders_equity": ["stockholders_equity"],
	"retained_earnings": ["retained_earnings"],
	"share_issued": ["share_issued"],
	"cash_cash_equivalents_and_short_term_investments": ["cash_cash_equivalents_and_short_term_investments"],
	"total_debt": ["total_debt"],
	"free_cash_flow": ["free_cash_flow"],
	"capital_expenditure": ["capital_expenditure"],
	"operating_cash_flow": ["operating_cash_flow"],
}

STATEMENT_FIELDS: dict[str, list[str]] = {
	"income_statement": [
		"total_revenue", "net_income", "gross_profit", "operating_income",
		"basic_average_shares", "otherunder_preferred_stock_dividend",
	],
	"balance_sheet": [
		"total_assets", "current_assets", "total_liabilities_net_minority_interest",
		"current_liabilities", "net_tangible_assets", "stockholders_equity",
		"retained_earnings", "share_issued",
		"cash_cash_equivalents_and_short_term_investments", "total_debt",
	],
	"cash_flow": [
		"free_cash_flow", "capital_expenditure", "operating_cash_flow",
	],
}

_normalized_cache: dict[str, str] = {}


def normalize_title(title: str) -> str:
	'''Normalize a statement line-item title to snake_case lookup key.'''
	cached = _normalized_cache.get(title)
	if cached is not None:
		return cached
	key = re.sub(r"[^a-z0-9]+", "_", title.strip().lower()).strip("_")
	_normalized_cache[title] = key
	return key


def pick_statement_value(fields: dict, db_field: str):
	'''Pick the first matching line-item value for a DB field from a normalized field dict.'''
	for alias in STATEMENT_FIELD_MAP[db_field]:
		if alias in fields:
			return fields[alias]
	return None


def route_symbols(symbols: list[str], us_members: set[str]) -> tuple[list[str], list[str]]:
	'''
	Partition symbols into DefeatBeta (US dataset) and yfinance targets.
	Membership in the DefeatBeta stock_profile dataset is the authoritative
	test, including for symbols that are not yet in the database.
	'''
	us = [s for s in symbols if s in us_members]
	intl = [s for s in symbols if s not in us_members]
	return us, intl


US_EXCHANGE_FALLBACK = {
	"NYSE", "NASDAQ", "AMEX", "ASE", "NMS", "NGM", "PCX", "BATS", "NYSEArca",
	"OTC", "PNK", "NYSE MKT", "OTC Markets", "OTCQB", "OTCBB",
}
