import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

import calculateIntrinsicValue from "~~/server/calculations/intrinsicValue";
import { getFinancialStatement, getMetric, getStock } from "#shared/query/stock";
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

	const stock = await getStock(client, symbol, ["id"]);
	const id = stock.id;

	const metrics = await getMetric(client, id, ["market_cap", "stock_price"]);
	const cashFlow = await getFinancialStatement(client, id, "stock_cash_flow", projectionHorizon);
	const balanceSheet = await getFinancialStatement(client, id, "stock_balance_sheet", 1);

	return calculateIntrinsicValue(
		metrics["market_cap"],
		metrics["stock_price"],
		balanceSheet[0]["cash_cash_equivalents_and_short_term_investments"],
		balanceSheet[0]["share_issued"],
		cashFlow,
		growthDiscount,
		cashFlowDiscount,
		safetyMargin,
	);
});