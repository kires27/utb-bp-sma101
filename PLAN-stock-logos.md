# Stock Logos

Show real company logos in the web app instead of the letter avatar.

## Context / Research

- yfinance does NOT provide logos.
- Clearbit (`logo.clearbit.com`) is dead — shut down Dec 2025.
- Tested working providers (all return 200 + image/svg+xml, no key needed):
  - `https://logoapi.sh/ticker/AAPL` ← works by ticker, best fit
  - `https://logoapi.sh/apple.com`
  - `https://miromiro.app/logo/apple.com`
- DB: `stock.logo` column exists (text) but is empty for all 198 rows — leave it unused.
  Deriving the URL client-side from the symbol needs no DB writes and no pipeline changes.

Logo.dev	https://img.logo.dev/apple.com?token=pk_...
Brandfetch	https://cdn.brandfetch.io/apple.com?c=ID
Google favicons	https://www.google.com/s2/favicons?domain=apple.com&sz=128

## Decision

New component `StockLogo.vue` that:
1. Renders `<img>` from `https://logoapi.sh/ticker/{SYMBOL}` (lazy, alt = company name).
2. On `@error` falls back to the existing `TickerSymbol` letter avatar (keep component untouched).

Provider URL lives in one const inside the component — easy swap if service dies.

## Steps

1. Create `web/app/ui/StockLogo.vue`
   - Props mirror `TickerSymbol`: `symbol`, `name`, `size`, `round`, `gradient`.
   - `img` styled with `object-fit: contain` inside the avatar box.
2. Replace the 3 `TickerSymbol` usages:
   - `web/app/pages/fundamental-analysis/[symbol].vue` line ~200 (size 44)
   - `web/app/ui/Searchbar.vue` line ~82 (size 24)
   - `web/app/pages/available-stocks.vue` line ~94 (size 28)
3. Dark-mode check: some SVGs assume a light background — add light inner bg tile if needed.

## Test

- Stock header logo loads for AAPL / MSFT / TSLA.
- Search dropdown shows logos.
- Fallback: fake symbol (e.g. `ZZZZ`) → letter avatar appears, no broken img.
- Dark mode looks correct.

## Out of scope

- No DB changes, no `toolkit-stocks` changes.
- Storing logos locally (CDN is fine for this scale).
