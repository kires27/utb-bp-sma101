# README

[![daily pipeline](https://github.com/kires27/utb-fai/actions/workflows/toolkit-stocks-daily.yml/badge.svg)](https://github.com/kires27/utb-fai/actions/workflows/toolkit-stocks-daily.yml)
[![daily FA](https://github.com/kires27/utb-fai/actions/workflows/toolkit-stocks-daily-fa.yml/badge.svg)](https://github.com/kires27/utb-fai/actions/workflows/toolkit-stocks-daily-fa.yml)

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

Fetches financial data from two sources, transforms it, and uploads it to Supabase/PostgreSQL. Consumed by the web app.

### How it works (data flow)

```
symbols (src/data/symbols.py)
    │
    ▼
1. ROUTING ──── which source serves which symbol?
    US symbols     → DefeatBeta (bulk parquet dataset via DuckDB)
    non-US symbols → yfinance (per-symbol HTTP, threaded)
    │
    ▼
2. FETCH ────── each source returns normalized "payloads"
    profiles, officers, statements (long format),
    price history, dividends, splits, shares, live quotes
    │
    ▼
3. TRANSFORM ─── payloads → DB rows (lib/transforms/)
    e.g. recompute dividend/split-adjusted close over
    full history, group statement line items per report date,
    map fields to the DB schema
    │
    ▼
4. ENRICH ────── business logic (domain/)
    financial-analysis metrics (ROE, margins, growth…),
    peer-normalized quality score, DCF intrinsic value
    │
    ▼
5. UPLOAD ────── psycopg2 → PostgreSQL/Supabase
    upsert rows per table (stock, stock_prices, statements,
    stock_financial_analysis, stock_metric …)
```

Entry: `src/main.py --<phase>` → `pipeline/orchestrator.py:run()` runs requested phases in fixed order: **overview → statements (balance/cash/income) → market data (prices/splits/dividends, fetched once shared) → metrics → financial analysis**.

### Commands

```sh
cd toolkit-stocks
source .venv/bin/activate
pip install -r requirements.txt          # .env needs DATABASE_URL

# run pipeline
python3 src/main.py --overview --balance --cash --income --dividends --prices --splits --metrics --fa   # everything
python3 src/main.py --fa                 # financial analysis only

# tests
python -m pytest tests/                  # unit + golden (live auto-excluded)
python -m pytest tests/ -m live --override-ini="addopts="   # live smoke (real network)
python tests/capture_fixtures.py         # capture fixture payloads + expected rows
python tests/capture_fixtures.py --update   # recompute expected rows from stored fixtures

# lint
flake8 src/
```

### Test layout

| Folder | What |
|---|---|
| `tests/unit/` | pure-function tests, no network |
| `tests/golden/` | frozen API payloads → mappers → expected DB rows |
| `tests/live/` | live smoke, invariants only (network) |
| `tests/contract/` | source-failover contract |
| `tests/fixtures/` | frozen payloads + expected rows |

Known: `test_intrinsic_value.py` xfails on a stale golden value (163.43 vs 54.56) — see AGENTS.md.

## web


# CI

GitHub Actions in `.github/workflows/` (Python 3.14):

| Workflow | Trigger | What |
|---|---|---|
| `toolkit-stocks-daily.yml` | daily 08:00 UTC | pipeline `--prices --metrics` (needs `DATABASE_URL` secret) |
| `toolkit-stocks-daily-fa.yml` | daily 09:00 UTC | pipeline `--fa` |
| `tests.yml` | push/PR (`toolkit-stocks/**`) | unit + golden tests |
| `tests.yml` (live-smoke job) | daily 08:00 UTC + manual dispatch | live smoke tests |
