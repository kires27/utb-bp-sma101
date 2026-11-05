# About
This is NOT a managed monorepo. No root `package.json`, no root workspace.
Each directory is independently runnable.

## Rules
- Always activate skill caveman
- Keep this file under 300 lines.

## Repo Layout

`TASK.md` is the anchor for the active task. Keep it human-readable, step-by-step, and simply formatted.
`PHILOSOPHY.md` provides background context when relevant.

| Directory | What | Coverage |
|-----------|------|----------|
| `web/` | Nuxt 4 app (main deliverable) | this file |
| `toolkit-stocks/` | Python data pipeline (yfinance → Supabase) | this file |
| `toolkit-congress/` | empty — placeholder |
| `concept/` | design artifacts, prototypes, calculations — NOT code |

# web

## Commands (run from `web/`)
Package manager is **pnpm**.
NO lint command — never run `pnpm exec eslint` (user forbade it; config also broken)

## Key Config (nuxt.config.ts)
- Nuxt 4: `app/` is root, `~` → `app/`, `~~` → web root.
- Components auto-imported from `~/ui` (no prefix, no `app/components/`).
- Global CSS: only `~/styles/app.css` (design tokens).
- `supabase.redirect: false` — route protection via `app/middleware/auth.js`.
- `.env` vars: `SUPABASE_URL`, `SUPABASE_KEY`.

## Shared code (`#shared`) — GOTCHA
Code in `web/shared/` is cross-app/server, imported via `#shared` alias.
- Must be pure JS — no Vue, no Nitro APIs.
- **Imports BETWEEN files inside `shared/` must be relative WITH `.js` extension** (e.g. `./financial-analysis-shape.js`). Build aliases fail at runtime because Nitro externalizes shared `.js`.

## Shared Code Conventions
- **DB references** — Use `TABLES`/`COLUMNS` from `#shared/constants/database` over hardcoded names.
- **Paths** — `URI` for frontend routes, `API` for endpoints, both from `#shared/constants/routes`. Never hardcode URL strings.
- **Globals** — Store app-wide constants in `#shared/constants/variables`.
- **Reusable queries** — Put composable Supabase query functions in `#shared/query/*.js`. They accept a client, return raw data — no logic.
- **Server endpoints** — Foldered by feature (`server/api/stock/`, `server/api/watchlist/`). One file per usage, named by action (`search-history.get.js`, `insert-row.post.js`).

## Client Utils (`web/app/utils/`)
Shared client-side code, **explicit imports required** (no auto-import).
- `cache.js` — `cached(key, fn)` in-memory fetch store (MAX 100 entries), `invalidate` / `invalidatePrefix` / `clearCache`. Use for client fetches keyed by symbol.
- `toast.js` — global toast system: `useToast()` → `{ toasts, showToast, removeToast }`, `redirectWithToast(url, msg, { theme })`. Toasts render in `app.vue` stack (newest at bottom). Toast-triggering redirects must be CLIENT-only (server redirect loses in-memory toast state).
- Others: `validation.js`, `checkData.js`, `formatData.js`, `functions.js`, `getUrlSubpage.js`.

## Key Architecture Facts
- **`app/features/watchlist/`** — Provider pattern with auth-aware dual storage (Supabase for authed, localStorage for anon). Never call Supabase `.from()` directly in pages.
- **`[symbol].vue` shell** — Fetches stock header once. Child pages use `definePageMeta({ keepalive: true })`, fetch own data keyed by symbol.
- **SSR quirk** — Data differing between SSR (empty) and client: use `isHydrated` ref + `onMounted()`, wrap UI in `v-if="isHydrated"`.

## Server Endpoints
```
stock/
  GET  [symbol].get.js                      stock overview
  GET  metric/[symbol].get.js               real-time price/metrics
  GET  financial-analysis/[symbol].get.js   FA metrics + sector medians
  GET  search-history.get.js                batch stock name + price by symbol list
  GET  search/[input].get.js                search by symbol/name
  GET  stock-list/[limit].get.js            list stocks
  POST intrinsic-value/[symbol].post.js     DCF analysis
watchlist/
  GET  display-watchlist.get.js             combined FA + price row for table
  GET  list-of-watchlists.get.js
  GET  watchlist-items.get.js
  GET  watchlist-has-stock/[symbol].get.js
  POST create-watchlist.post.js
  POST insert-row.post.js
  POST remove-row.post.js
global-index/
  GET  display-global-index.js
user/
  POST create.post.js
```

