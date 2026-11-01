# PLAN — rewrite toolkit

Target: scale pipeline from ~200 to ~4000 stocks. Battle-tested before expansion.
Docs: https://ranaroussi.github.io/yfinance/reference/index.html (yfinance 1.7.0)

## Research findings (verified live, Oct 2026)

- Batch quote endpoint `v7/finance/quote?symbols=...` works via yfinance's own
  request machinery (`YfData.get_raw_json`). Tested: 83 intl symbols in 1 call,
  500 LSE symbols in 1 call. Chunk at ≤500/call.
- Returned per symbol: price, change/pct, marketCap (direct — no close×shares),
  dividendYield, volume, currency (GBp fix), marketState
  (REGULAR/PRE/POST/POSTPOST/CLOSED), regularMarketTime (epoch).
  Covers: hourly price fetch, market-open detection, change detection.
- After-hours: regularMarketPrice does NOT move. Hourly fetch of closed-market
  stocks is redundant → skip unless regularMarketTime newer than stored.
- `spark` endpoint (`v7/finance/spark`) — batched, but close-only series,
  no OHLC/volume/events.
- Screener API (`yfinance.EquityQuery('eq', ['exchange', 'LSE'])`, 250/page)
  returns the whole exchange universe (3406 LSE). Possible auto-discovery of
  new symbols instead of hand-maintained list.
- **Batched fetch is the dominant rate-limit win.** Yahoo's limiter (429 +
  yfinance exponential backoff) counts **requests, not payload size**. Live
  test: 30 symbols individually = 30 requests / 2.06s; batched = 1 request /
  0.08s. 500 symbols = 1 request / 0.43s / 1.09 MB. Practically free.
- **yfinance built-in cache covers only timezones + cookies** (verified in
  source, `cache.py`). Data caching is ours to build — via the DB (below).
- `yfinance.Tickers` — wrapper; `.history()/.download()/.news()` are per-symbol
  loops internally, NOT true batch. Probably less useful than raw v7 batch.
- quoteSummary (assetProfile etc., statements, dividend/split events) is
  single-symbol only → stays per-symbol in daily phases.
- **No US/intl partition.** With DefeatBeta removed, US stocks use yfinance like
  every other stock — fetched together with all regions via the bulk v7/quote
  call. The `us_symbols`/`intl_symbols` split, routing, and exchange heuristics
  (partition_symbols, US_EXCHANGE_FALLBACK) go away. One unified symbol list.

## Design principles

- **Fetch raw facts only, compute everything derivable.** Never pay an API call
  (or storage) for a value we can calculate:
  - P/E, P/B, assets_price → from statements + price (`fa_calculations` already does)
  - marketCap → price × shares outstanding (or one batch field, no extra call)
  - change / change % → price vs previous close in DB
  - dividend yield → TTM dividends ÷ price (already computed from events)
- **DB is the only cache.** Mode decision per symbol: check DB for latest entry →
  no/missing entry → backfill; entry exists → incremental from last stored date.
- **Two fetch modes:**
  | Situation | Fetch | Cost @ 4000 stocks |
  |---|---|---|
  | New symbol | full backfill per-symbol (`history(period="max")`, statements, profile) | rare, spread over time |
  | Existing symbol, daily | `history(start=<last_db_date>)` incremental + statements refresh | ~4000 cheap calls once/day |
  | Existing symbol, hourly | `v7/quote` batched (≤500/call), marketState-gated writes | ~8 calls/hour |
- **Backfill = initial full load** (new symbol, or pool expansion 200→4000).
  Per-symbol: `history(period="max")` + statements + profile. Batching does not
  help here (chart API is single-symbol). ~3800 backfills × 3-4 calls ≈ 12-15k
  requests, one-time, spread over runs. Steady state afterwards is only the
  cheap incremental + batched hourly flows.
- **Insert strategy — middle ground between row-by-row and all-at-once.**
  Chunked bulk inserts: accumulate fetched rows in memory, flush to DB in
  chunks of N (e.g. 500-1000 rows) in one transaction per chunk.
  Detailed per-table method → "Insert strategy — hybrid per table" below.
- **Skip closed markets:** hourly run only writes when `marketState` is
  REGULAR/POST, or when `regularMarketTime` is newer than stored (missed close).

