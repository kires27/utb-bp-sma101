# PLAN: split-trigger recalculation (dividends + adj_close)

## Problem

`stock_dividend.dividend` stores **split-adjusted** amounts (today-basis, not
declared). When a NEW split is inserted into `stock_split`, older dividend rows
keep the old basis → TTM yield / yield-based metrics wrong.

Goal: on new-split insert, recalculate split-adjusted dividend amounts **from data already in DB**. No refetching.

## Design (anti-corruption)

**ONE new column, on `stock_dividend` only:** `adjusted_through date` —
"this dividend amount already includes all splits up to this date".
Prevents double-division by the trigger.

| Table | Change |
|---|---|
| `stock_dividend` | 1 new column `adjusted_through` (date) |
| `stock_split` | NO schema change — AFTER INSERT trigger only |

**Trigger behavior** (AFTER INSERT, valid factor):
1. Divide dividend rows where `date < NEW.date AND adjusted_through < NEW.date`;

**Pipeline stamping**: every new dividend row gets
`adjusted_through = max(newest payload split date, newest DB split date for that
stock)` (sentinel `2026-10-23` if none) — protects today-basis values from being
re-divided by later triggers regardless of insert order.

**`build_split_rows` sorts events ascending (oldest first)** so multi-split
batches apply in order.

Backfill idempotency: trigger-set `adjusted_through` always equals the newest
split date in DB (max split date), so re-running the backfill is a no-op.

## Part 1 — SQL migration

`toolkit-stocks/sql/2026-10-27_split_trigger_recalc.sql` (manual apply to Supabase)

1. `alter table stock_dividend add column if not exists adjusted_through date default '2026-10-23'` + backfill (per-stock max split date, else sentinel).
4. `on_new_split()` trigger function + `trg_stock_split_recalc` trigger (AFTER INSERT only).

## Part 2 — pipeline write hardening (Python)

1. `src/lib/transforms/events.py`: `build_dividend_rows` gets `adjusted_through`
   stamp param + module constant `SPLIT_SENTINEL_DATE = "2026-10-23"`;
   `build_split_rows` sorts ascending.
3. `src/lib/supabase/sql_functions.py`: add `get_latest_split_date(stock_id)`
4. Dividends stay incremental (`latest_div_dates` filter); splits stay
   `ON CONFLICT DO NOTHING` (prevents trigger re-fire).

## Part 3 — verification

1. Python-vs-SQL parity on NVDA / AAPL / 8802.T (`scripts/verify_split_trigger.py`).
3. Duplicate-insert safety (no re-fire, no double division).
4. Regression spot-check: NVDA 2012 dividend = 0.001875; NVDA 2021-07-20 4:1 

## Part 4 — docs

- Migration header comment.
- `AGENTS.md` toolkit-stocks note: dividends stored split-adjusted (today-basis);
  new splits rebasis older dividends
  pipeline must NEVER update `stock_split` (INSERT DO NOTHING only); new dividend
  rows must be stamped with `adjusted_through`.

## Risks

- Double-division is THE failure mode → guarded by `adjusted_through < NEW.date`
  (idempotent by construction) + INSERT-only trigger + DO-NOTHING upsert.
- Splits must insert oldest-first within a batch (trigger row-by-row ordering) —
  pipeline sorts ascending.
- Migration applied manually (no local `supabase/` dir in this repo).

## Status

- [ ] Part 1: SQL migration (column + backfill + product aggregate + recompute fn + trigger)
- [ ] Part 2: pipeline stamping + split ordering + intl fixes + recompute calls
- [ ] Unit tests updated (`test_transforms_events.py`); full suite green
- [ ] Migration applied to Supabase
- [ ] Part 3: verification script run
- [ ] Part 4: docs