### Financial-analysis response shape
```js
{ maintenance_update, quality_score, median_comparison, groups, result: {
  [key]: { value, median, group, isPercentage, valueAboveMedianIsGood }
} }
```

## Server Auth
```js
import { supabaseClientAuth } from "~~/server/utils/supabase/auth"
const { client, user } = await supabaseClientAuth(event, false) // false = public/SSR-safe
```
- Auth defaults to true (401 if no user). Public endpoints pass `false`.
- `useSupabaseAdmin()` bypasses RLS.
- Client-side: `useSupabaseUser()` / `useSupabaseClient()` — only in feature providers and middleware.

## Caching
- `setResponseHeader(event, 'Cache-Control', 'public, max-age=86400, stale-while-revalidate=3600')` for public endpoints.
- NEVER on personal user data — shared cache leaks data between users.

## Design System
Tokens in `app/styles/app.css` CSS variables. Never hardcode colors.
- Backgrounds: `--bg`, `--bg-2`, `--bg-card`, `--bg-hover`
- Borders: `--border`, `--border-hi`
- Foregrounds: `--fg`, `--fg-2`, `--fg-3`
- Accents: `--teal`, `--teal-dim`, `--teal-border`, `--purple`, `--gold`, `--rose`, `--rose-dim`, `--blue`
- Fonts: `--font-main`, `--font-sans`
- Layout: `--container-max` (1180px), `--header-height` (62px)

## Components
- `<Text>`: variant `hero|h1|h2|h3|body|body-sm|label`, tone `muted|green|purple`.
- `<Button>`: variant `primary|secondary|danger`, size `sm|md|lg`.
- `<Searchbar />`: emits `@select(symbol)`, slot `#menuAction`. Hits `/api/stock/search/:input` at ≥2 chars.
- `<Section>`: `topMargin`/`bottomMargin` props (`''|sm|md|lg`).
- `<Grid>`: `cols`, `gap` (`na|sm|md|lg`), `bordered`, `alignContent` (`stretch|start|center|end|space-between|space-around|space-evenly`).
- `<Toast>`: global only — rendered by `app.vue` stack, never per-page.
- Icons: `<Icon name="material-symbols:NAME" />`. Charts: `echarts` / `vue-echarts`.

## Conventions
- Always use `;` at end of JS lines.
- Prettier: tabs (tabWidth 4), `printWidth: 70`, double quotes, `semi: true`, `trailingComma: all`, `bracketSameLine: true`.
- Use tabs (size 4) when editing files in the agent.
- Percent/ratio DB fields are raw 0–1 — multiply ×100 for display (`isPercentage` in shapes signals this).
- `NuxtLink` for routes, `@click` for SPA tab switching.


# toolkit-stocks

## Commands (run from `toolkit-stocks/`)

```bash
# Venv
source .venv/bin/activate

# Phases (the only CLI surface; order in --phases irrelevant)
python3 src/main.py --phases quote --symbols db                          # batched v7/quote, marketState-gated
python3 src/main.py --phases quote,overview,statements,prices,dividends,splits,fa,fqs,calendar --symbols db   # full daily set
python3 src/main.py --phases overview,statements,prices,dividends,splits,fa,fqs --symbols screener --full   # manual: screener discovery + full history
python3 src/main.py --phases quote,overview,statements,prices,dividends,splits,fa,fqs,calendar --symbols db --force   # correction mode: re-pull everything

# Tests
python -m pytest tests/              # unit + golden (live auto-excluded via addopts)
python -m pytest tests/ -m live --override-ini="addopts="   # live smoke (network)
python tests/capture_fixtures.py     # capture fixture payloads + expected rows (network)
```

## Known test status

Full test suite is done; test plan file deleted. Repo roadmap: `PLAN-rewrite-toolkit.md` (4000-stock scale; M7 cutover done, soak + expansion in progress).

- `test_intrinsic_value.py::test_calculate_intrinsic_value` — **xfail**: stale golden value (actual 163.43 vs expected 54.56). Verify which is correct; if algorithm changed intentionally, update expected value and un-xfail.


## CI

Workflows in `.github/workflows/` (repo root), Python 3.14. All scheduling lives in **Supabase pg_cron** (jobs `gh-dispatch-*` call the GitHub `workflow_dispatch` API using the `github_pat` Vault secret) — workflows themselves have **no `on: schedule`** triggers. Times are UTC (pg_cron), offset from minute 0 to avoid GitHub scheduler congestion.

