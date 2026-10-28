import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

export default defineEventHandler(async (event) => {
	const { client } = await supabaseClientAuth(event, false);
	const input = getRouterParam(event, "input");

	let { data, error } = await client
		.from('stock')
		.select('logo,symbol,name,exchange')
		.or(`symbol.ilike.%${input}%,name.ilike.%${input}%`)
		.limit(5);

	if (error) throw createError({ statusCode: 500, statusMessage: error.message });

	return data;
})
