# Plan: Quarterly statements staleness-window gating ("gap trigger")

## Goal
Add quarterly financial statements fetching to the daily pipeline, gated by a
self-healing staleness window: only fetch a symbol when its newest stored
fiscal_date is older than ~95 days. Fetch daily until fresh again.

Rejected alternatives (see evaluation):
- Fetch-all daily (~4.4M req/yr, 97% redundant fetches).
- Hand-predicted fiscal calendar (silent-staleness failure mode).
- Yahoo announced earnings dates (v2 optimizer only, ~10x saving but needs
  sweep machinery + fallback; possible silent staleness if buggy).

## Why this design
- Failure mode is *wasted fetches*, never *stale data* — loop keeps fetching
  until condition met. Covers late filings, 4-4-5 fiscal calendars, IPOs
  (infinite gap -> fetch immediately), data gaps automatically.
- Zero extra API calls; one batched SQL query reusing existing infra.
- Estimated ~1.4M statement requests/yr vs 4.4M fetch-all (~3x saving).

## Design details

### Window logic (quarterly)
- Trigger: `today - newest_fiscal_date > QUARTERLY_WINDOW_DAYS` (~95 days).
- Data actually lands at gap ~105-133 days (quarter end + filing lag +
  Yahoo lag), so a 95d trigger gives a ~2-3 week daily-fetch window that
  catches the new quarter promptly without weeks of dead fetching.
- Annual keeps existing `FRESH_FISCAL_WINDOW_DAYS = 380` (same pattern).
- `--force` / `--full` bypass, matching current behavior.

### One trigger query for all three statements
- All three statements (balance/cash/income) publish together -> take the
  MAX newest fiscal_date across the three tables per stock as the trigger
  (or balance-sheet as proxy). One batched query, not three.
- Per-kind staleness windows would triple the query for no benefit.

### Freshness stamps
- Reuse `touch_statement_rows` stamping semantics: a fetched symbol gets
  stamped even if every row was a duplicate; fresh-skipped symbols get
  bumped too (existing behavior in `run_statements`).

## Implementation steps (toolkit-stocks)

1. **constants** — add `QUARTERLY_FISCAL_WINDOW_DAYS = 95` (or rename the
   annual constant into a shared shape, e.g. two constants in one place).
2. **sql** — extend `get_fresh_stock_ids` (or add a sibling) in
   `src/lib/supabase/sql_functions.py`:
   - accept a period-aware variant; compute newest fiscal_date across the
     three statement tables per stock (MAX), filter ids where
     `today - newest <= window` AND rows stamped.
   - keep NULL-stamp legacy rows treated as stale (refetch + stamp once).
3. **pipeline** — extend `src/pipeline/statements.py`:
   - `run_statements()` currently hardcodes `period_type = "annual"`;
     parametrize it (annual | quarterly) and select the matching window.
   - quarterly run calls `yfs.statements_payload(sym, kind, "quarterly")`
     for stale symbols only.
   - keep RowFlusher conflict keys `[stock_id, fiscal_date, period]` so
     quarterly rows upsert cleanly and restatements DO update.
4. **runner** — wire the quarterly phase into `run_mode("daily")` phase
   order after the annual statements phases; keep backfill/full behavior
   (full fetch incl. quarterly, no metrics).
5. **transforms** — verify `build_statement_rows` handles quarterly
   records (period mapping `Q1`-`Q4` vs `FY`); adjust if it assumes annual.

## Tests
- Unit: window boundary math (gap 94 / 95 / 96 days), max-across-tables
  query helper, legacy NULL-stamp rows treated stale.
- Golden: quarterly payload -> expected rows (reuse fixture pattern from
  `tests/capture_fixtures.py`).
- Full suite: `python -m pytest tests/` (from `toolkit-stocks/`, venv).

## Verification (live, after deploy)
- Watch daily run logs: `"<table>: N/M symbols stale/unknown -> fetch"` —
  expect N to spike around the first rollout (legacy stamps) then settle
  to roughly (symbols in window) per day.
- Confirm `stock_*_statement` quarterly rows appear post-filing with the
  expected lag, and no symbol goes stale beyond window + filing lag.
- Optionally log fetched-count/day to sanity-check the ~1.4M/yr estimate
  before considering the earnings-date v2 optimizer.

## Out of scope (v2)
- Yahoo earnings-date narrowing of the window (would cut ~1.4M -> ~300k
  fetches/yr) — only if volume proves costly. Never as the sole gate.