- **Pipeline shape — modular at two levels, composition table on top.**
  - **Sources (thin, dumb):** one file per fetch primitive, no logic — call
    Yahoo, return normalized dicts. `quotes_batch` (v7/quote, hourly),
    `history` (chart API, daily+backfill), `statements`, `profile`.
  - **Phases (own behavior):** each phase decides symbols × fetch mode ×
    transform to rows × chunked DB flush. `prices`, `statements`, `overview`, `fa`.
  - **Runner = composition table**, no branches inside phases:
    - `hourly`: prices (batch, marketState-gated)
    - `daily`: prices (incremental), statements (incremental), overview, fa
    - `backfill`: prices (full), statements (full), overview, fa
  - Mostly a **subtraction rewrite**: current `pipeline/` + `datasource/` shape
    kept; DefeatBeta, `FailoverSource`, US/intl partition deleted; batched-quote
    source added. `lib/transforms/` mappers fold into their phase (each used by
    one phase only); `domain/` (FA calcs, quality score) unchanged.
  - **Phases stream**: fetch chunk → transform → flush DB in chunks. Memory
    bounded; a phase failure only loses that phase's work (natural crash
    recovery, no disk cache needed).
  - **Own threaded executor** for per-symbol fetches (daily incremental +
    backfill), replacing `yf.download()`/`Tickers` (per-symbol loops anyway,
    but all-or-nothing timing and uncontrolled concurrency). Controlled
    concurrency, per-symbol error capture, results stream into phase flushes
    — not one giant DataFrame at the end.
