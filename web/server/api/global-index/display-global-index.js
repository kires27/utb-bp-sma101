import { supabaseClientAuth } from '~~/server/utils/supabase/auth'
import FINANCIALS_SHAPE from '~~/shared/logic/financial-analysis-shape'

const PAGE_SIZE = 20

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false)
	const query = getQuery(event)
	const offset = Number(query.offset || 0)
	const limit = Number(query.limit || PAGE_SIZE)

	// Page + full FA data in one query — includes quality_score for ordering
	const { data: page, error: pageErr } = await client
		.from('stock_financial_analysis')
		.select('*')
		.eq('period', 'TTM')
		.order('quality_score', { ascending: false, nullsFirst: false })
		.range(offset, offset + limit - 1)

	if (pageErr)
		throw createError({ statusCode: 500, statusMessage: pageErr.message })
	if (!page?.length) return []

	const stockIds = page.map((r) => r.stock_id)
	const faByStockId = Object.fromEntries(page.map((r) => [r.stock_id, r]))

	// stocks + metrics don't depend on each other — parallelize
	const [{ data: stocks, error: stocksErr }, { data: metrics, error: metricsErr }] = await Promise.all([
		client.from('stock').select('id, symbol, industry').in('id', stockIds),
		client.from('stock_metric').select('stock_id, stock_price').in('stock_id', stockIds),
	])

	if (stocksErr)
		throw createError({ statusCode: 500, statusMessage: stocksErr.message })
	if (metricsErr)
		throw createError({ statusCode: 500, statusMessage: metricsErr.message })

	const stockById = Object.fromEntries((stocks || []).map((s) => [s.id, s]))
	const priceMap = Object.fromEntries((metrics || []).map((m) => [m.stock_id, m.stock_price]))

	const sortedStocks = stockIds.map((id) => stockById[id]).filter(Boolean)
	const industries = [...new Set(sortedStocks.map((s) => s.industry).filter(Boolean))]

	// Median RPCs are independent per industry — parallelize
	const medianEntries = await Promise.all(
		industries.map(async (industry) => {
			const { data: medians } = await client.rpc('get_all_medians', {
				p_table_fa: 'stock_financial_analysis',
				p_table_stock: 'stock',
				p_stock_industry: industry,
			})
			return [industry, medians]
		})
	)
	const medianMap = Object.fromEntries(medianEntries.filter(([, m]) => m))

	return sortedStocks.map((s) => {
		const fa = faByStockId[s.id] || {}
		const result = {}
		for (const key of Object.keys(FINANCIALS_SHAPE)) {
			result[key] = {
				value: fa[key] ?? null,
				median: medianMap[s.industry]?.[key] ?? null,
			}
		}
		return {
			symbol: s.symbol,
			stock_price: priceMap[s.id] ?? null,
			quality_score: fa.quality_score ?? null,
			maintenance_update: fa.maintenance_update ?? null,
			result,
		}
	})
})