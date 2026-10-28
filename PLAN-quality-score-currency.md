# PLAN: quality score currency bug (planned, not done)

## Problem

Quality score min-max normalizes each metric per industry peer group (0–100). Two scored metrics are raw local-currency amounts, not ratios:

- `earning_per_share` — statement currency (USD 5 vs JPY 200+ vs GBP 3)
- `revenues_per_share` — same, revenue per share in local currency

Peer groups mix countries (US + UK + JP in same industry). JPY scale pins the max; non-yen peers crushed toward 0. Affects groups:

- `profitability_earnings` (weight 0.25) — via EPS
- `growth_quality` (weight 0.20) — via revenues_per_share

## Fix plan

- Drop `earning_per_share` + `revenues_per_share` from `GROUPS` in `src/domain/financial_quality_score/utils/constants.py` (keep in `METRIC_COLUMNS` / DB).
- Both redundant: ROE + net_margin cover profitability; revenue_growth covers growth.
- Redistribute removed metric weight within each affected group (remaining 4 metrics share equally).
- Update `HIGHER_IS_BETTER` entries not required if only GROUPS references scoring — verify no other code iterates GROUPS expecting those keys (`quality_score.py`).
- Re-run `--fa` to recompute quality scores.
- Tests: check golden/unit tests asserting group metric lists.

## Done

- GBp pe_ratio fix (see PLAN.md item marked FIXED).
