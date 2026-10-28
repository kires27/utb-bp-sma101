import { supabaseClientAuth } from '~~/server/utils/supabase/auth'

export default defineEventHandler(async (event) => {
	setResponseHeader(event, 'Cache-Control', 'public, max-age=86400, stale-while-revalidate=3600')

	const { client } = await supabaseClientAuth(event, false)
	const query = getQuery(event)
	if (!query.symbols) throw createError({ statusCode: 400, statusMessage: 'Missing symbols' })

	const symbols = query.symbols.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
	if (!symbols.length) throw createError({ statusCode: 400, statusMessage: 'Missing symbols' })

	const { data: stocks, error: stockErr } = await client
		.from('stock')
		.select('id, symbol, name')
		.in('symbol', symbols)

	if (stockErr) throw createError({ statusCode: 500, statusMessage: stockErr.message })

	const ids = stocks.map(s => s.id)
	const priceMap = new Map()

	if (ids.length) {
		const { data: metrics, error: metricErr } = await client
			.from('stock_metric')
			.select('stock_id, stock_price')
			.in('stock_id', ids)

		if (!metricErr) {
			for (const m of metrics) {
				priceMap.set(m.stock_id, m.stock_price)
			}
		}
	}

	const stockBySymbol = new Map(stocks.map(s => [s.symbol, s]))

	const results = symbols.map((symbol) => {
		const stock = stockBySymbol.get(symbol)
		if (!stock) return { symbol, name: symbol, price: null }
		return {
			symbol: stock.symbol,
			name: stock.name,
			price: priceMap.get(stock.id) ?? null,
		}
	})

	return { results }
})
