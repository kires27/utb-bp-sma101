# MEMORY

# Preferences
- Terse, no-filler. No emojis. No em dash.
- Work-log: Czech, newest-first, one feature per day.

# Decisions
- adj_close REMOVED (2026-10-26): column dropped from `stock_historical_price` + all code. Prices = pure as-traded OHLCV; adjustment derived on read from `stock_dividend` + `stock_split` when needed (formula: close × Π splits/divs after date). Consequence: DefeatBeta fine as primary for historical prices. Price chart = split-adjusted OHLC derived on read; adj series only for total return. Dividends stay yfinance-primary (full precision; DefeatBeta rounds 2dp).
- `--force` market data (2026-10-26, `PLAN-force-rewrite-market-data.md`): full-history rewrite via upsert (`conflict_keys` → DO UPDATE, passed only when forced); without force = incremental append. Force couples all three phases (dividends/splits/prices). PLAN-split-trigger-recalc.md still needed: dividend re-basing on new split + derive-on-read prices.
- Realtime prices IMPLEMENTED (2026-10-25, `PLAN-realtime-prices.md`): staleness 3 min on `regular_market_time`, yahoo-finance2 v4 + fallback, 60s client heartbeat + Realtime. Open: 2 manual RLS on kire; `SUPABASE_SECRET_KEY` in Netlify.
- Price history capped to 10y (2026-10-25): fetch-side cutoff + pg_cron weekly purge. Pre-10y div/split events kept (feed derivation).
- Monitoring DONE (2026-10-24): per-phase stats, `verify.py` freshness/fail checks → email.
- DefeatBeta (US) + yfinance (non-US); yahooquery deleted. Failover: `FailoverSource(primary, fallback, validate)`, prices all-or-nothing per full history. DefeatBeta license ODC-BY: thesis OK, not commercial.
- Intrinsic value: Excel sheet canonical: NFCF = mean of 3 newest FCFs; 5y AGR; terminal = peer/industry P/FCF; MoS ×0.75.
- Deps: yfinance 1.7.0, curl_cffi 0.16.3, pandas 3.1, numpy 2.5.4; don't bump duckdb (defeatbeta-api pins it).

# Gotchas & Lessons
- Kire (`kwpzvlymmaczaixtjdbu`) = live SMA DB (web target); halite = older copy, do not write. Web writes need `SUPABASE_SECRET_KEY` → `useSupabaseAdmin`.
- Yahoo's displayed OHLC is split-adjusted (volume too); `Adj Close` = split+dividend; as-traded needs `auto_adjust=False`.
- Raw close immutable (write-once); adj values shift on every new event → stored adj columns always stale, hence derive-on-read.
- DefeatBeta: splits "5:1" strings; `stock_prices.report_date` VARCHAR — compare ISO strings in DuckDB, never `DATE '...'`.
- Virtual fields (`price_age_seconds`, `stale`) computed post-query in `metric/[symbol].get.js`, stripped from `?select=`.
- PostgREST: after migration, `NOTIFY pgrst, 'reload schema'`.
- `test_intrinsic_value.py` xfail: stale golden (163.43 vs 54.56); re-check expected.
- CI workflows at repo root `.github/workflows/`.

# Open threads
- toolkit-stocks: session changes UNCOMMITTED (10y cap, --force, adj_close removal, yfinance 1.7.0, yahooquery removal, deps).
- Quality score currency bug (`PLAN-quality-score-currency.md`): drop EPS/revenues-per-share from GROUPS, redistribute weights, re-run `--fa`.
- Full-universe run (`PLAN-full-universe-run.md`): ~4,621 symbols, record timing.
- Regenerate `web/app/types/database.types.ts` (still declares adj_close).
