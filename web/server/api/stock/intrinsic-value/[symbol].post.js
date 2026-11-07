import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

import calculateIntrinsicValue from "~~/server/calculations/intrinsicValue";
import { getFinancialStatement, getQuote, getStock } from "#shared/query/stock";
import { validateIntrinsicValueInputs } from "#shared/validators/intrinsic-value";

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false);
	const symbol = getRouterParam(event, "symbol");
	if (!symbol) {
		throw createError({ statusCode: 400, statusMessage: 'Missing stock symbol' })
	}

	const body = await readBody(event) ?? {};
	const validation = validateIntrinsicValueInputs(body);
	if (!validation.valid) {
		throw createError({ statusCode: 400, statusMessage: 'Invalid input parameters' })
	}
	const { growthDiscount, cashFlowDiscount, safetyMargin, projectionHorizon } = validation.value;

	const stock = await getStock(client, symbol, ["id", "sector"]);
	const id = stock.id;

	// peer-median P/FCF (option A): reuse get_all_medians on both tables —
	// median market_cap (stock_quote) ÷ median free_cash_flow
	// (stock_statement_cash), scoped to the stock's sector
	const [medianQuote, medianCash] = await Promise.all([
		client.rpc('get_all_medians', {
			p_table_fa: 'stock_quote',
			p_table_stock: 'stock',
			p_stock_sector: stock.sector
		}),
		client.rpc('get_all_medians', {
			p_table_fa: 'stock_statement_cash',
			p_table_stock: 'stock',
			p_stock_sector: stock.sector
		}),
	]);

	if (medianQuote.error) throw createError({ statusCode: 500, statusMessage: medianQuote.error.message })
	if (medianCash.error) throw createError({ statusCode: 500, statusMessage: medianCash.error.message })

	const medianCap = medianQuote.data?.["market_cap"];
	const medianFcf = medianCash.data?.["free_cash_flow"];
	if (typeof medianCap !== "number" || typeof medianFcf !== "number" || medianFcf <= 0) {
		throw createError({ statusCode: 404, statusMessage: 'Peer price-to-FCF unavailable for this sector' })
	}
	const priceToFcf = medianCap / medianFcf;

	const quote = await getQuote(client, id, ["stock_price"]);
	// horizon may exceed the projection length: AGR uses up to 6 FCFs;
	// FY-only — quarterly statements duplicate the FY fiscal_date and
	// would break the strict newest-first ordering the calc requires
	const cashFlow = await getFinancialStatement(client, id, "stock_statement_cash", Math.max(projectionHorizon, 6), "FY");
	const balanceSheet = await getFinancialStatement(client, id, "stock_statement_balance", 1);

	return calculateIntrinsicValue(
		priceToFcf,
		quote["stock_price"],
		balanceSheet[0]["cash_cash_equivalents_and_short_term_investments"],
		balanceSheet[0]["share_issued"],
		cashFlow,
		growthDiscount,
		cashFlowDiscount,
		safetyMargin,
		projectionHorizon,
	);
});