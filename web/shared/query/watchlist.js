export async function getWatchlistId(client, name) {
	const { data, error } = await client
		.from('watchlist')
		.select('id')
		.eq('name', name)
		.single()

	if (error) throw new Error(error.message)

	return data.id
}

export async function getUserWatchlists(client, userId, columns = ["id", "name", "created_at"]) {
	const selectColumns = columns.join(",");
	const { data, error } = await client
		.from('watchlist')
		.select(selectColumns)
		.eq('user_id', userId)
		.order('created_at', { ascending: false })

	if (error) throw new Error(error.message)

	return data
}

export async function getUserWatchlistById(client, userId, watchlistId) {
	const { data, error } = await client
		.from('watchlist')
		.select('id, name')
		.eq('id', watchlistId)
		.eq('user_id', userId)
		.single()

	if (error || !data) {
		throw createError({ statusCode: 404, statusMessage: 'Watchlist not found' })
	}

	return data
}

export async function getWatchlistItems(client, watchlistId, limit) {
	const { data, error } = await client
		.from('watchlist_item')
		.select('stock_id, stock!inner(symbol)')
		.eq('watchlist_id', watchlistId)
		.order('added_at', { ascending: false })
		.limit(limit)

	if (error) throw new Error(error.message)


	return data
}