import { supabaseClientAuth } from '~~/server/utils/supabase/auth';
import { getStock } from "#shared/query/stock";
import FINANCIALS_SHAPE, { FINANCIAL_GROUPS } from "#shared/logic/financial-analysis-shape"

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false)
	const symbol = getRouterParam(event, "symbol");
	if (!symbol) {
		throw createError({ statusCode: 400, statusMessage: 'Missing stock id' })
	}

	// Peer grouping uses the broad field (stock.sector) per GICS convention
	const { id, sector } = await getStock(client, symbol, ["id", "sector"])
	if (!id) {
		throw createError({ statusCode: 400, statusMessage: 'Invalid stock symbol' })
	}

	// TTM rows accumulate (one per pipeline run) — take the newest by
	// fiscal_date instead of maybeSingle(), which 404s on multiple rows
	const { data, error } = await client
		.from('stock_financial_analysis')
		.select('*')
		.eq('stock_id', id)
		.eq('period', 'TTM')
		.order('fiscal_date', { ascending: false })
		.limit(1)

	if (error)
		throw createError({ statusCode: 404, statusMessage: error.message })
	// limit(1) still returns an array — unwrap the single row
	const row = data?.[0]
	if (!row)
		throw createError({ statusCode: 404, statusMessage: 'No TTM financial analysis for this stock' })

	const { data: medianData, error: medianError } = await client
		.rpc('get_all_medians', {
			p_table_fa: 'stock_financial_analysis',
			p_table_stock: 'stock',
			p_stock_sector: sector
		})

	if (medianError) throw createError({ statusCode: 500, statusMessage: medianError.message })

	const result = {}
	for (const [key, meta] of Object.entries(FINANCIALS_SHAPE)) {
		result[key] = {
			value: row[key] ?? null,
			median: medianData?.[key] ?? null,
			group: meta.group,
			isPercentage: meta.isPercentage,
			valueAboveMedianIsGood: meta.valueAboveMedianIsGood
		}
	}

	return {
		maintenance_update: row.maintenance_update,
		quality_score: row.quality_score,
		median_comparison: row.median_comparison,
		groups: FINANCIAL_GROUPS,
		result,
	}
})
