import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

export default eventHandler(async (event) => {
	const { client } = supabaseClientAuth(event);
	const body = await readBody(event);
	const { watchlistId, stockSymbol } = body;

	if (!watchlistId) 
		throw createError({ statusCode: 400, statusMessage: 'Missing watchlistId' });
	else if (!stockSymbol)
		throw createError({ statusCode: 400, statusMessage: 'Missing stockSymbol' });

	const stock = await getStock(client, stockSymbol, ["id"])
	const { error } = await client
		.from('watchlist_item')
		.insert({
			watchlist_id: watchlistId,
			stock_id: stock.id
		});

	if (error) {
		throw createError({ statusCode: 500, statusMessage: error.message });
	}

	return { success: true };
});
