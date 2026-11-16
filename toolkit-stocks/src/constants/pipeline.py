# Quarterly statement fetch gating (daily pipeline).
# A symbol is stale when today - max(newest fiscal_date across the three
# statement tables) > QUARTERLY_FISCAL_WINDOW_DAYS. A stale symbol is
# suppressed while a known future earnings event sits beyond the lookahead
# window, but never when its gap exceeds MAX_SUPPRESSION_GAP_DAYS.
QUARTERLY_FISCAL_WINDOW_DAYS = 95
EARNINGS_EVENT_LOOKAHEAD_DAYS = 7	# must stay < calendar sweep window (calendar.yml window_days)
MAX_SUPPRESSION_GAP_DAYS = 180	# never suppress data missing >~2 quarters

# Staggered revision sweep: each day refetch 1/N of symbols whose newest
# quarterly fiscal_date is still revision-prone (<= window days old). Catches
# restatements/adjustments that carry no earnings-calendar signal; worst-case
# revision lag drops from the 95d fresh window to N days. Deterministic shard
# (stock_id mod N == day bucket) — no state, no extra cron jobs.
QUARTERLY_SWEEP_WINDOW_DAYS = 180
QUARTERLY_SWEEP_BUCKETS = 7

# Fallback stagger for stale symbols the earnings calendar cannot protect:
# stale (> window) AND not suppressed AND no calendar signal means the old
# rule fetched them EVERY day (calendar coverage is sparse — only ~1/3 of
# symbols ever get an earnings row). Instead, rotate them 1/N per day, same
# shard scheme as the sweep. Worst-case new-report detection lag = N days.
# Unknown symbols (no rows at all) always fetch immediately, never staggered.
QUARTERLY_STAGGER_BUCKETS = 3

# Overview refetch cadence: stock.maintenance_update older than this (or NULL)
# triggers a profile refetch. Daily profile changes are rare; weekly is enough.
OVERVIEW_MAX_AGE_DAYS = 7

# Symbol column width for log lines (f"...{symbol:<{SYMBOL_COL_WIDTH}}...").
# Universe max today: BHARTIARTL.NS (13). One char headroom; the screener can
# discover longer tickers, which then overflow the column by a few chars.
SYMBOL_COL_WIDTH = 14

# Human-readable labels for quarterly fetch/skip reasons, keyed by the
# classification the SQL in get_quarterly_fetch_ids assigns. Log lines compose
# from these so every message explains the term inline (why fetched / skipped).
REASON_LABELS = {
	# fetch reasons
	"unknown": "first fetch (no statement rows)",
	"sweep": "revision sweep (restatement re-check)",
	"gap_too_old": f"filing older than {MAX_SUPPRESSION_GAP_DAYS}d (suppression unsafe)",
	"stale_event_near": f"earnings report due within {EARNINGS_EVENT_LOOKAHEAD_DAYS}d",
	"stale_no_event": "stale, no earnings date on calendar",
	# skip reasons
	"fresh": f"fresh (last filing within {QUARTERLY_FISCAL_WINDOW_DAYS}d)",
	"suppressed": f"suppressed (earnings beyond {EARNINGS_EVENT_LOOKAHEAD_DAYS}d, filing under {MAX_SUPPRESSION_GAP_DAYS}d)",
	"waiting_stagger": f"awaiting stagger shard (1/{QUARTERLY_STAGGER_BUCKETS} daily rotation)",
	"unstamped": "legacy rows unstamped (one-time refetch)",
}

# Labels that mean the symbol IS fetched this run; the rest are skip reasons.
FETCH_REASON_LABELS = {"unknown", "sweep", "gap_too_old", "stale_event_near", "stale_no_event"}
