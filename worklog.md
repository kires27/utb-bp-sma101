# Pracovní deník

## 16.11.2026
Vylepšen vzhled logování.
Opraven "type bug" v databázové funkce `on_new_split`.

## 13.11.2026
Zahraniční akcie se teď správně přepočítávají do jejich obchodní měny — kurzy se stahují automaticky, takže poměry jako cena/zisk fungují i pro firmy vykazující v jiné měně.
Nový indikátor, jestli burza dané akcie má zrovna otevřeno nebo zavřeno (včetně polední pauzy u asijských burz), s časem poslední aktualizace ceny.
Hodnocení kvality firem už neporovnává metriky mezi různými měnami. Drobné opravy zaokrouhlení čísel a rozšířená stránka vnitřní hodnoty akcie.

## 8.11.2026
Tržní kapitalizace se nově počítá vlastním výpočtem (cena × počet akcií z výkazů).
Oprava ceny londýnských akcií: některé se uvádějí v pencích místo liber, teď se to správně přepočítává.
Nedávné kvartální výsledky firem se průběžně doplňují — každý den se obnoví část akcií, takže pokud firma své výsledky zpětně opraví, změna se projeví nejpozději do týdne.
Sběr dat je rychlejší a šetří požadavky díky menšímu počtu dotazů. Vylepšeno shrnutí běhu — ukazuje i počet dotazů do databáze a Yahoo. Zjednodušené ovládání nástroje a přepsaná dokumentace. Úklid v databázi (přejmenování tabulek výkazů, nové sloupce).

## 4.11.2026
Výpočty finančních metrik využívají už uložené ceny z databáze místo opakovaného stahování, běh je výrazně rychlejší a šetří požadavky.
Dividendový výnos se počítá z vlastních dat a nestahuje se z Yahoo (spolehlivější).
Hodnocení kvality firem (FQS) je odděleno do samostatného kroku a běží až po výpočtu metrik. 

## 2.11.2026
Nový DB trigger při splitu = přepočítá starší dividendy a historické ceny.

## 28.10.2026
Nová funkce: přepsání historických tržních dat přes flag `--force` pro fáze dividends/splits/prices = přepis celé historie. Odstraněn sloupec `adj_close` z databáze.

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
Přidán pipeline `--metrics` pro real-time cenu a tržní kapitalizaci do tabulky `stock_quote`.

## 22.04.2026
První pipeline: `--overview`. Načítá metadata akcií přes yahooquery a plní tabulku `stock` obory a sektory.

## 18.04.2026
Založen repozitář se dvěma nezávislými částmi: `toolkit-stocks` (Python datový pipeline) a `web` (frontend). Vytvoření projektu.
