# Quarterly statement fetch gating (daily pipeline).
# A symbol is stale when today - max(newest fiscal_date across the three
# statement tables) > QUARTERLY_FISCAL_WINDOW_DAYS. A stale symbol is
# suppressed while a known future earnings event sits beyond the lookahead
# window, but never when its gap exceeds MAX_SUPPRESSION_GAP_DAYS.
QUARTERLY_FISCAL_WINDOW_DAYS = 95
EARNINGS_EVENT_LOOKAHEAD_DAYS = 7	# must stay < calendar sweep window (14d)
MAX_SUPPRESSION_GAP_DAYS = 180	# never suppress data missing >~2 quarters

# Staggered revision sweep: each day refetch 1/N of symbols whose newest
# quarterly fiscal_date is still revision-prone (<= window days old). Catches
# restatements/adjustments that carry no earnings-calendar signal; worst-case
# revision lag drops from the 95d fresh window to N days. Deterministic shard
# (stock_id mod N == day bucket) — no state, no extra cron jobs.
QUARTERLY_SWEEP_WINDOW_DAYS = 180
QUARTERLY_SWEEP_BUCKETS = 7
