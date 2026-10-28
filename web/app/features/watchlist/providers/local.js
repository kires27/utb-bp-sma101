const LS_LISTS = "wl-lists"
const LS_ITEMS_PREFIX = "wl-items-"

function readJSON(key, fallback) {
	if (!import.meta.client) return fallback
	try {
		return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback))
	} catch {
		return fallback
	}
}

function writeJSON(key, value) {
	if (!import.meta.client) return
	localStorage.setItem(key, JSON.stringify(value))
}

function normalizeName(name) {
	return String(name || "").trim()
}

function normalizeSymbol(symbol) {
	return String(symbol || "").trim().toUpperCase()
}

function makeId() {
	return globalThis.crypto?.randomUUID?.() || String(Date.now())
}

function itemsKey(id) {
	return `${LS_ITEMS_PREFIX}${id}`
}

function hasStock(listId, symbol) {
	const items = readJSON(itemsKey(listId), [])
	return items.includes(symbol)
}

export function createLocalWatchlistProvider() {
	return {
		async list(symbol = "") {
			const watchlists = readJSON(LS_LISTS, [])
			const upperSymbol = normalizeSymbol(symbol)

			if (!upperSymbol) return watchlists

			return watchlists.map((watchlist) => ({
				...watchlist,
				hasStock: hasStock(watchlist.id, upperSymbol),
			}))
		},

		async create(name) {
			const trimmed = normalizeName(name)
			const watchlists = readJSON(LS_LISTS, [])
			const watchlist = {
				id: makeId(),
				name: trimmed,
				created_at: new Date().toISOString(),
			}

			watchlists.unshift(watchlist)
			writeJSON(LS_LISTS, watchlists)
			return watchlist
		},

		async rename(id, name) {
			const trimmed = normalizeName(name)
			const watchlists = readJSON(LS_LISTS, [])
			const next = watchlists.map((watchlist) => (
				String(watchlist.id) === String(id)
					? { ...watchlist, name: trimmed }
					: watchlist
			))

			writeJSON(LS_LISTS, next)
			return next.find((watchlist) => String(watchlist.id) === String(id)) || null
		},

		async delete(id) {
			const watchlists = readJSON(LS_LISTS, [])
			const next = watchlists.filter((watchlist) => String(watchlist.id) !== String(id))
			writeJSON(LS_LISTS, next)
			if (import.meta.client) localStorage.removeItem(itemsKey(id))
			return true
		},

		async items(id) {
			if (!id) return []
			return readJSON(itemsKey(id), [])
		},

		async addItem(id, symbol) {
			if (!id) return []
			const upperSymbol = normalizeSymbol(symbol)
			const items = readJSON(itemsKey(id), [])
			if (!items.includes(upperSymbol)) {
				items.push(upperSymbol)
				writeJSON(itemsKey(id), items)
			}
			return items
		},

		async removeItem(id, symbol) {
			if (!id) return []
			const upperSymbol = normalizeSymbol(symbol)
			const items = readJSON(itemsKey(id), [])
			const next = items.filter((item) => item !== upperSymbol)
			writeJSON(itemsKey(id), next)
			return next
		},
	}
}
