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


PRICE_DECIMALS = 4


def _round_price(value) -> float | None:
	f = _clean(value)
	return None if f is None else round(f, PRICE_DECIMALS)


def _clean_int(value) -> int | None:
	f = _clean(value)
	return None if f is None else round(f)


def build_price_rows(symbol: str, stock_id: int, rows_desc: list[dict], latest_date) -> list[dict]:
	'''
	Transform price history into DB rows, incremental: only dates on/after
	latest_date are emitted (None = full history, e.g. --force).

	Rows are as-traded OHLCV; adjustment (dividends/splits) is derived on
	read from stock_dividend + stock_split, not stored.
	Prices are rounded to PRICE_DECIMALS — float64 sources carry binary
	noise (e.g. 342.6700134277344) that pollutes the numeric columns.
	'''
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		rows = []
		for row in rows_desc:
			d = str(row["date"])[:10]
			if latest_date is not None and d < str(latest_date):
				continue

			close = _round_price(row["close"])
			if close is None:
				continue

			rows.append({
				"stock_id": stock_id,
				"date": d,
				"open": _round_price(row.get("open")),
				"high": _round_price(row.get("high")),
				"low": _round_price(row.get("low")),
				"close": close,
				"volume": _clean_int(row.get("volume")),
			})

		return rows
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []
