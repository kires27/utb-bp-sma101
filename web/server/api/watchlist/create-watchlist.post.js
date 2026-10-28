import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

export default eventHandler(async (event) => {
	const { client, user } = await supabaseClientAuth(event);
	const body = await readBody(event);
	const { name } = body;

	if (!name || typeof name !== 'string' || name.trim().length === 0) {
		throw createError({ statusCode: 400, statusMessage: 'Watchlist name required' });
	}
	const trimmedName = name.trim();

	const { data, error } = await client
		.from('watchlist')
		.insert({
			name: trimmedName,
			user_id: user.sub
		})
		.select('id, name, created_at')
		.single();

	if (error) throw createError({ statusCode: 500, statusMessage: error.message });

	return { success: true, data };
});
