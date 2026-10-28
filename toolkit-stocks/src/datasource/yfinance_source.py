import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.module.printf import printf, level as lv


MAX_WORKERS = 8
MAX_RETRIES = 4


class YFinanceSource:
	'''
	Per-symbol yfinance source for non-US symbols (and live quotes).
	Threaded with exponential backoff on rate limits.
	'''

	def __init__(self, max_workers: int = MAX_WORKERS):
		import logging
		import warnings

		import yfinance as yf
		import pandas as pd

		# yfinance installs its own warnings filter (^yfinance -> "default")
		# at import time, which would override any earlier "ignore" filter.
		# Re-apply after the import so Pandas4Warning noise stays suppressed.
		warnings.filterwarnings("ignore", category=pd.errors.Pandas4Warning)
		# yfinance logs raw HTTP errors (e.g. 404 for unknown tickers) to stderr
		logging.getLogger("yfinance").setLevel(logging.CRITICAL)

		self._yf = yf
		self._max_workers = max_workers

	def _ticker(self, symbol: str):
		return self._yf.Ticker(symbol)

	def map_symbols(self, fn, symbols: list[str], label: str) -> dict[str, object]:
		'''
		Run fn(symbol) per symbol on a thread pool, with backoff on rate limits.
		fn must catch its own per-call errors if a skip is preferable; results
		for symbols whose fn returned None or raised are omitted.
		'''
		out: dict[str, object] = {}

		def worker(symbol: str):
			return symbol, fn(symbol)

		with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
			futures = {pool.submit(worker, s): s for s in symbols}
			try:
				for future in as_completed(futures):
					symbol = futures[future]
					try:
						result_symbol, result = future.result()
						if result is not None:
							out[result_symbol] = result
					except Exception as err:
						tb = traceback.extract_tb(err.__traceback__)[-1]
						printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
			except KeyboardInterrupt:
				# Do not wait for in-flight yfinance calls; cancel pending work.
				pool.shutdown(wait=False, cancel_futures=True)
				printf("yfinance batch interrupted, cancelling pending fetches", lv.WARNING)
				raise

		printf(f"yfinance {label}: {len(out)}/{len(symbols)} symbols fetched", lv.INFO)
		return out

	def with_backoff(self, symbol: str, fn, *args, **kwargs):
		'''Call fn with exponential backoff on rate limit / transient errors.'''
		import yfinance as yf

		for attempt in range(MAX_RETRIES):
			try:
				return fn(*args, **kwargs)
			except yf.YFRateLimitError as err:
				wait = 2 ** attempt
				printf(f"{symbol}: rate limited, retry in {wait}s ({err})", lv.WARNING)
				time.sleep(wait)
			except Exception:
				raise
		printf(f"{symbol}: giving up after {MAX_RETRIES} retries", lv.ERROR)
		return None

	def info(self, symbol: str) -> dict | None:
		def fetch(ticker):
			data = ticker.info
			return data if data else None

		data = self.with_backoff(symbol, fetch, self._ticker(symbol))
		return data if data else None

	def profile(self, symbol: str) -> dict | None:
		return self.info(symbol)

	GBP_STYLE_CURRENCIES = ("GBp", "GBX")

	def quote(self, symbol: str) -> dict | None:
		'''Live quote fields for stock_metric, straight from info().'''
		info = self.info(symbol)
		if not info:
			return None

		price = info.get("regularMarketPrice")
		# Pence-quoted symbols (LSE) report prices in GBp; statements are in
		# GBP. Scale price to the statement currency so pe_ratio is not 100x.
		if info.get("currency") in self.GBP_STYLE_CURRENCIES and price is not None:
			price = price / 100

		return {
			"stock_price": price,
			"market_cap": info.get("marketCap"),
			"regular_market_change_percent": info.get("regularMarketChangePercent"),
			"regular_market_change": info.get("regularMarketChange"),
			"regular_market_time": info.get("regularMarketTime"),
			# yfinance reports percent (2.94); normalize to fraction for fac.dividend_yield
			"dividend_yield": (info.get("dividendYield") / 100) if info.get("dividendYield") else None,
		}

	def history(self, symbol: str, period: str = "max") -> object | None:
		'''Daily OHLCV + Adj Close + Dividends + Stock Splits, unadjusted close.'''
		def fetch(ticker):
			df = ticker.history(period=period, interval="1d", auto_adjust=False)
			if df is None or df.empty:
				return None
			return df

		return self.with_backoff(symbol, fetch, self._ticker(symbol))

	def statements(self, symbol: str, kind: str, period: str = "annual") -> object | None:
		'''
		kind: income_statement | balance_sheet | cash_flow
		Returns the transposed yfinance DataFrame (line items as index, dates as columns)
		or None. Period: "annual" | "quarterly".
		'''
		def fetch(ticker):
			if period == "quarterly":
				df = {
					"income_statement": ticker.quarterly_income_stmt,
					"balance_sheet": ticker.quarterly_balance_sheet,
					"cash_flow": ticker.quarterly_cashflow,
				}[kind]
			else:
				df = {
					"income_statement": ticker.income_stmt,
					"balance_sheet": ticker.balance_sheet,
					"cash_flow": ticker.cashflow,
				}[kind]
			if df is None or df.empty:
				return None
			return df

		return self.with_backoff(symbol, fetch, self._ticker(symbol))

	def statements_payload(self, symbol: str, kind: str, period: str = "annual") -> list[dict] | None:
		'''Normalized grouped statement records: [{report_date, <normalized_field>: value}].'''
		from datasource.base import normalize_title

		df = self.statements(symbol, kind, period)
		if df is None:
			return None

		grouped = []
		for date_col in df.columns:
			record = {"report_date": str(date_col.date())}
			for item_name, value in df[date_col].items():
				record[normalize_title(str(item_name))] = value
			grouped.append(record)
		return grouped

	def history_payload(self, symbol: str, period: str = "max") -> dict | None:
		'''
		Normalized market payload from one history call:
		{price_rows: [{date, open, high, low, close, volume}],
		div_events: [{date, amount}], split_events: [{date, factor}]}
		'''
		df = self.history(symbol, period)
		if df is None:
			return None

		price_rows = []
		div_events = []
		split_events = []
		for idx, row in df.iterrows():
			d = str(idx.date() if hasattr(idx, "date") else idx)[:10]
			price_rows.append({
				"date": d,
				"open": row.get("Open"),
				"high": row.get("High"),
				"low": row.get("Low"),
				"close": row.get("Close"),
				"volume": row.get("Volume"),
			})
			div = row.get("Dividends")
			if div is not None and float(div) != 0:
				div_events.append({"date": d, "amount": float(div)})
			spl = row.get("Stock Splits")
			if spl is not None and float(spl) != 0:
				split_events.append({"date": d, "factor": float(spl)})

		return {"price_rows": price_rows, "div_events": div_events, "split_events": split_events}
