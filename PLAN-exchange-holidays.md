# PLAN: Exchange Holidays → stock_economic_calendar

Goal: market holidays as events in `stock_economic_calendar` (`event_type = "market_holiday"`),
source = `exchange_calendars` package. Web work (badge, calendar page) NOT in this plan.

## Verified facts (2026-11-16, exchange_calendars 4.13.3 tested in throwaway venv)

- EC covers 32/33 target MICs: `XNAS`/`ARCX` alias to `XNYS`. Missing: XNSE.
- NSE + BSE both map to `XBOM` calendar. Verified 2024-26: NSE closures are a strict
  subset of BOM closures (PMC XNSE cross-check, zero NSE days missed). Extra 2 BOM days
  per year = Diwali muhurat special sessions (accepted false-closed risk, ~1h session).
- Closed-day truth = sessions list. Derive: weekday not in sessions AND not weekend.
  Weekend auto-detect: dayofweek with zero sessions over a 2+ year window
  (XSAU = Fri/Sat weekend, handled). Verified clean on all 27 working calendars.
- Names: complete for rule-based holidays (all EU/US/Nordic/JP/KR/AU/CA/BR/ZA/TW).
  Missing (date only, NaN name): XBOM (all ad-hoc), XHKG + XTAI (lunar), XIST + XSAU
  (Islamic Ramazan/Eid). Use sentinel name when NaN.
- Early closes: separate `cal.early_closes` list — SKIP (only full-day closures written).
- Eve-style regular holidays that are NOT full closures (XTAE "Passover Eve", XSWX
  "1-2 Jan", XTKS "Jan 2/3") land in `regular_holidays` but are NOT missing sessions —
  the closed-day filter (sessions-based) removes them automatically. Verified.
- Data horizon: most calendars have 2027 data now. XBOM/XSHG/XSES stop at year-end
  (package ships yearly, ~1yr ahead). Handle: shrink end-date until instantiation works.
- XTAE (Tel Aviv) BROKEN in 4.13.3: `ValueError: Special dates ... are not sessions`
  on 2026 instantiation. Skip + log warning. Note: seed row `Saudi` has wrong MIC
  `XTAE` (copy of TASE row) and there are duplicate HK rows (`Hong Kong` + `HKSE`,
  both XHKG) — dedupe/mapping must collapse by calendar, not MIC.

## Implementation

### 1. Dependency
- `exchange_calendars>=4.13` in `toolkit-stocks/requirements.txt` (pinned version).
- NOT a per-symbol fetch — one import in the holidays phase.

### 2. MIC → calendar map
`src/data/exchange_calendar_map.py`: exchange_code → EC calendar code.
- US 3 rows → XNYS. NSE + BSE → XBOM. Saudi → XSAU (fix its MIC bug separately or
  only in this map — seed MIC `XTAE` must NOT route to the broken TASE calendar).
- HK rows (both) → XHKG. Everything else: MIC as-is.
- 33 rows → 31 calendar targets, minus XTAE broken → 30 writable.

### 3. Phase: `holidays` (`src/pipeline/holidays.py`)
Standalone phase (like `exchange`, no RunContext), flag `--phases holidays`.
Per calendar code:
1. Try window (today → +9 months); on "holidays are only recorded to year X" error,
   shrink end to that year-end and log INFO.
2. Instantiate `get_calendar(code, start=..., end=...)`.
3. Weekend detection from sessions (2y lookback window).
4. Closed days = weekday, not session, not weekend, within window.
5. Names: `regular_holidays.holidays(s, e, return_name=True)`; adhoc dates where
   accessor exists. Name NaN → sentinel `"<SHORT_NAME> market holiday"`.
6. Row shape:
   - `event_type`: `"market_holiday"`
   - `symbol`: `""`
   - `stock_id`: None
   - `region`: exchange country code lowercase? (check transform conventions —
     existing rows use lowercase region codes or "global"); use country from seed
   - `event_name`: holiday name or sentinel
   - `event_datetime`: holiday date at exchange-local midnight → aware UTC
     (DST-aware via zoneinfo; midnight local can shift day under some offsets —
     Asia-Pacific fine, XSAU ok; verify no row lands on neighbor day)
   - `country_code`: from seed `country` (2-letter code)
   - `raw`: jsonb `{"source": "exchange_calendars", "calendar": code, "date": ...}`
7. Dedup in-memory by natural key (mirrors calendar.py).
8. Write: `RowFlusher(dbt.economic_calendar, flush_size=1000,
   conflict_keys=CONFLICT_KEYS)` — same as calendar.py. CHECK: existing
   `CONFLICT_KEYS = [event_type, symbol, event_datetime, event_name]` — with sentinel
   event_name always non-null this works unchanged.
9. Optional cleanup: delete `market_holiday` rows with `event_datetime < today`
   (normal 6-month purge also handles them; holidays are future-dated so optional).

### 4. Runner wiring
`runner.py`: standalone-phase branch like `exchange` (run when phases include
`holidays`, even if the rest of the list is calendar-only). Keep independent from
`calendar` phase so pg_cron can run it weekly/monthly separately.

### 5. Tests (`tests/`)
- Unit: transform (closed-day derivation, weekend detect incl. Fri/Sat, sentinel
  name, tz conversion) with synthetic/fixture calendar data.
- Live (marked, auto-excluded): instantiate all 30 writable calendars end-to-end,
  assert row counts > 0 for the working window.
- Unit for exchange_calendar_map: every seed exchange_code maps; Saudi does NOT map
  to XTAE.

### 6. Follow-ups (explicitly out of scope here)
- Fix exchange seed: Saudi MIC `XTAE` → XSAU, dedupe HK rows (needs care: stock.exchange
  values reference both codes).
- Web: badge + economic calendar page consumption of `market_holiday` rows.
- Yearly maintenance: bump exchange_calendars (new years ship ~1yr ahead), rerun
  phase. Add to CI as a monthly refresh workflow if wanted.

## Risks / accepted
- Late ad-hoc closures (mourning days): unknown until package updates. No source can
  do better. Yahoo `marketState` in quote phase stays the live truth.
- Unnamed lunar/Islamic closures: sentinel name acceptable for v1.
- XTAE unusable until upstream fix; row skipped, warning logged.
