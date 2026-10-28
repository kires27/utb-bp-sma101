import traceback
from datetime import datetime, timezone

from lib.functions.data_types import time_to_timestamptz
from lib.module.printf import printf, level as lv


def build_metric_row(symbol: str, stock_id: int, quote: dict) -> dict:
	'''
	quote: normalized {stock_price, market_cap, regular_market_change_percent,
	regular_market_change, regular_market_time, source}.
	DefeatBeta (US): EOD close/shares-derived values, regular_market_time is None
	(key omitted on upsert -> old value preserved).
	yfinance (non-US): live info() fields.
	'''
	try:
		if not isinstance(symbol, str):
			raise TypeError(f"symbol has wrong data type: {type(symbol)}")
		if stock_id is None:
			raise TypeError("stock_id is None")

		row = {
			"stock_id": stock_id,
			"maintenance_update": datetime.now(timezone.utc),
			"stock_price": quote.get("stock_price"),
			"market_cap": quote.get("market_cap"),
			"regular_market_change_percent": quote.get("regular_market_change_percent"),
			"regular_market_change": quote.get("regular_market_change"),
		}

		raw_time = quote.get("regular_market_time")
		if raw_time:
			row["regular_market_time"] = time_to_timestamptz(
				str(raw_time), "%Y-%m-%d %H:%M:%S"
			) if isinstance(raw_time, str) else datetime.fromtimestamp(int(raw_time), tz=timezone.utc).isoformat().replace("+00:00", "Z")

		return row
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
