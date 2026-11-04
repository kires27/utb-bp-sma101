import { TABLES } from "../constants/database.js";

/**
 * Read one stock_quote row by stock_id.
 * @param {any} client - supabase client
 * @param {number} stockId
 * @param {string[]} columns
 * @returns {Promise<object|null>}
 */
export async function getPriceRow(client, stockId, columns = ["*"]) {
	const selectClause = columns.join(",");

	const { data, error } = await client
		.from(TABLES.quote)
		.select(selectClause)
		.eq("stock_id", stockId)
		.limit(1);

	if (error) throw new Error(error.message);

	return data[0] ?? null;
}

/**
 * Upsert price fields into stock_quote (service-key client expected).
 * @param {any} client - supabase client (admin)
 * @param {number} stockId
 * @param {object} patch - { stock_price, market_cap, regular_market_change,
 *   regular_market_change_percent, regular_market_time, currency }
 * @returns {Promise<void>}
 */
export async function upsertPriceRow(client, stockId, patch) {
	const row = { stock_id: stockId, ...patch };

	const { error } = await client
		.from(TABLES.quote)
		.upsert(row, { onConflict: "stock_id" });

	if (error) throw new Error(error.message);
}

/**
 * Staleness check against regular_market_time (UTC ISO string).
 * Missing/null timestamp counts as stale.
 * @param {object|null} row - stock_quote row
 * @param {number} maxAgeMs - default 3 minutes
 * @returns {{ stale: boolean, ageMs: number|null }}
 */
export function isPriceStale(row, maxAgeMs = 180_000) {
	const ts = row?.regular_market_time;
	if (!ts) return { stale: true, ageMs: null };

	const ageMs = Date.now() - new Date(ts).getTime();
	return { stale: ageMs > maxAgeMs, ageMs };
}
