# README

[![Toolkit stocks hourly](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-hourly.yml/badge.svg)](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-hourly.yml)
[![Toolkit stocks calendar](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-calendar.yml/badge.svg)](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-calendar.yml)
[![Toolkit stocks daily](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-daily.yml/badge.svg)](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-daily.yml)
[![Toolkit stocks discover](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-discover.yml/badge.svg)](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-discover.yml)
[![Toolkit stocks tests](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-tests.yml/badge.svg)](https://github.com/kires27/utb-bp-sma101/actions/workflows/toolkit-stocks-tests.yml)


# Commands

## Git

### Inspect branch state
`git log --oneline --graph --decorate --all -20`

### .gitignore
If file already tracked, .gitignore does nothing. Remove from index:
`git rm --cached path/to/file`

or do for whole repo:
```sh
git rm -r --cached .
git add .
git commit -m ""
```

### Workflow — work on dev
```sh
git switch develop
git pull
git add .
git commit -m "Describe your changes"
git push
```

### Workflow — release to prod
```sh
git switch prod
git pull
git merge --ff-only develop
git push
```

### Upstream
Check tracking: `git branch -vv`
Setup upstream (usually on first push): `git push -u origin prod`

## Python

**Create a virtual environment:** `python3 -m venv venv`

**Activation:** `source ./.venv/bin/activate` · deactivate: `deactivate` · list packages: `pip list`

**Get python requirements:** `pip freeze > requirements.txt`

---

# Repo Layers

## toolkit-stocks (stock data pipeline)

Fetches financial data from yfinance, transforms it, and uploads it to Supabase/PostgreSQL. Consumed by the web app. Built to scale to ~4000 stocks (see `PLAN-rewrite-toolkit.md`).

### How it works (data flow)

```
symbols (--symbols db | file | screener)
    │  db = already in `stock` · file = manual list · screener = auto-discovery
    ▼
1. FETCH ────── yfinance only, two modes
    hourly:  batched v7/quote (≤500 symbols/call), marketState-gated
    daily/backfill: per-symbol threaded history() + statements + profile
                    (daily incremental from last stored date, backfill = full)
    calendar: paginated POST sweep of Yahoo's v1/finance/visualization
              endpoint (earnings by region + global economic events)
    │
    ▼
2. TRANSFORM ── payloads → DB rows (lib/transforms/)
    e.g. recompute dividend/split-adjusted close over
    full history, group statement line items per report date,
    map fields to the DB schema
    │
    ▼
3. ENRICH ───── business logic (domain/)
    financial-analysis metrics (ROE, margins, growth…),
    peer-normalized quality score, DCF intrinsic value
    │
    ▼
4. UPLOAD ───── psycopg2 → PostgreSQL/Supabase
    chunked bulk inserts (RowFlusher), per-table conflict strategy
    (stock, stock_historical_price, stock_statement_*, stock_quote,
    stock_financial_analysis …)
```

Entry: `src/main.py --run <hourly|daily|backfill|calendar> --symbols <db|file|screener>` → `pipeline/runner.py:run_mode()` composition table:
- **hourly** — batched quotes → prices (gated on marketState / newer regularMarketTime)
- **daily** — overview → statements → market data → metrics → financial analysis
- **backfill** — same order as daily, full-history fetch, metrics skipped
- **calendar** — standalone Yahoo earnings + economic event sweep → `stock_economic_calendar` (tier-2 statement optimizer; also appended as a final daily phase)

### Commands

```sh
cd toolkit-stocks
source .venv/bin/activate
pip install -r requirements.txt          # .env needs DATABASE_URL

# run pipeline
python3 src/main.py --run hourly --symbols db            # hourly prices
python3 src/main.py --run daily --symbols db             # full daily refresh
python3 src/main.py --run backfill --symbols screener    # discovery + full backfill
python3 src/main.py --run daily --symbols db --force     # correction mode
python3 src/main.py --run calendar                       # earnings + economic event sweep

# tests
python -m pytest tests/                  # unit + golden (live auto-excluded)
python -m pytest tests/ -m live --override-ini="addopts="   # live smoke (real network)
python tests/capture_fixtures.py         # capture fixture payloads + expected rows
python tests/capture_fixtures.py --update   # recompute expected rows from stored fixtures
```

### Test layout

| Folder | What |
|---|---|
| `tests/unit/` | pure-function tests, no network |
| `tests/golden/` | frozen API payloads → mappers → expected DB rows |
| `tests/live/` | live smoke, invariants only (network) |
| `tests/fixtures/` | frozen payloads + expected rows |

Known: `test_intrinsic_value.py` xfails on a stale golden value (163.43 vs 54.56) — see AGENTS.md.

## web


# CI

GitHub Actions in `.github/workflows/` (Python 3.14). Workflows are `workflow_dispatch`-only — all scheduling lives in **Supabase pg_cron** (jobs `gh-dispatch-*` call the GitHub API using the `github_pat` Vault secret):

| Workflow | Schedule (pg_cron, UTC) | Command |
|---|---|---|
| `toolkit-stocks-hourly-prices.yml` | hourly :37 | `--run hourly --symbols db` |
| `toolkit-stocks-daily.yml` | daily 08:23 | `--run daily --symbols db` + verify.py |
| `toolkit-stocks-calendar.yml` | daily 06:47 | `--run calendar` (earnings/economic sweep) |
| `toolkit-stocks-manual-backfill.yml` | manual only | `--run backfill --symbols screener` |
| `tests.yml` (unit job) | push/PR (`toolkit-stocks/**`) | unit + golden tests |
| `tests.yml` (live-smoke job) | daily 08:53 + manual dispatch | live smoke tests |

Direct SQL maintenance jobs (pg_cron, no GitHub side):

| Job | Schedule (UTC) | Command |
|---|---|---|
| `cron-run-details-cleanup` | daily 03:00 | purge `cron.job_run_details` > 7 days |
| `purge-old-calendar-events` | daily 03:10 | purge `stock_economic_calendar` rows older than 6 months |
