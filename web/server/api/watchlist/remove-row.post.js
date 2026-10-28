import { supabaseClientAuth } from '~~/server/utils/supabase/auth';
import { getStock } from '#shared/query/stock';

export default eventHandler(async (event) => {
	const { client, user } = supabaseClientAuth(event);
	const body = await readBody(event);
	const { watchlistId, stockSymbol } = body;

	if (!watchlistId) 
		throw createError({ statusCode: 400, statusMessage: 'Missing watchlistId' });
	else if (!stockSymbol)
		throw createError({ statusCode: 400, statusMessage: 'Missing stockSymbol' });

	const stock = await getStock(client, stockSymbol, ["id"])
	const { error } = await client
		.from('watchlist_item')
		.delete()
		.eq('watchlist_id', watchlistId)
		.eq('stock_id', stock.id);

	if (error) throw createError({ statusCode: 500, statusMessage: error.message });

	return { success: true };
});
