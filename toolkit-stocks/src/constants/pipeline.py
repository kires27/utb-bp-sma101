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
