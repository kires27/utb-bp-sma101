import { getStock } from "#shared/query/stock"
import { getUserWatchlists } from "#shared/query/watchlist"

function normalizeName(name) {
	return String(name || "").trim()
}

function normalizeSymbol(symbol) {
	return String(symbol || "").trim().toUpperCase()
}

async function getUserId(user) {
	const id = user.value?.sub
	if (!id) throw new Error("Unauthorized")
	return id
}

export function createSupabaseWatchlistProvider() {
	const client = useSupabaseClient()
	const user = useSupabaseUser()

	return {
		async list(symbol = "") {
			const userId = await getUserId(user)
			const watchlists = await getUserWatchlists(client, userId, ["id", "name", "created_at"]);
			if (!normalizeSymbol(symbol)) return watchlists || []

			const { id: stockId } = await getStock(client, symbol, ["id"])
			if (!stockId) {
				return watchlists || []
			}

			const { data: memberships, error: membershipError } = await client
				.from("watchlist_item")
				.select("watchlist_id")
				.eq("stock_id", stockId)
				.in("watchlist_id", (watchlists || []).map((watchlist) => watchlist.id))

			if (membershipError) return watchlists || []

			const hasStock = new Set((memberships || []).map((item) => item.watchlist_id))
			return (watchlists || []).map((watchlist) => ({
				...watchlist,
				hasStock: hasStock.has(watchlist.id),
			}))
		},

		async create(name) {
			const userId = await getUserId(user)
			const trimmed = normalizeName(name)
			const { data, error } = await client
				.from("watchlist")
				.insert({ name: trimmed, user_id: userId })
				.select("id, name, created_at")
				.single()

			if (error) throw new Error(error.message)
			return data
		},

		async rename(id, name) {
			const userId = await getUserId(user)
			const trimmed = normalizeName(name)
			const { data, error } = await client
				.from("watchlist")
				.update({ name: trimmed })
				.eq("id", id)
				.eq("user_id", userId)
				.select("id, name, created_at")
				.single()

			if (error) throw new Error(error.message)
			return data
		},

		async delete(id) {
			const userId = await getUserId(user)
			await client.from("watchlist_item").delete().eq("watchlist_id", id)
			const { error } = await client
				.from("watchlist")
				.delete()
				.eq("id", id)
				.eq("user_id", userId)

			if (error) throw new Error(error.message)
			return true
		},

		async items(id) {
			if (!id) return []
			await getUserId(user)
			const { data: rows, error } = await client
				.from("watchlist_item")
				.select("stock_id")
				.eq("watchlist_id", id)

			if (error) throw new Error(error.message)
			if (!rows?.length) return []

			const stockIds = rows.map((row) => row.stock_id)
			const { data: stocks, error: stockError } = await client
				.from("stock")
				.select("id, symbol")
				.in("id", stockIds)

			if (stockError) throw new Error(stockError.message)
			return (stocks || []).map((stock) => stock.symbol)
		},

		async addItem(id, symbol) {
			if (!id) return true
			const userId = await getUserId(user)
			const upperSymbol = normalizeSymbol(symbol)

			const { data: watchlist, error: wlError } = await client
				.from("watchlist")
				.select("id")
				.eq("id", id)
				.eq("user_id", userId)
				.single()

			if (wlError || !watchlist) throw new Error("Watchlist not found")

			const { id: stockId } = await getStock(client, symbol, ["id"])

			const { error } = await client
				.from("watchlist_item")
				.insert({ watchlist_id: id, stock_id: stockId })

			if (error && error.code !== "23505") throw new Error(error.message)
			return true
		},

		async removeItem(id, symbol) {
			if (!id) return true
			const userId = await getUserId(user)
			const upperSymbol = normalizeSymbol(symbol)

			const { data: watchlist, error: wlError } = await client
				.from("watchlist")
				.select("id")
				.eq("id", id)
				.eq("user_id", userId)
				.single()

			if (wlError || !watchlist) throw new Error("Watchlist not found")

			const { id: stockId } = await getStock(client, symbol, ["id"])

			const { error } = await client
				.from("watchlist_item")
				.delete()
				.eq("watchlist_id", id)
				.eq("stock_id", stockId)

			if (error) throw new Error(error.message)
			return true
		},
	}
}
