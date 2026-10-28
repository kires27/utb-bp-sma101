import traceback

from lib.module.printf import printf, level as lv


def nonempty(result) -> bool:
	'''Default validation: result exists and is truthy (non-empty list/dict).'''
	return bool(result)


def price_rows_valid(rows) -> bool:
	'''Price history rows: non-empty, every row has date + close.'''
	if not rows:
		return False
	return all(r.get("date") and r.get("close") is not None for r in rows)


class FailoverSource:
	'''
	Per-symbol failover wrapper: try primary, validate, else fallback.
	Same method surface as the underlying sources where both can serve.

	Contract (tests/contract/test_failover_contract.py): get(symbol) tries
	primary then fallback, returning (result, source_name) or (None, None).
	Real sources have no .get, so get() duck-types any callable member.

	Prices are all-or-nothing per symbol's full history: sources may carry
	different event completeness (dividends/splits), and events drive
	dividend/split-adjusted series derived on read - splicing histories
	mid-way would corrupt every row before the splice point.
	'''

	def __init__(self, primary, fallback, validate=nonempty, label: str = "failover"):
		self.primary = primary
		self.fallback = fallback
		self.validate = validate
		self.label = label

	def get(self, symbol):
		'''Contract method: works with any source exposing .get(symbol).'''
		for name, source in (("primary", self.primary), ("fallback", self.fallback)):
			try:
				result = source.get(symbol)
				if self.validate(result):
					return result, name
			except Exception:
				pass
		return None, None

	def _per_symbol(self, symbols: list[str], primary_fn, fallback_fn, label: str,
			primary_name: str = None, fallback_name: str = None) -> dict:
		'''
		Primary per symbol; on raise/invalid result, retry via fallback_fn.
		Returns {symbol: result} only for symbols served by either source.
		primary_name/fallback_name: names used in logs/counters. Defaults to
		constructor order; pass explicitly when a method inverts the roles
		(e.g. dividends serves yfinance first).
		'''
		primary_name = primary_name or type(self.primary).__name__
		fallback_name = fallback_name or type(self.fallback).__name__
		out: dict = {}
		served_by = {primary_name: 0, fallback_name: 0}
		for symbol in symbols:
			try:
				result = primary_fn(symbol)
				if self.validate(result):
					out[symbol] = result
					served_by[primary_name] += 1
					continue
			except Exception as err:
				tb = traceback.extract_tb(err.__traceback__)[-1]
				printf(f"{symbol}: {primary_name} {label} failed ({err}) (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
			try:
				result = fallback_fn(symbol)
				if self.validate(result):
					out[symbol] = result
					served_by[fallback_name] += 1
					printf(f"{symbol}: {label} served by ({fallback_name})", lv.INFO)
					continue
			except Exception as err:
				tb = traceback.extract_tb(err.__traceback__)[-1]
				printf(f"{symbol}: {fallback_name} {label} failed ({err}) (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
			printf(f"{symbol}: {label} unavailable from both sources", lv.WARNING)
		if len(out) < len(symbols):
			printf(f"{label}: {len(out)}/{len(symbols)} symbols served", lv.INFO)
		breakdown = ", ".join(f"{name}: {n}" for name, n in served_by.items() if n)
		printf(f"{label} served by {breakdown}", lv.INFO)
		return out

	# --- market data: all-or-nothing per symbol's full history ---

	def prices(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> full price history rows (primary) or yfinance history_payload rows (fallback).'''
		def fallback(symbol: str):
			payload = self.fallback.history_payload(symbol)
			return payload["price_rows"] if payload else None

		return self._per_symbol(symbols, lambda s: self.primary.prices([s]).get(s), fallback, "prices")

	def dividends(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''
		symbol -> [{date, amount}] full precision.

		yfinance is primary: DefeatBeta stores split-adjusted amounts
		rounded to 2dp, which zeroes out tiny pre-split dividends.
		DefeatBeta stays as fallback. Lists containing amount == 0 are
		rejected (a real dividend is never 0 - that's source corruption).
		'''
		def divs_valid(rows) -> bool:
			return bool(rows) and all(r.get("amount") != 0 for r in rows)

		# yfinance primary (full precision), DefeatBeta fallback.
		# Note the FailoverSource constructor still lists DefeatBeta first -
		# prices/splits use it as primary. Dividends intentionally invert,
		# so pass names explicitly to keep logs/counters truthful.
		def primary(symbol: str):
			payload = self.fallback.history_payload(symbol)
			return payload["div_events"] if payload else None

		def fallback(symbol: str):
			rows = self.primary.dividends([symbol]).get(symbol)
			return rows if divs_valid(rows) else None

		def primary_validated(symbol: str):
			rows = primary(symbol)
			return rows if divs_valid(rows) else None

		return self._per_symbol(
			symbols, primary_validated, fallback, "dividends",
			primary_name=type(self.fallback).__name__,
			fallback_name=type(self.primary).__name__,
		)

	def splits(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> [{date, factor}] from primary events or yfinance history payload.'''
		def fallback(symbol: str):
			payload = self.fallback.history_payload(symbol)
			return payload["split_events"] if payload else None

		return self._per_symbol(symbols, lambda s: self.primary.splits([s]).get(s), fallback, "splits")

	def shares_outstanding(self, symbols: list[str]) -> dict[str, float | None]:
		'''symbol -> latest shares; fallback reads info().sharesOutstanding.'''
		def fallback(symbol: str):
			info = self.fallback.info(symbol)
			return info.get("sharesOutstanding") if info else None

		return self._per_symbol(symbols, lambda s: self.primary.shares_outstanding([s]).get(s), fallback, "shares")

	# --- DefeatBeta-only calls the pipeline makes: delegate to primary ---

	def us_members(self, symbols: list[str]) -> set[str]:
		return self.primary.us_members(symbols)

	def officers(self, symbols: list[str]) -> dict[str, list[dict]]:
		return self.primary.officers(symbols)

	def statements(self, symbols: list[str], finance_type: str, period_type: str = "annual") -> dict[str, list[dict]]:
		return self.primary.statements(symbols, finance_type, period_type)

	# --- profiles: fail over freely per call ---

	def profiles(self, symbols: list[str]) -> dict[str, dict]:
		def fallback(symbol: str):
			info = self.fallback.info(symbol)
			return info or None

		return self._per_symbol(symbols, lambda s: self.primary.profiles([s]).get(s), fallback, "profiles")
