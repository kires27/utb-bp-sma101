import { supabaseClientAuth } from '~~/server/utils/supabase/auth'
import { getUserWatchlistById, getWatchlistItems } from '#shared/query/watchlist'

export default eventHandler(async (event) => {
	const { client, user } = await supabaseClientAuth(event);
	const query = getQuery(event);
	const watchlistId = parseInt(query.id, 10);
	const limit = parseInt(query.limit, 10) || 20;

	if (!watchlistId || isNaN(watchlistId)) {
		throw createError({ statusCode: 400, statusMessage: 'Watchlist id required' });
	}

	const watchlistData = await getUserWatchlistById(client, user.sub, watchlistId);
	const watchlistItems = await getWatchlistItems(client, watchlistId, limit);

	const symbols = watchlistItems.map(i => i.stock?.symbol).filter(Boolean)
	return { watchlist: watchlistData, items: symbols }
})
