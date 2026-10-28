import { supabaseClientAuth } from '~~/server/utils/supabase/auth';

const PAGE_SIZE = 20

export default defineEventHandler(async (event) => {
    const { client } = await supabaseClientAuth(event, false)

    const offset = Number(getRouterParam(event, 'limit'))

    if (!Number.isInteger(offset) || offset < 0) {
        throw createError({
            statusCode: 400,
            statusMessage: 'Invalid offset',
        })
    }

    const search = String(getQuery(event).q ?? '').trim()

    let query = client
        .from('stock')
        .select('symbol, logo, name')
        .order('symbol')

    if (search.length >= 2) {
        const pattern = `%${search}%`

        query = query.or(
            `symbol.ilike.${pattern},name.ilike.${pattern}`
        )
    }

    const { data: stocks, error } = await query.range(
        offset,
        offset + PAGE_SIZE - 1
    )

    if (error) {
        throw createError({
            statusCode: 500,
            statusMessage: error.message,
        })
    }

    return stocks
})