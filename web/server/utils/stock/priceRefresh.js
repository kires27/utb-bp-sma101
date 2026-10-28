/**
 * Swappable Yahoo price fetcher.
 * Primary: yahoo-finance2 `quote()` (handles crumb/cookie handshake).
 * Fallback: raw /v8/finance/chart (no crumb needed, price-only).
 * Never throws — returns null on failure so caller keeps the last good row.
 */

const CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart";
const BROWSER_UA =
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";

let YahooFinance = null;
async function getQuoteFn() {
	if (!YahooFinance) {
		const mod = await import("yahoo-finance2");
		// v4: class — instantiate (suppress one-time survey notice)
		YahooFinance = new mod.default({ suppressNotices: ["yahooSurvey"] });
	}
	return YahooFinance;
}

/**
 * @param {string} symbol
 * @returns {Promise<{ price: number, previousClose: number|null, currency: string|null, regularMarketTime: string }|null>}
 */
export async function fetchQuote(symbol) {
	let quote = await fetchViaLib(symbol);
	if (quote) return quote;

	quote = await fetchViaChart(symbol);
	return quote;
}

async function fetchViaLib(symbol) {
	try {
		const yf = await getQuoteFn();
		const quote = await yf.quote(symbol);
		if (!quote?.regularMarketPrice) {
			console.warn(`[priceRefresh] lib quote empty for ${symbol}`);
			return null;
		}

	return {
		price: quote.regularMarketPrice,
		previousClose: quote.previousClose ?? quote.regularMarketPreviousClose ?? null,
		currency: quote.currency ?? null,
		marketCap: quote.marketCap ?? null,
		regularMarketTime:
			quote.regularMarketTime instanceof Date
				? quote.regularMarketTime.toISOString()
				: new Date(quote.regularMarketTime * 1000).toISOString(),
	};
	} catch (err) {
		console.warn(`[priceRefresh] lib quote failed for ${symbol}: ${err.message}`);
		return null;
	}
}

async function fetchViaChart(symbol) {
	try {
		const response = await fetch(`${CHART_URL}/${encodeURIComponent(symbol)}`, {
			headers: { "User-Agent": BROWSER_UA },
		});
		// Log every response code — 429 watch (see PLAN-realtime-prices.md)
		console.info(`[priceRefresh] chart ${symbol} -> ${response.status}`);

		if (!response.ok) return null;

		const payload = await response.json();
		const meta = payload?.chart?.result?.[0]?.meta;
		if (!meta?.regularMarketPrice) {
			console.warn(`[priceRefresh] chart meta empty for ${symbol}`);
			return null;
		}

		return {
			price: meta.regularMarketPrice,
			previousClose: meta.chartPreviousClose ?? meta.previousClose ?? null,
			currency: meta.currency ?? null,
			regularMarketTime: new Date(
				(meta.regularMarketTime ?? Math.floor(Date.now() / 1000)) * 1000
			).toISOString(),
		};
	} catch (err) {
		console.warn(`[priceRefresh] chart fetch failed for ${symbol}: ${err.message}`);
		return null;
	}
}

/**
 * Map a fresh quote onto the stock_metric column shape.
 * Change fields are derived vs previousClose; percent is raw 0-1 (DB convention).
 * @param {object} quote - fetchQuote result
 * @returns {object} patch for upsertPriceRow
 */
export function quoteToMetricPatch(quote) {
	const change =
		quote.previousClose != null ? quote.price - quote.previousClose : null;
	const changePercent =
		change != null && quote.previousClose
			? change / quote.previousClose
			: null;

	return {
		stock_price: quote.price,
		market_cap: quote.marketCap,
		regular_market_change: change,
		regular_market_change_percent: changePercent,
		regular_market_time: quote.regularMarketTime,
		currency: quote.currency,
		maintenance_update: new Date().toISOString(),
	};
}
