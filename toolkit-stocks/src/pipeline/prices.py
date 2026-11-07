from datetime import datetime, timezone

from datasource.quotes_batch import QuotesBatchSource
from lib.functions.stats import count_symbol, new_phase
from lib.transforms import build_quote_row
from lib.module.printf import printf, level as lv
from lib.supabase.sql_functions import (
	get_latest_market_times,
	get_latest_shares_outstanding,
	get_missing_market_caps,
	get_split_factors,
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

# Own market-cap calc (price x shares outstanding) diverging from Yahoo
# marketCap by more than this ratio logs a warning. Log-only: own value
# still wins — Yahoo is frequently the stale side (foreign filings lag
# months; Samsung).
CAP_DIVERGENCE = 0.02

# Clean ADR ratios: when own/yahoo divergence snaps to one of these within
# ADR_SNAP_TOLERANCE, the divergence is a share-basis mismatch (quote price
# is the ADR price, shares outstanding counts ordinary shares), not stale
# data. own / ratio is then the corrected market cap (own-calc stays
# primary).
ADR_RATIOS = {0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 2, 4, 5, 10, 20, 25, 50}
ADR_SNAP_TOLERANCE = 0.01


def adjusted_shares(shares: float, fiscal_date, splits: list[tuple]) -> float:
	'''Rebase a filing's shares outstanding to today's share basis: every
	split AFTER the filing's fiscal_date multiplies the count. E.g. SMFG
	(8316.T): filing 2026-06-30 reports 3.83B shares, 2-for-1 split
	2026-09-29 -> 7.65B post-split shares matching today's post-split
	price.'''
	# float() guards against Decimal share counts from the DB: Decimal * float raises TypeError
	for split_date, factor in splits:
		if split_date > fiscal_date:
			shares = float(shares) * float(factor)
	return shares


def derive_adr_ratio(own: float, yahoo: float) -> float | None:
	'''ADR ratio implied by the own/yahoo divergence, snapped to a clean
	fraction; None when the divergence is not a clean basis mismatch.
	AMX (1 ADR = 20 shares): own = ADR price x all ordinary shares is
	exactly 20x the true cap -> ratio 20. KEP (1 ADR = 0.5 shares) -> 0.5.'''
	ratio = own / yahoo
	for candidate in ADR_RATIOS:
		if abs(ratio / candidate - 1) <= ADR_SNAP_TOLERANCE:
			return candidate
	return None


def own_market_cap(quote: dict, shares: float | None, symbol: str) -> None:
	'''
	Override quote["market_cap"] in place with own calc: stock_price x latest
	filing shares outstanding (ordinary, else issued - treasury, else
	issued; split-adjusted to today's share basis). Yahoo marketCap stays
	untouched as the fallback when own inputs (price or shares) are
	missing/invalid - shares <= 0 counts as invalid: Yahoo occasionally
	carries dollar values in share-count fields (RY.TO preferred = C$14B)
	or zero-fills ordinary counts, and a negative count must never write a
	negative market cap.

	Divergence handling vs Yahoo (>2% warns, log-only):
	- clean ADR fraction (within 1%) -> share-basis mismatch: own is
	  corrected by the derived ratio (own / ratio) and stays primary;
	- anything else -> own value still wins (Yahoo frequently the stale
	  side: foreign filings lag months; Samsung counts preferred shares).
	'''
	price = quote.get("stock_price")
	if not shares or shares <= 0 or not price or price <= 0:
		return

	own = price * float(shares)
	yahoo = quote.get("market_cap")
	if yahoo and yahoo > 0:
		ratio = own / yahoo
		adr_ratio = derive_adr_ratio(own, yahoo)
		if adr_ratio is not None:
			printf(
				f"{symbol:<10}: market_cap divergence own {own:.0f} vs yahoo {yahoo:.0f} "
				f"(ratio {ratio:.3f}, ADR {adr_ratio:g}x -> {ratio / adr_ratio:.3f}), "
				f"own cap corrected to {own / adr_ratio:.0f}",
				lv.INFO,
			)
			own /= adr_ratio
		elif abs(ratio - 1) > CAP_DIVERGENCE:
			printf(
				f"{symbol:<10}: market_cap divergence own {own:.0f} vs yahoo {yahoo:.0f} (ratio {ratio:.3f})",
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

	market_cap provenance: own calc (stock_price x latest filing shares
	outstanding from stock_statement_balance) primary; Yahoo marketCap stays
	only as the fallback when own inputs are missing (see own_market_cap).
	'''
	stats = new_phase("quote", len(symbols))
	src = QuotesBatchSource()

	known_ids = [stock_ids[s] for s in symbols if stock_ids.get(s) is not None]
	stored_times = get_latest_market_times(known_ids)
	missing_cap_ids = get_missing_market_caps(known_ids)
	shares_outstanding = get_latest_shares_outstanding(known_ids)
	split_factors = get_split_factors(known_ids)

	rows: list[dict] = []
	quotes = src.fetch(symbols)
	for symbol in symbols:
		quote = quotes.get(symbol)
		stock_id = stock_ids.get(symbol)
		if quote is None or stock_id is None:
			count_symbol(stats, False, symbol)
			continue
		outstanding = shares_outstanding.get(stock_id)
		shares = None
		if outstanding is not None:
			filing_shares, fiscal_date = outstanding
			shares = adjusted_shares(filing_shares, fiscal_date, split_factors.get(stock_id, []))
		own_market_cap(quote, shares, symbol)
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
