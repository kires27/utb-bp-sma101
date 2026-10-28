import { supabaseClientAuth } from '~~/server/utils/supabase/auth'
import { getUserWatchlists } from '#shared/query/watchlist'

export default eventHandler(async (event) => {
	const { client, user } = await supabaseClientAuth(event)

	return getUserWatchlists(client, user.sub)
})
