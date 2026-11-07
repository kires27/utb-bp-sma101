import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

import { getStock, countFinancialStatement } from "#shared/query/stock";

// projection horizon must not exceed the real number of FY cash flows —
// the POST endpoint's DCF fetch is FY-only, so this count is FY-only too
// (quarterly rows duplicate fiscal_date and would inflate the cap)
export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false);
	const symbol = getRouterParam(event, "symbol");
	if (!symbol) {
		throw createError({ statusCode: 400, statusMessage: 'Missing stock symbol' })
	}

	const stock = await getStock(client, symbol, ["id"]);
	if (!stock.id) {
		throw createError({ statusCode: 400, statusMessage: 'Invalid stock symbol' })
	}

	const count = await countFinancialStatement(client, stock.id, "stock_statement_cash", "FY");

	return { available_years: count };
});
