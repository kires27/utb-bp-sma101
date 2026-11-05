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
 * return array of objects, starting from newest
 * @param {*} supabase 
 * @param {string} symbol 
 * @param {"stock_statement_cash" | "stock_statement_balance" | "stock_statement_income"} statementTable 
 * @param {number} limit 
 * @returns {Promise<object[]>}
 */
export async function getFinancialStatement(supabase, stockId, statementTable, limit = 5) {
	const { data, error } = await supabase
		.from(statementTable)
		.select('*')
		.eq('stock_id', stockId)
		.order("fiscal_date", { ascending: false })
		.limit(limit);

	if (error) throw new Error(error.message)

	return data
}
