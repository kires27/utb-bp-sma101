import time
import traceback

from lib.functions.netstats import incr_yf
from lib.module.printf import printf, level as lv


CHUNK_SIZE = 500
MAX_RETRIES = 4
QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

GBP_STYLE_CURRENCIES = ("GBp", "GBX")


class QuotesBatchSource:
	'''
	Batched v7/finance/quote source via yfinance's own request machinery
	(YfData.get_raw_json). One request per <=500-symbol chunk: Yahoo's rate
	limiter counts requests, not payload size, so batching is ~free.

	Returns the same normalized quote dict as YFinanceSource.quote() plus
	extra gating fields (market_state, currency, volume) the quote phase
	uses to skip closed markets. No DB writes.
	'''

	def __init__(self, chunk_size: int = CHUNK_SIZE):
		from yfinance.data import YfData

		self._data = YfData()
		self._chunk_size = chunk_size

	def _chunks(self, symbols: list[str]):
		for i in range(0, len(symbols), self._chunk_size):
			yield symbols[i:i + self._chunk_size]

	def _fetch_chunk(self, symbols: list[str]) -> list[dict]:
		'''Raw quote records for one chunk, with backoff on rate limits.'''
		import yfinance as yf

		for attempt in range(MAX_RETRIES):
			incr_yf()
			try:
				resp = self._data.get_raw_json(QUOTE_URL, params={"symbols": ",".join(symbols)})
				return resp.get("quoteResponse", {}).get("result") or []
			except yf.YFRateLimitError as err:
				wait = 2 ** attempt
				printf(f"quotes_batch: rate limited, retry in {wait}s ({err})", lv.WARNING)
				time.sleep(wait)
		printf(f"quotes_batch: giving up after {MAX_RETRIES} retries (chunk of {len(symbols)})", lv.ERROR)
		return []

	def fetch(self, symbols: list[str]) -> dict[str, dict]:
		'''symbol -> normalized quote dict; symbols absent from Yahoo response are omitted.'''
		out: dict[str, dict] = {}
		for chunk in self._chunks(symbols):
			try:
				records = self._fetch_chunk(chunk)
			except Exception as err:
				tb = traceback.extract_tb(err.__traceback__)[-1]
				printf(f"quotes_batch chunk failed: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
				continue
			for record in records:
				symbol = record.get("symbol")
				if not symbol:
					continue
				out[symbol] = self._normalize(record)
		printf(f"quotes_batch: {len(out)}/{len(symbols)} symbols fetched", lv.INFO)
		return out

	@staticmethod
	def _normalize(record: dict) -> dict:
		'''
		Raw v7/quote record -> normalized quote dict. Same five contract keys
		as YFinanceSource.quote() (stock_price, market_cap, change, change_pct,
		regular_market_time) + gating extras.
		'''
		price = record.get("regularMarketPrice")
		# Pence-quoted symbols (LSE) report price in GBp; statements are in GBP.
		# marketCap is already base currency (GBP), no scaling.
		currency = record.get("currency")
		if currency in GBP_STYLE_CURRENCIES and price is not None:
			price = price / 100

		return {
			"stock_price": price,
			"market_cap": record.get("marketCap"),
			"regular_market_change": record.get("regularMarketChange"),
			"regular_market_change_percent": record.get("regularMarketChangePercent"),
			"regular_market_time": record.get("regularMarketTime"),
			# gating extras (not part of build_quote_row contract)
			"market_state": record.get("marketState"),
			"currency": currency,
			"volume": record.get("regularMarketVolume"),
			"previous_close": record.get("regularMarketPreviousClose"),
		}