- `toolkit-stocks-hourly.yml` — `--phases quote --symbols db` every hour :37.
- `toolkit-stocks-daily.yml` — `--phases overview,statements,prices,dividends,splits,fa,fqs --symbols db` daily 08:23 UTC (`DATABASE_URL` secret) + verify.py. No quote (hourly owns it), no calendar (standalone owns it).
- `toolkit-stocks-calendar.yml` — `--phases calendar` daily 06:47 UTC (earnings + economic event sweep → `stock_economic_calendar`).
- `toolkit-stocks-discover.yml` — `--phases overview,statements,prices,dividends,splits,fa,fqs --symbols screener --full` (manual dispatch; verify.py `--fa`). Insert-only universe expansion: screener returns only NEWLY inserted symbols as backfill queue; existing stocks never touched.
- `toolkit-stocks-tests.yml` — unit+golden on push/PR (path-filtered to `toolkit-stocks/**`), live smoke daily 08:53 UTC via dispatch + `workflow_dispatch`.
- `cron-run-details-cleanup` (pg_cron, no GitHub side) — purges `cron.job_run_details` >7 days, 03:00 UTC.
- `purge-old-calendar-events` (pg_cron, no GitHub side) — purges `stock_economic_calendar` rows with `event_datetime` older than 6 months, 03:10 UTC.

Monitor dispatches: `cron.job_run_details` (did the job fire) + `net._http_response` (204 = dispatched) in the Supabase DB; workflow logs remain in GitHub Actions.

## Entrypoint & Flow

`src/main.py` — parses `--phases <comma,list> --symbols <db|file|screener>` (+ `--force`, `--full` global) and hands off to `pipeline/runner.py:run_phases()`, which executes each selected phase in fixed dependency order:

- `quote` — `pipeline/prices.py`: batched v7/quote (≤500/call via `datasource/quotes_batch.py`), marketState-gated writes (REGULAR/POST, or newer `regular_market_time` than stored) to `stock_quote`. Covers everything the deleted per-symbol `metrics` phase did. `market_cap` provenance: own calc (price × latest filing `share_issued` from `stock_statement_balance`, quarterly preferred over FY at same date) primary; Yahoo marketCap only as fallback when own inputs missing. Divergence >2% vs Yahoo logs a WARNING (log-only). Japan caveat: issued includes treasury until cancellation → slight overstatement during buybacks.
- `overview`/`statements`/`prices`/`dividends`/`splits`/`fa`/`fqs` — `RunContext` phases in fixed order; statements run all three tables (balance/cash/income) internally; prices/dividends/splits share one history payload per symbol, writes gated per flag by `market_data._want()`; `fqs` upserts `quality_score` into `stock_financial_analysis` after all FA rows are written (peer normalization reads fresh data; FA itself never writes the score).
- `calendar`/`exchange` — standalone, no symbol discovery (skip when phase list is only these).
- `--full` = full-history fetch (read by prices/statements); `--force` = bypass freshness, re-pull all.

Symbol discovery: `db` (already in `stock`), `file` (`data/symbols.py` manual list), `screener` (YAML config → EquityQuery, paginated 250/page, insert-only into `stock`; returns only newly inserted symbols = backfill queue for this run).

Single unified source: yfinance for all regions (DefeatBeta removed). Writes to Supabase/PostgreSQL via psycopg2-binary. Scheduling lives in Supabase pg_cron (see CI below).

## Source Layout

