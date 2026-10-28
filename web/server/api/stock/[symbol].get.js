import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

export default defineEventHandler(async (event) => {
    const {client} = await supabaseClientAuth(event, false);
    const symbol = getRouterParam(event, "symbol");
    // const client = await serverSupabaseClient(event)

    let { data, error } = await client
        .from('stock')
        .select('*')
        .eq('symbol', symbol)
        .single(1);

    if (error) throw createError({ statusCode: 500, statusMessage: error.message });

    return data;
})
