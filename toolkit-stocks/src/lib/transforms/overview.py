import json
import traceback
from datetime import datetime, timezone

from lib.module.printf import printf, level as lv


def build_overview_row(symbol: str, profile: dict, officers: list[dict], db_meta: dict, yf_info: dict | None) -> dict:
	'''
	Map a normalized profile record to a stock-table row.

	profile: DefeatBeta profile dict OR pre-normalized dict from yfinance info.
	db_meta: existing {name, exchange, currency} from DB - wins over fallbacks,
	keeps old values alive on upsert (omitted keys are not updated).
	yf_info: optional yfinance info dict used as fallback for missing identity fields.

	NOTE: DB sector/industry columns are intentionally swapped
	(stock.sector stores the fine-grained industry, stock.industry the sector)
	matching the legacy yahooquery pipeline convention.
	'''
	try:
		row = {
			"maintenance_update": datetime.now(timezone.utc),
			"address": profile.get("address") or profile.get("address1"),
			"description": profile.get("long_business_summary") or profile.get("longBusinessSummary"),
			"employees": profile.get("full_time_employees") or profile.get("fullTimeEmployees"),
			"sector": profile.get("industry"),	# sector x industry -> switched on purpose
			"industry": profile.get("sector"),	# sector x industry -> switched on purpose
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
		currency = db_meta.get("currency") or profile.get("currency")

		if yf_info:
			name = name or (yf_info.get("longName") or yf_info.get("shortName"))
			exchange = exchange or (yf_info.get("fullExchangeName") or yf_info.get("exchange"))
			currency = currency or yf_info.get("currency")

		if name:
			row["name"] = name
		if exchange:
			row["exchange"] = exchange
		if currency:
			row["currency"] = currency

		return row
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
