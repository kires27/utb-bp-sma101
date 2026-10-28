import { supabaseClientAuth } from '~~/server/utils/supabase/auth';
import { getStock } from "#shared/query/stock";
import FINANCIALS_SHAPE, { FINANCIAL_GROUPS } from "#shared/logic/financial-analysis-shape"

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false)
	const symbol = getRouterParam(event, "symbol");
	if (!symbol) {
		throw createError({ statusCode: 400, statusMessage: 'Missing stock id' })
	}

	const { id, industry } = await getStock(client, symbol, ["id", "industry"])
	if (!id) {
		throw createError({ statusCode: 400, statusMessage: 'Invalid stock symbol' })
	}

	const { data, error } = await client
		.from('stock_financial_analysis')
		.select('*')
		.eq('stock_id', id)
		.eq('period', 'TTM')
		.maybeSingle()

	if (error || !data)
		throw createError({ statusCode: 404, statusMessage: error.message })


	const { data: medianData, error: medianError } = await client
		.rpc('get_all_medians', {
			p_table_fa: 'stock_financial_analysis',
			p_table_stock: 'stock',
			p_stock_industry: industry
		})

	if (medianError) throw createError({ statusCode: 500, statusMessage: medianError.message })

	const result = {}
	for (const [key, meta] of Object.entries(FINANCIALS_SHAPE)) {
		result[key] = {
			value: data[key] ?? null,
			median: medianData?.[key] ?? null,
			group: meta.group,
			isPercentage: meta.isPercentage,
			valueAboveMedianIsGood: meta.valueAboveMedianIsGood
		}
	}

	return {
		maintenance_update: data.maintenance_update,
		quality_score: data.quality_score,
		median_comparison: data.median_comparison,
		groups: FINANCIAL_GROUPS,
		result,
	}
})
