'''FX phase: backfill + daily refresh of fx_rate, one row per currency
quoted against USD (Yahoo {CCY}=X series: value = CCY per 1 USD). Standalone
like calendar/exchange -- no symbol discovery, no RunContext. Runs BEFORE fa
in the daily set so the FA transform can look up statement->trading-currency
rates at each row's vintage date without any network dependency inside FA.

Backfill (missing pair) uses period="max" in one request; daily refresh uses
period="1y". force re-runs the full max backfill (idempotent upsert).

fx_rate uses reserved words "from"/"to" as columns: writes go through
RowFlusher (insert_rows_bulk quotes every column identifier); never
interpolate those column names raw in SQL strings.'''
import traceback

from datasource import YFinanceSource
from lib.functions.stats import new_phase, count_symbol
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import RowFlusher
import constants.db_tables as dbt


# Currencies seen in stock.statement_currency / stock_quote.currency.
# GBP included: Yahoo serves GBP=X, and cross-listed stocks (ULVR.L) need it
# even though pence quotes are normalized to GBP before storing.
CURRENCIES = [
	"AUD", "BRL", "CAD", "CHF", "CNY", "DKK", "EUR", "GBP", "HKD", "INR",
	"JPY", "KRW", "MXN", "NOK", "PLN", "SEK", "SGD", "TRY", "TWD",
]
BASE = "USD"
# fx_rate PK is (from, to, rate_date).
CONFLICT_KEYS = ["from", "to", "rate_date"]
FLUSH_SIZE = 5000


def fetch_pair_rates(yfs: YFinanceSource, ccy: str, period: str) -> dict | None:
	'''{date: rate} for one currency vs USD, or None on failure. fx_history
	backoffs internally; this guards the outer per-pair error path.'''
	try:
		return yfs.fx_history(ccy, period=period)
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"fx {ccy}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return None


def build_fx_rows(ccy: str, rates: dict) -> list[dict]:
	'''{date: rate} -> fx_rate rows (from=USD, to=ccy, rate). Empty dict is
	valid: the {CCY}=X series can come back empty -> warning, not a failure.
	Rate rounded to 6 decimals: Yahoo serves full double precision, 6 dp keeps
	>=3 sig figs even for the smallest rates (KRW ~0.0007).'''
	return [
		{"from": BASE, "to": ccy, "rate_date": date, "rate": round(rate, 6)}
		for date, rate in sorted(rates.items())
	]


def run_fx(force: bool = False, currencies: list[str] | None = None) -> dict:
	'''Backfill/refresh fx_rate. force re-runs the full "max" backfill;
	otherwise each pair refreshes with a "1y" history (upsert is idempotent,
	older rows untouched).'''
	pairs = currencies if currencies is not None else CURRENCIES
	stats = new_phase("fx", len(pairs))
	yfs = YFinanceSource()
	flusher = RowFlusher(dbt.fx_rate, flush_size=FLUSH_SIZE, conflict_keys=CONFLICT_KEYS)

	printf(f"-- fx rates: {len(pairs)} pairs --", lv.INFO)
	for ccy in pairs:
		printf(f"---- {BASE}/{ccy} fx --", lv.INFO)
		period = "max" if force else "1y"
		rates = fetch_pair_rates(yfs, ccy, period)
		if rates is None:
			count_symbol(stats, False, ccy)
			continue
		rows = build_fx_rows(ccy, rates)
		if not rows:
			printf(f"fx {ccy}: empty {period} history from Yahoo", lv.WARNING)
			count_symbol(stats, False, ccy)
			continue
		flusher.add(rows)
		count_symbol(stats, True, rows=len(rows))

	written = flusher.finish()
	printf(f"fx: {written} rows written across {len(pairs)} pairs", lv.INFO)
	stats["rows_written"] = written
	return stats
