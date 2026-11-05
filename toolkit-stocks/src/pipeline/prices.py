from datetime import datetime, timezone

from datasource.quotes_batch import QuotesBatchSource
from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_quote_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import (
	get_latest_market_times,
	get_latest_share_issued,
	get_missing_market_caps,
	insert_rows_bulk,
)
import constants.db_tables as dbt

# Flush size for stock_quote upserts: rows are small (one per symbol), and
# 4000-row flushes are a single execute_values page.
QUOTE_FLUSH_SIZE = 1000

# Markets where the quote moves during these states; everything else
# (CLOSED/PRE*/post*) only gets written when regularMarketTime is newer
# than stored (missed close catch-up).
LIVE_MARKET_STATES = {"REGULAR", "POST", "POSTPOST"}

# Own market-cap calc (price x share_issued) diverging from Yahoo marketCap
# by more than this ratio logs a warning. Log-only: own value still wins —
# Yahoo is frequently the stale side (foreign filings lag months; Samsung).
CAP_DIVERGENCE = 0.02


def own_market_cap(quote: dict, shares: float | None, symbol: str) -> None:
	'''
	Override quote["market_cap"] in place with own calc: stock_price x latest
	filing share_issued. Yahoo marketCap stays untouched as the fallback when
	own inputs (price or shares) are missing/invalid. Divergence >2% vs Yahoo
	warns (log-only; own value still wins).
	'''
	price = quote.get("stock_price")
	if not shares or not price or price <= 0:
		return

	own = price * float(shares)
	yahoo = quote.get("market_cap")
	if yahoo and yahoo > 0:
		ratio = own / yahoo
		if abs(ratio - 1) > CAP_DIVERGENCE:
			printf(
				f"{symbol}: market_cap divergence own {own:.0f} vs yahoo {yahoo:.0f} (ratio {ratio:.3f})",
				lv.WARNING,
			)
	quote["market_cap"] = own


def should_write(quote: dict, stored_time: datetime | None) -> bool:
	'''
	Hourly gating: write live quotes from open/near-open markets, and closed
	markets only when the last regularMarketTime is newer than what the DB
	stores (missed close). Never-known symbols always write.
	'''
	state = quote.get("market_state")
	if state in LIVE_MARKET_STATES:
		return True

	raw_time = quote.get("regular_market_time")
	if raw_time is None:
		return False
	fetched_time = datetime.fromtimestamp(int(raw_time), tz=timezone.utc)
	return stored_time is None or fetched_time > stored_time


def run_quote(symbols: list[str], stock_ids: dict[str, int], force: bool = False) -> dict:
	'''
	Quote phase: one batched v7/quote call per 500 symbols, gated writes to
	stock_quote. No historical prices, no per-symbol requests.

	market_cap provenance: own calc (stock_price x latest filing
	share_issued from stock_statement_balance) primary; Yahoo marketCap stays
	only as the fallback when own inputs are missing (see own_market_cap).
	'''
	stats = new_phase("quote", len(symbols))
	src = QuotesBatchSource()

	known_ids = [stock_ids[s] for s in symbols if stock_ids.get(s) is not None]
	stored_times = get_latest_market_times(known_ids)
	missing_cap_ids = get_missing_market_caps(known_ids)
	share_issued = get_latest_share_issued(known_ids)

	rows: list[dict] = []
	quotes = src.fetch(symbols)
	for symbol in symbols:
		quote = quotes.get(symbol)
		stock_id = stock_ids.get(symbol)
		if quote is None or stock_id is None:
			count_symbol(stats, False, symbol)
			continue
		own_market_cap(quote, share_issued.get(stock_id), symbol)
		if not force and not should_write(quote, stored_times.get(stock_id)):
			# closed market, nothing new: skip, not a failure — unless the
			# stored row lacks market_cap and this fetch has one (self-heal)
			if quote.get("market_cap") is None or stock_id not in missing_cap_ids:
				stats["skipped_fresh"] = stats.get("skipped_fresh", 0) + 1
				continue
		row = build_quote_row(symbol, stock_id, quote)
		if not row:
			count_symbol(stats, False, symbol)
			continue
		rows.append(row)
		count_symbol(stats, True, rows=1)

	# chunked flush
	written = 0
	for i in range(0, len(rows), QUOTE_FLUSH_SIZE):
		written += insert_rows_bulk(
			dbt.quote,
			rows[i:i + QUOTE_FLUSH_SIZE],
			conflict_keys=["stock_id"],
		)
	skipped = stats.get("skipped_fresh", 0)
	stats["rows_written"] = written
	printf(
		f"quote: {written}/{len(rows)} quote rows written, {skipped} skipped",
		lv.INFO,
	)
	return stats