- **Insert strategy — hybrid per table.**
  - `execute_values` + `ON CONFLICT DO UPDATE` for upsertable tables:
    `stock_metric`, `stock_financial_analysis`, `stock_overview`,
    `stock_statement_*` (statements can be restated by companies).
  - `COPY` (→ staging table → `INSERT ... ON CONFLICT DO NOTHING`) for
    append-only tables: `stock_historical_price`, `stock_dividend`.
  - `stock_split` stays insert-only — the split-rebasing trigger must never
    see a re-inserted split (double-rebase risk). Force-update applies to
    prices/dividends/statements only, never splits.
  - `--force` flag: global; flips conflict handler to `DO UPDATE` and re-pulls,
    for corrections (restated financials, adjusted history). Prices are stored
    split-adjusted on a consistent basis, so overwriting is safe.
  - **Chunk size is not hardset** — each phase defines its own flush size as a
    local constant (comfortable spot next to the phase's logic), since hourly
    (4000 rows total) and backfill (millions) want different values.
- **CLI surface — three orthogonal flags, workflows set them:**
  - `--run hourly|daily|backfill` → picks the composition row (which phases, which fetch mode)
  - `--symbols db|file|screener` → discovery mode (hourly/daily jobs use `db`)
  - `--force` → global correction mode
  - GitHub Actions workflows map 1:1: `hourly-prices.yml` → `--run hourly --symbols db`,
    daily workflow → `--run daily --symbols db`, manual/expansion run → `--run backfill --symbols screener`
- **Discovery — three modes (`--symbols` flag):**
  - `db` — only stocks already in `stock` table (used by hourly/daily price
    jobs; never discovers new symbols).
  - `file` — current behavior: `symbols.py`, insert-if-missing.
  - `screener` — discover via screener API, config-driven.
- **Screener config = YAML mapping 1:1 onto the fixed screener vocabulary.**
  Verified: operators are a closed set (`eq, is-in, btwn, gt, lt, gte, lte,
  and, or`) and fields validated against `EQUITY_SCREENER_EQ_MAP`
  (region/exchange/sector/industry/peer_group + numeric fields). No parsing
  engine needed; unknown fields/operators fail loudly at startup. Loader builds
  EquityQueries, ands them, paginates screen() (250/page). New listings minus
  symbols already in `stock` = backfill queue. Config versioned in repo
  documents why the universe is what it is. **Insert-only**: discovery just
  inserts into `stock`; the next scheduled run picks up backfill for new
  symbols. Discovery stays cheap, ingestion stays incremental.

## Implementation plan (ordered)

Build order chosen so each milestone is independently verifiable; old code
stays runnable until M7 (deletion last). Use `--dev` (manual_symbols) as the
test harness for every milestone.

**M0 — Audit.** Inventory `src/` tree: every module, every table it touches,
every workflow. Output: short mapping (module → table → workflow) appended to
this file. Nothing rewritten yet.

**M1 — Batched quote source.** New source module `quotes_batch`: v7/quote via
yfinance machinery, ≤500 symbols/call, normalize (GBp ÷100, currency,
marketState, regularMarketTime epoch). No DB writes. Verify: fetch all current
symbols in dev, print summary, eyeball vs. current `info()` output.

**M2 — DB read helpers.** `get_symbols()` without US/intl partition; last
stored `regular_market_time` / last price date per symbol (one query each).
Verify: correct on a known subset.

**M3 — Hourly vertical slice.** `prices` phase (batch mode) + marketState
gating (write only REGULAR/POST, or newer regularMarketTime than stored) +
runner composition table + CLI (`--run`, `--symbols`, `--force`). Verify:
dev run writes same rows as current hourly flow; closed-market stocks skipped;
`stock_metric` row diffs empty on second run.

**M4 — Remove DefeatBeta.** Delete defeatbeta source, `FailoverSource`,
`partition_symbols`, exchange heuristics. US stocks route through yfinance
(`history()` daily incremental like intl). Verify: daily dev run produces
price rows for US symbols matching DefeatBeta values (allow small adjustment
differences; document any).

**M5 — Threaded executor + daily phase.** Own executor (controlled
concurrency, per-symbol errors) driving `history(start=<last_db_date>)` +
statements refresh, streaming into chunked flushes (per-phase flush size).
Verify: dev subset — incremental returns ~1 row/symbol; restated statement
rows update via `DO UPDATE`.

**M6 — Backfill + screener discovery.** Backfill phase (full history +
statements + profile for symbols missing data). Screener mode: YAML config →
EquityQuery loader (validate against EQUITY_SCREENER_EQ_MAP, fail loudly),
paginated 250/page, insert-only into `stock`. Verify: pick 5 new screener
symbols → inserted into `stock`, next scheduled run backfills them.

**M7 — Cutover + cleanup.** Update GitHub Actions workflows to new CLI
(hourly → `--run hourly --symbols db`, daily → `--run daily --symbols db`,
manual → `--run backfill --symbols screener`). Delete dead code. Soak 24-48h
at current scale (~200 stocks). Then expansion to 4000 in screener batches
(e.g. 500/run), soak after each batch before the next.

**Guardrails for any agent:** never insert/update `stock_split` twice (rebase
trigger); conflict method per table as in Insert strategy; fetch raw facts
only — no valuation/derivative endpoints; phases stream, never buffer whole
universe in memory; a failed phase must not block the next phase's start, but
must exit nonzero.

## M0 Audit — module → table → workflow mapping (2026-11-01)

### Entry / orchestration
| Module | Role | Tables touched | Workflow |
|---|---|---|---|
| `src/main.py` | argparse: `--dev`/`--prod`, `--force`, `--fetch <phases>` (overview/balance/cash/income/dividends/prices/splits/metrics/fa) | none | all |
| `src/pipeline/orchestrator.py` | fixed phase order; fetches DefeatBeta bulk once when any of prices/splits/dividends/metrics/fa requested (line 36-38) | all (via phases) | all |
| `src/pipeline/context.py` | `RunContext` (symbols, stock_ids, symbol_meta, ds=FailoverSource(DefeatBeta, yf), yfs, market_data_cache); `partition_symbols` via `us_members` probe, exchange-heuristic fallback | none | all |
| `src/data/symbols.py` | `manual_symbols` (~200) for `--dev` | none | dev only |
| `src/data/etoro_stocks.py` | 27k-line etoro list, currently unreferenced by pipeline | none | none |

### Phases
| Phase | Module | Fetch path | Tables | Conflict strategy |
|---|---|---|---|---|
| overview | `pipeline/overview.py` | US: DefeatBeta profiles+officers, yf identity fallback for missing names; intl: yf info() per symbol | `stock` | upsert by symbol (update_condition) |
| balance/cash/income | `pipeline/statements.py` | US: DefeatBeta statements bulk; intl: yf statements_payload per symbol. Freshness: 380-day window + `updated_at` stamp check | `stock_balance_sheet`, `stock_cash_flow`, `stock_income_statement` | plain insert (no conflict keys) |
| prices/splits/dividends | `pipeline/market_data.py` | US: DefeatBeta bulk (prices/shares/divs/splits); intl: yf history_payload per symbol, incremental via `get_latest_dates` + `map_latest_yahoo_historical` period mapping | `stock_historical_price`, `stock_split`, `stock_dividend` | prices/divs: conflict_keys ["stock_id","date"] only when `--force`; **splits also get conflict_keys on force (see audit finding 1)** |
| metrics | `pipeline/metrics.py` | US: `build_us_quote` from cached DefeatBeta bulk (EOD close, shares, TTM divs); intl: yf quote() per symbol | `stock_metric` | upsert by stock_id |
| fa | `pipeline/financial_analysis.py` | same quote paths as metrics; statements read back from DB | `stock_financial_analysis` | upsert by (stock_id, fiscal_date, period); then quality_score second upsert |

### Data sources
| Module | Role |
|---|---|
| `datasource/defeatbeta.py` | HF parquet via DuckDB, 500/chunk: us_members, profiles, officers, statements (long format), prices, dividends, splits ("a:b" strings), shares_outstanding |
| `datasource/yfinance_source.py` | per-symbol threaded (8 workers, 4-retry backoff): info, quote, history (auto_adjust=False), statements (annual/quarterly), history_payload |
| `datasource/failover.py` | per-symbol failover; prices/divs/splits all-or-nothing per full history; dividends invert roles (yfinance primary for precision) |
| `datasource/base.py` | STATEMENT_FIELD_MAP aliases, normalize_title, route_symbols, US_EXCHANGE_FALLBACK |

### Transforms (source-agnostic mappers)
`lib/transforms/`: prices (`build_price_rows`, incremental by latest_date), events (dividend/split rows, splits sorted oldest-first), metrics (`build_metric_row`), overview (`build_overview_row`, sector/industry intentionally swapped), statements (`build_statement_rows`, `group_statement_records`), financial_analysis (`build_financial_analysis` via `fa_calculations`, 19 metrics), quality_score.

### DB layer
`lib/supabase/sql_functions.py`: `insert_data_statement` is **row-by-row** (one cursor.execute per row, one commit at the end). `get_latest_dates`/`get_latest_fiscal_dates` batched. Connection singleton `lib/supabase/init.py`.

### Workflows (all `workflow_dispatch`; scheduling via Supabase pg_cron)
| Workflow | Command |
|---|---|
| `toolkit-stocks-hourly-prices.yml` | `--prod --fetch metrics` |
| `toolkit-stocks-daily.yml` | `--prod --fetch overview balance cash income prices metrics splits` + verify.py |
| `toolkit-stocks-daily-fa.yml` | `--prod --fetch fa` + verify.py |
| `tests.yml` | pytest unit+golden on PR; live smoke daily |

### Tests
`tests/unit/` (11 files: transforms, fa_calcs, quality score, stats, gating, data types, intrinsic value xfail), `tests/contract/test_failover_contract.py`, `tests/golden/`, `tests/live/`.

### Audit findings (carry into rewrite)
1. **Split force bug**: `market_data.py` passes `conflict_keys` to `stock_split` when `--force`. An UPDATE would not re-fire the AFTER INSERT rebase trigger, so no double-rebase, but it violates the "never update stock_split from Python" rule. Rewrite: splits never receive conflict keys, ever.
2. **Overview has no freshness gate** — refetches profiles+officers for the entire US universe every run it's enabled. Fine at 200, wasteful at 4000. Daily flow should gate by meta presence / staleness like statements do.
3. **Hourly metrics run pays the full DefeatBeta bulk fetch** (prices+shares+dividends) because `build_us_quote` needs the market_data cache. Under the rewrite the hourly flow becomes the batched v7/quote call only.
4. **`insert_data_statement` row-by-row** is the per-row commit bottleneck; the rewrite's chunked `execute_values` replaces it. Note: it also loses `regular_market_time` on US metric rows (key omitted → old value preserved) — intentional.
5. **etoro_stocks.py is dead weight** for the pipeline (27k lines, unused). Candidate for deletion in M7 or leaving untouched (out of scope unless user says otherwise).
6. **yf statements `touch_statement_rows` after fetch** also stamps rows whose fetch returned nothing — acceptable (fetch happened), keep semantics.

