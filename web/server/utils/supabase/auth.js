import { createClient } from '@supabase/supabase-js'

export function useSupabaseAdmin() {
	const config = useRuntimeConfig()
	return createClient(config.supabaseUrl, config.supabaseSecretKey)
}

// !!!!!!!!!!!!!! NOTE !!!!!!!!!!!!!!!!!!!!!!! 
// for server-side authenticated user use:
// import { serverSupabaseClient } from '#supabase/server' 	→ to query database 
// import { serverSupabaseUser } from '#supabase/server'	→ to get info about user

import { serverSupabaseClient, serverSupabaseUser } from '#supabase/server'

export async function supabaseClientAuth(event, authorize=true) {
	const client = await serverSupabaseClient(event)
	let user = {};

	if (authorize) {
		user = await serverSupabaseUser(event)

		if (!user) {
			throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
		}
	}

	return { client, user };
}