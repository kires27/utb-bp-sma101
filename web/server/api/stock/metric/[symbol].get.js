import { supabaseClientAuth, useSupabaseAdmin } from '~~/server/utils/supabase/auth';

import { getStock, getMetric } from "#shared/query/stock";
import { getPriceRow, upsertPriceRow, touchSymbolActivity, isPriceStale } from "#shared/query/price";
import { fetchQuote, quoteToMetricPatch } from '~~/server/utils/stock/priceRefresh';

const PRICE_MAX_AGE_MS = 180_000; // 3 min — the throttle into Yahoo
const RETRY_BACKOFF_MS = 10 * 60_000; // after a failed fetch, wait 10 min before retrying

// In-flight dedupe within one server instance (per PLAN-realtime-prices.md).
// Cross-instance bursts handled by staleness check + idempotent upsert.
const inflight = new Map();
// last refresh attempt time per symbol — throttles retry storms when market
// is closed (quote time never advances) or Yahoo is down
const lastAttempt = new Map();

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false);
	const symbol = getRouterParam(event, "symbol");
	const { select } = getQuery(event);
	let columns = select ? select.split(',') : ["*"];
	// virtual fields computed server-side — strip before hitting Supabase
	const VIRTUAL = new Set(["price_age_seconds", "stale"]);
	const requestedVirtual = columns.filter((c) => VIRTUAL.has(c));
	if (!columns.includes("*")) {
		columns = columns.filter((c) => !VIRTUAL.has(c));
		if (!columns.length) columns = ["stock_price", "regular_market_time"];
	}

	const stock = await getStock(client, symbol, ["id", "symbol"]);
	const id = stock.id;
	let data = await getMetric(client, id, columns);

	// interest registry — fire-and-forget, never blocks or fails the request
	touchSymbolActivity(useSupabaseAdmin(), stock.symbol).catch((err) =>
		console.warn(`[metric] symbol_activity touch failed: ${err.message}`)
	);

	// staleness check only against full row (selected columns may omit timestamp)
	const priceRow = data
		? await getPriceRow(client, id, ["regular_market_time"])
		: null;
	const { stale, ageMs } = isPriceStale(priceRow, PRICE_MAX_AGE_MS);

	// retry throttle: if last attempt is recent, don't hammer Yahoo again
	// (covers market-closed weekends: quote time frozen, but we stop retrying)
	const attempted = lastAttempt.get(stock.symbol) ?? 0;
	const throttled = Date.now() - attempted < RETRY_BACKOFF_MS;

	// missing row = stale; refresh creates it on demand
	if ((!data || stale) && !throttled) {
		lastAttempt.set(stock.symbol, Date.now());
		data = await refreshPrice({ stockId: id, symbol: stock.symbol, current: data, columns });
	} else if (!data) {
		throw createError({
			statusCode: 502,
			statusMessage: `No cached price for ${symbol} — refresh recently attempted, retry soon`,
		});
	} else {
		if (ageMs != null) {
			// virtual field: computed here, never passed to Supabase select
			data = { ...data, price_age_seconds: Math.round(ageMs / 1000) };
		}
	}

	return data;
});

async function refreshPrice({ stockId, symbol, current, columns }) {
	// dedupe concurrent bursts for the same symbol in this instance
	if (inflight.has(symbol)) return inflight.get(symbol);

	const job = (async () => {
		const quote = await fetchQuote(symbol);

		if (!quote) {
			// NEVER cache failures, NEVER delete the old row — serve stale
			console.warn(`[metric] yahoo refresh failed for ${symbol}, serving stale`);
			if (current) return { ...current, stale: true };
			throw createError({
				statusCode: 502,
				statusMessage: `Price refresh failed for ${symbol} — no cached price available`,
			});
		}

		try {
			await upsertPriceRow(useSupabaseAdmin(), stockId, quoteToMetricPatch(quote));
		} catch (err) {
			console.warn(`[metric] price upsert failed for ${symbol}: ${err.message}`);
			return { ...current, stale: true };
		}

		// re-read merged row, restricted to requested columns
		const fresh = await getPriceRow(
			// admin client: bypasses RLS; row just written via same key
			useSupabaseAdmin(),
			stockId,
			["*"]
		);
		return filterColumns(fresh, columns);
	})();

	job.finally(() => inflight.delete(symbol));

	inflight.set(symbol, job);
	return job;
}

function filterColumns(row, columns) {
	// virtual freshness fields — added after Supabase query, never in select=
	if (columns.includes("*")) {
		return { ...row, price_age_seconds: 0 };
	}
	const picked = {};
	for (const col of columns) {
		if (col in row) picked[col] = row[col];
	}
	picked.price_age_seconds = 0;
	return picked;
}
