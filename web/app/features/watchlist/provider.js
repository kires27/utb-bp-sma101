import { createLocalWatchlistProvider } from "./providers/local"
import { createSupabaseWatchlistProvider } from "./providers/supabase"
import { API } from "#shared/constants/routes"

function provider() {
	const user = useSupabaseUser()
	return user.value
		? createSupabaseWatchlistProvider()
		: createLocalWatchlistProvider()
}

function cleanName(name) {
	const value = String(name || "").trim()
	if (!value) throw new Error("Watchlist name required")
	return value
}

function cleanSymbol(symbol) {
	const value = String(symbol || "").trim().toUpperCase()
	if (!value) throw new Error("Stock symbol required")
	return value
}

const watchlist = {
	list(symbol = "") {
		return provider().list(symbol)
	},

	create(name) {
		return provider().create(cleanName(name))
	},

	rename(id, name) {
		return provider().rename(id, cleanName(name))
	},

	delete(id) {
		return provider().delete(id)
	},

	items(id) {
		return provider().items(id)
	},

	addItem(id, symbol) {
		return provider().addItem(id, cleanSymbol(symbol))
	},

	removeItem(id, symbol) {
		return provider().removeItem(id, cleanSymbol(symbol))
	},

	async getDetailedItems(id) {
		if (!id) return []
		const items = await provider().items(id)
		if (!items.length) return []

		try {
			const { results } = await $fetch(API.watchlist.get_watchlist(items))
			return results
		} catch {
			return items.map((symbol) => ({
				symbol,
				stock_price: null,
				quality_score: null,
				maintenance_update: null,
				result: {},
			}))
		}
	},
}

export function useWatchlist() {
	return watchlist
}
