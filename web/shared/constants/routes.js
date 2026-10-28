export const URI = {
	home: '/',
	user: {
		settings: '/user/settings',
		login: '/auth/login',
		register: '/auth/register',
		// detail: (id) => `/user/${id}`
	},
	tool: {
		fa: '/fundamental-analysis',
		fa_financials: (symbol) => `/fundamental-analysis/${symbol}/financials`,
		fa_iv: (symbol) => `/fundamental-analysis/${symbol}/intrinsic-value`,
		fa_stock_profile: (symbol) => `/fundamental-analysis/${symbol}/stock-profile`,
		congress: '/congress',
		watchlist: '/watchlist',
		global_index: "/global-index"
	},
	about: '/about-us',
	privacy: '/privacy',
	terms: '/terms',
	disclaimer: '/disclaimer',
	listStocks: '/available-stocks'
}

export const API = {
	auth: {
		login: '/api/user/login',
		logout: '/api/user/logout'
	},
	users: {
		list: '/api/users',
		detail: (id) => `/api/users/${id}`,
		create: '/api/users',
		update: (id) => `/api/users/${id}`,
		delete: (id) => `/api/users/${id}`
	},
	watchlist: {
		get_lists: "/api/watchlist/list-of-watchlists",
		get_items: (id, limit) => `/api/watchlist/watchlist-items?id=${id}&limit=${limit}`,
		get_watchlist: (symbols) => {
			const joined = Array.isArray(symbols) ? symbols.join(",") : symbols
			return `/api/watchlist/display-watchlist?symbols=${joined}`
		}
	},
	stocks: {
		list: (limit) => `/api/stock/stock-list/${limit}`,
		get_stock: (symbol) => `/api/stock/${symbol}`,
		get_metric: (symbol) => `/api/stock/metric/${symbol}`,
		get_financials: (symbol) => `/api/stock/financial-analysis/${symbol}`,
		get_events: (symbol) => `/api/stock/events/${symbol}`,
		get_intrinsic_value: (symbol) => `/api/stock/intrinsic-value/${symbol}`,
		get_search_history: (symbols) => {
			const joined = Array.isArray(symbols) ? symbols.join(',') : symbols
			return `/api/stock/search-history?symbols=${joined}`
		},
		global_index: (offset) => `/api/global-index/display-global-index?offset=${offset}&limit=20`,

	}
}