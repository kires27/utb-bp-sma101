import { supabaseClientAuth } from '~~/server/utils/supabase/auth'
import { getStock } from "#shared/query/stock"

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false)
	const symbol = getRouterParam(event, "symbol")
	if (!symbol) {
		throw createError({ statusCode: 400, statusMessage: 'Missing stock symbol' })
	}

	const { id } = await getStock(client, symbol, ["id"])
	if (!id) {
		throw createError({ statusCode: 400, statusMessage: 'Invalid stock symbol' })
	}

	const [{ data: dividends, error: divErr }, { data: splits, error: splitErr }] = await Promise.all([
		client.from('stock_dividend').select('date, dividend').eq('stock_id', id).order('date', { ascending: false }),
		client.from('stock_split').select('date, factor').eq('stock_id', id).order('date', { ascending: false }),
	])

	if (divErr) throw createError({ statusCode: 500, statusMessage: divErr.message })
	if (splitErr) throw createError({ statusCode: 500, statusMessage: splitErr.message })

	return {
		dividends: (dividends ?? []).map(d => ({ date: d.date, amount: d.dividend })),
		splits: (splits ?? []).map(s => ({ date: s.date, factor: Number(s.factor) })),
	}
})
