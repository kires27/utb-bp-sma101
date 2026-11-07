import json
import traceback
from datetime import datetime, timezone

from lib.module.printf import printf, level as lv


def build_overview_row(symbol: str, profile: dict, officers: list[dict], db_meta: dict, yf_info: dict | None) -> dict:
	'''
	Map a normalized profile record to a stock-table row.

	profile: DefeatBeta profile dict OR pre-normalized dict from yfinance info.
	db_meta: existing {name, exchange} from DB - wins over fallbacks,
	keeps old values alive on upsert (omitted keys are not updated).
	yf_info: optional yfinance info dict used as fallback for missing identity fields.

	NOTE: Standard GICS convention — stock.sector stores the broad sector
	(Technology, Healthcare, ...), stock.industry the fine-grained industry
	(Consumer Electronics, Banks - Diversified, ...).
	'''
	try:
		row = {
			"maintenance_update": datetime.now(timezone.utc),
			"address": profile.get("address") or profile.get("address1"),
			"description": profile.get("long_business_summary") or profile.get("longBusinessSummary"),
			"employees": profile.get("full_time_employees") or profile.get("fullTimeEmployees"),
			"sector": profile.get("sector"),
			"industry": profile.get("industry"),
			"key_executives": json.dumps(officers) if officers is not None else json.dumps(
				(profile.get("companyOfficers") or []) if profile.get("companyOfficers") is not None else (yf_info or {}).get("companyOfficers", [])
			),
			"phone_number": profile.get("phone"),
			"website": profile.get("web_site") or profile.get("website"),
			"symbol": symbol,
			"logo": None,
			"city": profile.get("city"),
			"country": profile.get("country"),
			"zip": profile.get("zip"),
		}

		name = db_meta.get("name") or profile.get("longName") or profile.get("shortName")
		exchange = db_meta.get("exchange") or profile.get("fullExchangeName") or profile.get("exchange")

		if yf_info:
			name = name or (yf_info.get("longName") or yf_info.get("shortName"))
			exchange = exchange or (yf_info.get("fullExchangeName") or yf_info.get("exchange"))

		if name:
			row["name"] = name
		if exchange:
			row["exchange"] = exchange

		# Reporting currency of the financial statements (yfinance
		# financialCurrency), NOT the trading currency — differs for ADRs.
		fin_ccy = profile.get("financialCurrency") or (yf_info or {}).get("financialCurrency")
		if fin_ccy:
			row["statement_currency"] = fin_ccy

		return row
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
