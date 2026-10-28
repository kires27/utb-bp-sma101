export const TABLES = {
	stock: "stock",
	balance: "stock_balance_sheet",
	cash: "stock_cash_flow",
	income: "stock_income_statement",
	financial: "stock_financial_analysis",
	metric: "stock_metric",
	symbolActivity: "symbol_activity",
	watchlist: "watchlist",
	watchlistItem: "watchlist_item"
}

export const COLUMNS = {
	stock: {
		id: "id",
		symbol: "symbol"
	},
	symbolActivity: {
		symbol: "symbol",
		lastVisit: "last_visit"
	}
}
