import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

import { getStock, getExchangeInfo } from "#shared/query/stock";

// static reference data (exchange session times) — safe to cache publicly
const CACHE_CONTROL = "public, max-age=86400, stale-while-revalidate=3600";

export default defineEventHandler(async (event) => {
    const {client} = await supabaseClientAuth(event, false);
    const symbol = getRouterParam(event, "symbol");

    const data = await getStock(client, symbol, ["*"]);

    // exchange session data for the market-status badge (nullable:
    // exchange_code may reference an exchange not in stock_exchange)
    const exchange_info = data.exchange
        ? await getExchangeInfo(client, data.exchange).catch(() => null)
        : null;

    setResponseHeader(event, 'Cache-Control', CACHE_CONTROL);
    return { ...data, exchange_info };
})
