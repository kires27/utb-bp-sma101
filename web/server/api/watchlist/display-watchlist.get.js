import { supabaseClientAuth } from '~~/server/utils/supabase/auth'
import FINANCIALS_SHAPE from '~~/shared/logic/financial-analysis-shape'

function emptyResult(symbol) {
	return { symbol, stock_price: null, quality_score: null, maintenance_update: null, result: {} }
}

async function fetchDetails(client, symbols) {
	// 1. Batch stock lookup — one query, all symbols
	const { data: stocks, error: stockErr } = await client
		.from('stock')
		// sector = broad peer-group field (GICS convention)
		.select('id, symbol, sector')
		.in('symbol', symbols)

	if (stockErr) throw createError({ statusCode: 500, statusMessage: stockErr.message })

	const stockBySymbol = new Map(stocks.map(s => [s.symbol, s]))
	const ids = stocks.map(s => s.id)
	if (!ids.length) return symbols.map(emptyResult)

	// 2. Batch financial_analysis + quote — two queries total, not one per stock
	const [{ data: analyses, error: analysisErr }, { data: quotes, error: quoteErr }] = await Promise.all([
		client.from('stock_financial_analysis').select('*').in('stock_id', ids).eq('period', 'TTM'),
		client.from('stock_quote').select('stock_id, stock_price').in('stock_id', ids),
	])
	if (analysisErr) throw createError({ statusCode: 500, statusMessage: analysisErr.message })
	if (quoteErr) throw createError({ statusCode: 500, statusMessage: quoteErr.message })

	const analysisByStockId = new Map(analyses.map(a => [a.stock_id, a]))
	const quoteByStockId = new Map(quotes.map(q => [q.stock_id, q]))

	// 3. Dedupe sectors — one RPC call per DISTINCT sector, not per symbol
	const sectors = [...new Set(stocks.map(s => s.sector).filter(Boolean))]
	const medianEntries = await Promise.all(
		sectors.map(async (sector) => {
			const { data } = await client.rpc('get_all_medians', {
				p_table_fa: 'stock_financial_analysis',
				p_table_stock: 'stock',
				p_stock_sector: sector,
			})
			return [sector, data]
		})
	)
	const medianBySector = new Map(medianEntries)

	// 4. Assemble in memory — no more DB calls
	return symbols.map((symbol) => {
		const stock = stockBySymbol.get(symbol)
		if (!stock) return emptyResult(symbol)

		const quote = quoteByStockId.get(stock.id)
		const analysis = analysisByStockId.get(stock.id)
		if (!analysis) {
			return { symbol, stock_price: quote?.stock_price ?? null, quality_score: null, maintenance_update: null, result: {} }
		}

		const medianData = medianBySector.get(stock.sector)
		const result = {}
		for (const key of Object.keys(FINANCIALS_SHAPE)) {
			result[key] = { value: analysis[key] ?? null, median: medianData?.[key] ?? null }
		}

		return {
			symbol,
			stock_price: quote?.stock_price ?? null,
			quality_score: analysis.quality_score,
			maintenance_update: analysis.maintenance_update,
			result,
		}
	})
}

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false)
	const query = getQuery(event)

	let symbols
	if (query.symbols) {
		symbols = query.symbols.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
		if (!symbols.length) throw createError({ statusCode: 400, statusMessage: 'Missing symbols' })
	} else {
		const symbol = getRouterParam(event, 'symbol')
		if (!symbol) throw createError({ statusCode: 400, statusMessage: 'Missing stock symbol' })
		symbols = [symbol]
	}

	const results = await fetchDetails(client, symbols)
	return { results }
})