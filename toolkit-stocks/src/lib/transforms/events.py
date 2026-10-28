import traceback

from lib.module.printf import printf, level as lv


def _parse_date(raw):
	if raw is None:
		return None
	try:
		return str(raw)[:10]
	except (TypeError, ValueError):
		return None


def build_dividend_rows(symbol: str, stock_id: int, events: list[dict], latest_date) -> list[dict]:
	'''
	events: [{date: "YYYY-MM-DD", amount: float}] sorted desc.
	latest_date: only events on/after this DB date are emitted (incremental sync).
	'''
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		rows = []
		for event in events:
			d = _parse_date(event["date"])
			if d is None or (latest_date is not None and d < str(latest_date)):
				continue

			amount = float(event["amount"])
			if amount == 0:
				# 0 dividend = source corruption (e.g. rounded pre-split value), never real
				printf(f"{symbol}: skip zero dividend event on {d}", lv.WARNING)
				continue

			rows.append({
				"stock_id": stock_id,
				"date": d,
				"dividend": amount,
			})

		return rows
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []


def build_split_rows(symbol: str, stock_id: int, events: list[dict], latest_date=None) -> list[dict]:
	'''
	events: [{date, factor: float | None}]. Events with factor None or 0 skipped.
	'''
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		rows = []
		for event in events:
			factor = event.get("factor")
			if factor is None or factor == 0:
				continue

			d = _parse_date(event["date"])
			if d is None:
				continue
			if latest_date is not None and d < str(latest_date):
				continue

			rows.append({
				"stock_id": stock_id,
				"date": d,
				"factor": int(factor) if float(factor).is_integer() else float(factor),
			})

		# oldest first: split-trigger rebasis must apply in insertion order
		rows.sort(key=lambda r: r["date"])
		return rows
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []
