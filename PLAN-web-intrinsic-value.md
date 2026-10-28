# Plan: Web mirror of intrinsic value (canonical Excel model)

Python `toolkit-stocks/src/domain/intrinsic_value/intrinsic_value.py` is already rewritten (goldens 54.56 / 69.55 pass). This plan brings `web` in line with the same canonical Excel model.

## Model recap (canonical, matches Excel sheet)

- NFCF = mean of 3 newest FCFs
- AGR = newest vs FCF 5y back; fallback to full available span if < 6 years
- 5 projected years, growth discount (×0.85), discounted by FDR^year
- Terminal = FCF5 × peer/industry P/FCF, discounted
- NO cash added; margin of safety applied to per-share result at the end

## JS changes — `web/server/calculations/intrinsicValue.js`

New signature (web KEEPS `projection`; python dropped it):

```js
calculateIntrinsicValue(stockPrice, shareIssued, cashFlow, priceToFcf,
	growthRateDiscount, futureDiscountRate, safetyMargin, projection)
```

Body:

1. `annualGrowthRate(fcfs.slice(0, 6))` — newest vs oldest of up to 6 FCFs, `periods = length - 1` (fallback = available span, same as python)
2. `normalizedFreeCashFlow` → mean of first 3 only: `(v[0]+v[1]+v[2])/3`
3. `futureFreeCashFlows(nfcf, projection, dagr)` — projection from param (default 5)
4. Delete `priceToFreeCashFlow` helper; `ter = ffcfs[projection - 1] * priceToFcf`
5. `iv = dffcfSum + dter` — remove `+ cashAndEquivalents`
6. Return object: drop `market_cap` key; `projection_horizon` = projection param
7. Keep `iv_upside`, `intrinsic_value_per_share` semantics unchanged

## Ripple effects

| File | Change |
|---|---|
| `web/server/api/stock/intrinsic-value/[symbol].post.js` | new arg order; fetch peer/industry P/FCF instead of computing from marketCap; drop cash-equivalents lookup; accept `projection` from request |
| `#shared/validators/intrinsic-value` | validate `priceToFcf` (positive number), `projection` (int, 3–10); remove marketCap/cash checks |
| API request/response shape | response loses `market_cap`; request gains `priceToFcf` (or resolved server-side) — update any UI reading `market_cap` |
| Peer P/FCF source | see decision below |

## Decision: where `priceToFcf` comes from

- **A — quick:** endpoint computes on the fly (median of industry peers' `market_cap / free_cash_flow`, both in DB via `stock_metric` + statements). No pipeline change; heavier query per request.
- **B — pipeline (recommended):** add `price_to_fcf` metric column to FA pipeline (already computes industry medians — natural fit); endpoint reads the median. Needs one `--fa` run to populate.

## Tests

- Mirror python goldens in JS if a JS test setup exists (currently web has none): AAPL-2025 = 54.56, AAPL-2024 = 69.55, same hardcoded peer P/FCF values as python test (`7.8436273373235155`, `7.848663902326654`).

## Out of scope / later

- FA pipeline `price_to_fcf` metric column (if B chosen) — separate step, needs DB schema change + pipeline run
- Any backfill/migration of stored intrinsic values
