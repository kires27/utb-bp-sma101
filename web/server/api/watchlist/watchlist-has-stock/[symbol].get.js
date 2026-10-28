import { getStock } from '#shared/query/stock';
import { getUserWatchlists } from '#shared/query/watchlist';
import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

export default eventHandler(async (event) => {
	const { client, user } = supabaseClientAuth(event);
	const symbol = getRouterParam(event, 'symbol');

	if (!symbol)
		throw createError({ statusCode: 400, statusMessage: 'Missing symbol' });

	// async call in parallel
	const [watchlists, stock] = await Promise.all([
		getUserWatchlists(client, user.sub, ['id']),
		getStock(client, symbol, ['id']),
	])

	const { data: watchlistsWithStock, error } = await client
		.from('watchlist_item')
		.select('watchlist_id')
		.eq('stock_id', stock.id)

	if (error) {
		throw createError({
			statusCode: 500,
			statusMessage: error.message,
		})
	}

	const watchlistIdsWithStock = new Set(
		watchlistsWithStock.map(wws => wws.watchlist_id)
	)

	// Returns a lookup table where:
	// - key = watchlist ID
	// - value = true if the requested stock exists in that watchlist, otherwise false.
	//
	// Example:
	// {
	//   "2": false,
	//   "15": false,
	//   "51": true
	// }
	const watchlistResult = Object.fromEntries(
		watchlists.map(w => [
			w.id,
			watchlistIdsWithStock.has(w.id),
		])
	)

	return watchlistResult
});