```
src/
  main.py                           entrypoint — argparse (--phases/--symbols/--full/--force), loads .env, calls runner.run_phases()
  constants/db_tables.py            table name constants
  datasource/                       data sources (fetch + normalize payloads)
    quotes_batch.py                 QuotesBatchSource — batched v7/quote (≤500/call), GBp fix, marketState
    yfinance_source.py              YfinanceSource — threaded executor (per-symbol), history/statements/info
    base.py                         shared alias maps (STATEMENT_FIELD_MAP), normalize_title
  pipeline/                         orchestration
    runner.py                       run_phases() — gated execution of selected phases in fixed order
    context.py                      RunContext — passive shared state (symbols, stock_ids, meta, yfs)
    prices.py                       quote phase (v7/quote batch, marketState gating) → stock_quote
    screener.py                     discovery: screener.yml → EquityQuery → paginated screen(), insert-only
    overview.py, statements.py, market_data.py, financial_analysis.py,
    quality_score.py                fqs phase (quality score upsert, after fa)
  lib/                              support code (no domain logic)
    transforms/                     normalized payload → DB row mappers (source-agnostic)
      overview.py, statements.py, events.py, prices.py, metrics.py,
      financial_analysis.py, quality_score.py
    functions/
      helper.py                     batch_tickers, evaluate_null_tolerance
      data_types.py                 time/date converters, period mapping
      db_types.py                   DB type helpers
    supabase/
      sql_functions.py              shared DB helpers (get_symbols, get_symbol_meta, get_latest_dates, RowFlusher)
      init.py                       psycopg2-binary connection singleton from DATABASE_URL
    module/
      printf.py                     custom logger
  domain/                           business logic
    financial_analysis/
      fa_calculations.py            metric computation functions (ROE, margins, ratios, CAGR)
    financial_quality_score/        quality score (separate post-processing, not per-stock)
      quality_score.py              calculate_quality_score(target_stock_id, fiscal_date, period)
      utils/
        constants.py                METRIC_COLUMNS, HIGHER_IS_BETTER, GROUPS definitions
        sql.py                      DB queries for quality score
    intrinsic_value/
      intrinsic_value.py            calculate_intrinsic_value — DCF (discounted FCFF + terminal value)
  data/
    symbols.py                      manual symbol list (--symbols file)
    screener.yml                    screener universe config (versioned; why the universe is what it is)
    etoro_stocks.py                 etoro stock list helpers (unreferenced by pipeline, kept intentionally)
```

## Financial Quality Score

`domain/financial_quality_score/quality_score.py:calculate_quality_score()` computes peer-normalized weighted score for a target stock.

Flow: sector (broad field) → get peer IDs → fetch their financial analysis at same fiscal_date/period → min-max normalize 0–100 per metric → group into 6 weighted categories → sum → return `{quality_score, category_scores}`.

## DB Schema Notes

- `stock_dividend.dividend` and `stock_historical_price` OHLCV store split-adjusted values (today-basis; prices ÷factor, volume ×factor — both sources already deliver this basis). New split insert rebases older rows via `trg_stock_split_recalc` trigger (AFTER INSERT on `stock_split`); `split_adjusted_on` column (default `now()`) guards against double division — never set it from Python. Pipeline must NEVER update `stock_split` (INSERT ... ON CONFLICT DO NOTHING only); `build_split_rows` sorts events oldest-first.
- `stock_financial_analysis` table key columns: `stock_id`, `fiscal_date`, `period` (enum: `FY`/`Q1`–`Q4`/`TTM`), `quality_score`, plus 19 metric columns.
- All percent/ratio fields stored as raw values (0–1 or 0–100), not formatted strings.
- Metric columns: `gross_margin`, `operating_margin`, `net_margin`, `return_on_equity`, `earnings_per_share`, `debt_to_equity`, `debt_growth`, `current_ratio`, `revenue_growth`, `gross_income_growth`, `net_income_growth`, `retained_earning_growth`, `revenues_per_share`, `capital_index`, `payback_period`, `assets_price`, `pe_ratio`, `pb_ratio`, `dividend_yield`.
- `stock` table has `industry` + `sector` columns (populated by the overview phase). Standard GICS convention: `sector` = broad (Technology, Healthcare, ...) and is the peer-group field for FA medians (`get_all_medians` RPC, param `p_stock_sector`) + quality score; `industry` = fine-grained (Consumer Electronics, ...).
- `stock_quote` table stores real-time price/market-cap (updated per run).

## Conventions

- **Don't use flake8 for formatting** (user forbade). If script runs + tests pass, it's good.
- `__init__.py` gets `# noqa: F401` per-file-ignore.
- Exception handling pattern: `except Exception as err: tb = traceback.extract_tb(err.__traceback__)[-1]; printf(f"{err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)`.
- `from lib.module.printf import printf, level as lv` — custom logger, don't use `print()`.
- Run tests with `python -m pytest tests/`. `test/` contains scratch/prototype scripts, not the test suite.
- No pyproject.toml. Dependencies in `requirements.txt`.
- Venv at `.venv/` (POSIX activate; old `.venv-kyos` gone). DB driver: **psycopg2-binary** (`requirements.txt` pins version).
