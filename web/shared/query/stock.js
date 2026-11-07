/**
 * @param {any} client - supabase client
 * @param {string} symbol 
 * @param {string[]} columns 
 * @returns {Promise<object>}
 */
export async function getStock(client, symbol, columns = ["*"]) {
	const selectClause = columns.join(',')
	symbol = symbol.toUpperCase()

	const { data, error } = await client
		.from('stock')
		.select(selectClause)
		.eq('symbol', symbol)
		.single()

	if (error) throw new Error(error.message)

	return data
}

export async function getQuote(supabase, stockId, selectColumns = ["*"]) {
	const selectClause = selectColumns.join(',')

	const { data, error } = await supabase
		.from('stock_quote')
		.select(selectClause)
		.eq('stock_id', stockId)
		.limit(1);

	if (error) throw new Error(error.message)

	return data[0];
}


/**
 * count of statements matching an optional period filter — used by the
 * intrinsic-value page to cap the user-picked projection horizon at the
 * real number of FY cash flows available
 * @param {*} supabase
 * @param {number} stockId
 * @param {"stock_statement_cash" | "stock_statement_balance" | "stock_statement_income"} statementTable
 * @param {string} [period] optional period filter ("FY", "Q1", ...)
 * @returns {Promise<number>}
 */
export async function countFinancialStatement(supabase, stockId, statementTable, period = null) {
	let query = supabase
		.from(statementTable)
		.select('*', { count: 'exact', head: true })
		.eq('stock_id', stockId);

	if (period) query = query.eq('period', period);

	const { count, error } = await query;

	if (error) throw new Error(error.message)

	return count ?? 0
}

/**
 * return array of objects, starting from newest
 * @param {*} supabase
 * @param {string} symbol
 * @param {"stock_statement_cash" | "stock_statement_balance" | "stock_statement_income"} statementTable
 * @param {number} limit
 * @param {string} [period] optional period filter ("FY", "Q1", ...) —
 * quarterly statements share fiscal_date with the FY filing (e.g.
 * 2025-09-30 Q3 + FY), which breaks the strict newest-first ordering
 * the DCF math requires; FY-only matches the canonical model
 * @returns {Promise<object[]>}
 */
export async function getFinancialStatement(supabase, stockId, statementTable, limit = 5, period = null) {
	let query = supabase
		.from(statementTable)
		.select('*')
		.eq('stock_id', stockId)
		.order("fiscal_date", { ascending: false })
		.limit(limit);

	if (period) query = query.eq('period', period);

	const { data, error } = await query;

	if (error) throw new Error(error.message)

	return data
}

/**
 * exchange session metadata for the market-status badge
 * @param {any} client - supabase client
 * @param {string} exchangeCode - e.g. "NasdaqGS"
 * @returns {Promise<object|null>} null when exchange_code is unknown
 */
export async function getExchangeInfo(client, exchangeCode) {
	const { data, error } = await client
		.from('stock_exchange')
		.select('timezone, open_time, break_start_time, break_end_time, close_time, week_pattern, short_name')
		.eq('exchange_code', exchangeCode)
		.maybeSingle()

	if (error) throw new Error(error.message)

	return data
}
