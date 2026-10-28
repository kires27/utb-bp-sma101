import traceback

from lib.module.printf import printf, level as lv


def _clean(value) -> float | None:
	try:
		if value is None:
			return None
		f = float(value)
		return None if f != f else f	# NaN check without pandas
	except (TypeError, ValueError):
		return None


def build_price_rows(symbol: str, stock_id: int, rows_desc: list[dict], latest_date) -> list[dict]:
	'''
	Transform price history into DB rows, incremental: only dates on/after
	latest_date are emitted (None = full history, e.g. --force).

	Rows are as-traded OHLCV; adjustment (dividends/splits) is derived on
	read from stock_dividend + stock_split, not stored.
	'''
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		rows = []
		for row in rows_desc:
			d = str(row["date"])[:10]
			if latest_date is not None and d < str(latest_date):
				continue

			close = _clean(row["close"])
			if close is None:
				continue

			rows.append({
				"stock_id": stock_id,
				"date": d,
				"open": _clean(row.get("open")),
				"high": _clean(row.get("high")),
				"low": _clean(row.get("low")),
				"close": close,
				"volume": _clean(row.get("volume")),
			})

		return rows
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []
