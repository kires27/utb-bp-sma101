import { ref, computed } from "vue"

export function useWatchlistView(detailedItems) {
	const filterQuery = ref("")
	const sortColumn = ref(null)

	const filteredItems = computed(() => {
		let result = detailedItems.value

		if (filterQuery.value) {
			const q = filterQuery.value.toLowerCase()
			result = result.filter((i) => i.symbol?.toLowerCase().includes(q))
		}

		if (sortColumn.value) {
			const { key, asc } = sortColumn.value
			result = [...result].sort((a, b) => {
				const inResult = a.result && key in a.result
				let aVal = inResult ? a.result[key]?.value : a[key]
				let bVal = inResult ? b.result?.[key]?.value : b[key]
				if (aVal == null && bVal == null) return 0
				if (aVal == null) return 1
				if (bVal == null) return -1
				if (typeof aVal === "string") {
					aVal = aVal.toLowerCase()
					bVal = (bVal || "").toLowerCase()
				}
				if (aVal < bVal) return asc ? -1 : 1
				if (aVal > bVal) return asc ? 1 : -1
				return 0
			})
		}

		return result
	})

	const symbolCount = computed(() => filteredItems.value.length)

	function onSort(key) {
		if (sortColumn.value?.key === key) {
			if (sortColumn.value.asc) {
				sortColumn.value.asc = false
			} else {
				sortColumn.value = null
			}
		} else {
			sortColumn.value = { key, asc: true }
		}
	}

	function getSortDir(key) {
		if (sortColumn.value?.key !== key) return null
		return sortColumn.value.asc ? "asc" : "desc"
	}

	return { filterQuery, sortColumn, filteredItems, symbolCount, onSort, getSortDir }
}
