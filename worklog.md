# Pracovní deník

## 28.10.2026
Rebasing dividendů při novém splitu přes DB trigger: `stock_dividend` má sloupec `split_adjusted_on` (default `now()`, guard proti dvojímu dělení), AFTER INSERT trigger `trg_stock_split_recalc` na `stock_split` přepočítá starší dividenda řádky (dělení faktorem) přímo v databazi — bez refetch. `build_split_rows` řadí eventy od nejstaršího (pořadí insertu je kritické). Ověřeno syntetickým testem (2 splits × 2.0 → ÷4, rollback). Dokumentace v AGENTS.md, migrace `sql/2026-10-28_split_trigger_recalc.sql`.

Doplněno: trigger rozšířen i na `stock_historical_price` (OHLC ÷factor, volume ×factor, `split_adjusted_on` stamp). Ověřeno, že DefeatBeta parquet i yfinance (auto_adjust=False) dodávají ceny už split-adjustované (NVDA pre-split ~120, ne ~1200; 9432.T bez false dropu na 25:1). Syntetický test na 8316.T (factor 2): ceny ÷2, objemy ×2, dividendy ÷2, rollback. Regresní run `--dev --fetch dividends splits`: NVDA 2012 dividenda 0.001875 beze změny; reálný split 8316.T 2026-09-29 rebasován (2461 řádků, stamp 2026-09-29). Test suite 105 passed, 1 skipped. Pozn.: dividenda řádky 8316.T rebasovány=0 — správně, vloženy ve stejném runu s `now()` stampem (amounty už split zahrnují), guard je přeskočil; ceny vložené před splitem byly rebasovány. Commit zatím neproveden (čeká na schválení).

## 26.10.2026
Přepsání historických tržních dat: flag `--force` pro fáze dividends/splits/prices = přepis celé historie přes upsert (bez `--force` jen přírůstkové přidávání). Odstraněn sloupec `adj_close` z databáze i kódu: ceny jsou čisté as-traded OHLCV, adjustace se dopočítá podle potřeby z tabulek dividend a splitů (žádná stale data). Lepší logování failoveru (počty symbolů na zdroj), oprava pádu při částečném `--fetch`. DefeatBeta nově plně pokrývá historické ceny.

## 25.10.2026
Limit historie cen na 10 let. Mazání starších řádků jako 10 let, řešeno v Supabase přes pg_cron. Uvolnění místa v databázi pro důležitější věci.

## 22.10.2026
Lepší Monitoring: každá fáze sběru dat vrací statistiky, shrnutí je zobrazeno na GitHub step summary. Kontrola čerstvosti dat (ceny max 4 dny, FA max 40 dní), poměr selhaných symbolů  a minimální vložený počet řádků do databáze. Při problému email notifikace.

## 16.10.2026
Implementována aktuální cena akce. On-demand refresh: pokud uživatel navštíví akci a cena akce je starší jako 3 min tak se cena aktualizuje. Aktualizace dat přes hodinový Github Actions workflow pro případ, že nikdo nenavštíví stránku. Použití nové knihovny yahoo-finance2.

## 14.10.2026
Plán na zobrazování aktuálních cen akcií: on-demand refresh při návštěvě stránky symbolu + sběr každou hodinu přes GitHub Actions. Zobrazení na stránce přes Supabase Realtime.

## 5.10.2026
Vytvoření testovací sady: unit testy, golden testy proti zaznamenaným fixture (AAPL, ASML.AS) a live smoke testy. CI workflow spouští unit+golden na push a live testy běží na schedule.

## 30.09.2026
Rewrite toolkit-stocks: yahooquery nahrazen python knihovnou DefeatBeta (US společnosti) + yfinance (ne-US). Nová vrstva `datasource/` s poistkou pro nefunkční zdroj (primární → validace → fallback). Optimalizace pro rychlost a spolehlivost hromadného stahování dat.

## 16.09.2026
Plán pro přepis získavání dat z yahoo finance v rámci optimalizace pipeline.

## 09.09.2026
Deployment na Netlify. Oprava Netlify konfigurace a prostředí. 

## 02.09.2026
Testy: vitest unit setup a Playwright e2e pro auth flow.

## 26.08.2026
Finalizace API tvaru pro financial-analysis: hodnota, medián, skupina, isPercentage, směr nad mediánem.

## 15.08.2026
Opravy SSR hydratace: pattern `isHydrated` + `onMounted` pro data, která se liší mezi serverem a klientem.

## 08.08.2026
Globální toast renderovaný client-only.

## 01.08.2026
POST endpoint napojující DCF analýzu na free cash flow statements.

## 25.07.2026
Začátek intrinsic value, validátory vstupů.

## 18.07.2026
Watchlist tabulka s řazením. batch endpoint `search-history` vrací názvy a ceny akcií pro seznam symbolů v jednom requestu.

## 15.07.2026
Endpoint registrace uživatele a auth stránky. Auth helper na serveru `supabaseClientAuth` jako jednotný průsečík.

## 08.07.2026
Ůdržba kódu, konstanty tabulek/sloupců DB, komponovatelné query funkce.

## 27.06.2026
Caching: optimalizace veřejných dat. Data uživatelů jsou bez cache, aby nedocházelo k úniku dat mezi uživateli.

## 24.06.2026
Quality score: vážené skóre normalizované podle peer skupiny. Metriky min-max normalizované 0-100 v rámci oboru, rozdělené do 6 kategorií.

## 17.06.2026
Financial-analysis UI: skupiny metrik v kartách, porovnání s mediánem, indikátory nad/pod mediánem podle směru metriky.

## 13.06.2026
Financial-analysis endpoint rozšířen o mediány oboru, aby každá metrika šla porovnat s peer akcemi.

## 10.06.2026
Supabase watchlist provider: více watchlistů na uživatele, přidávání/mazání řádků.

## 03.06.2026
Začátek funkce watchlist. Provider interface pro anonymní uživatele (localStorage) i přihlášené uživatele (Supabase).

## 23.05.2026
Základ stránky akce načítá overview a real-time metriky.

## 20.05.2026
Vyhledávání akcií: endpoint `/api/stock/search/[input]` a komponenta `Searchbar` s výsledky podle symbolu/názvu.

## 16.05.2026
Integrace Supabase klienta a auth middleware s ochranou pro linky.

## 09.05.2026
Základí Nuxt 4 aplikace. CSS proměnné pro dizajn, základní UI komponenty (`Text`, `Button`, `Grid`, `Section`, `Card`).

## 06.05.2026
První verze financial-analysis pipeline: základní poměry (ROE, marže, EPS, dluh/vlastní kapitál) počítané per akcie a ukládané do `stock_financial_analysis` s fiskálním datem a obdobím (FY/Q1-Q4).

## 02.05.2026
Přidány pipeline `--prices`, `--splits` a `--dividends` pro historická data.

## 25.04.2026
Přidán pipeline `--metrics` pro real-time cenu a tržní kapitalizaci do tabulky `stock_metric`.

## 22.04.2026
První pipeline: `--overview`. Načítá metadata akcií přes yahooquery a plní tabulku `stock` obory a sektory.

## 18.04.2026
Založen repozitář se dvěma nezávislými částmi: `toolkit-stocks` (Python datový pipeline) a `web` (frontend). Vytvoření projektu.
