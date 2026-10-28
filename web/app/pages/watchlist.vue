<script setup>
import { ref, reactive, onMounted } from "vue"
import { API } from "#shared/constants/routes"
import { cached, invalidate } from "~/utils/cache"
import { useWatchlist } from "~/features/watchlist/provider"
import { useWatchlistView } from "~/features/watchlist/functions/composable"
import WatchlistSwitcher from "~/features/watchlist/components/WatchlistSwitcher.vue"
import WatchlistMenu from "~/features/watchlist/components/WatchlistMenu.vue"
import AddStockModal from "~/features/watchlist/components/AddStockModal.vue"
import WatchlistCreateModal from "~/features/watchlist/components/WatchlistCreateModal.vue"

useHead({ title: "MEIC — Watchlist" })

const watchlist = useWatchlist()

// ── State ──
const watchlists = ref([])
const selectedId = ref(null)
const items = ref([])
const detailedItems = ref([])
const itemsPending = ref(true)
const showAddModal = ref(false)
const showCreateModal = ref(false)
const modalMode = ref("create")

// ── View (filter/sort) ──
const { filterQuery, filteredItems, symbolCount, onSort, getSortDir } = useWatchlistView(detailedItems)

// ── Data fetching ──
async function fetchWatchlists() {
	try {
		watchlists.value = await cached("wl-list", () => watchlist.list())
	} catch {
		watchlists.value = []
	}

	if (watchlists.value.length && !watchlists.value.some((item) => String(item.id) === String(selectedId.value))) {
		selectedId.value = watchlists.value[0].id
	} else if (!watchlists.value.length) {
		selectedId.value = null
		itemsPending.value = false
	}
}

async function fetchItems() {
	if (!selectedId.value) {
		items.value = []
		return
	}

	try {
		items.value = await cached(`wl-items-${selectedId.value}`, () =>
			watchlist.items(selectedId.value),
		)
	} catch {
		items.value = []
	}
}

async function fetchDetailedItems() {
	if (!selectedId.value) return
	detailedItems.value = await cached(`wl-detailed-${selectedId.value}`, () =>
		watchlist.getDetailedItems(selectedId.value),
	)
}

async function loadWatchlistData() {
	itemsPending.value = true
	await fetchItems()
	await fetchDetailedItems()
	itemsPending.value = false
}

// ── Actions ──
async function addStockToWatchlist(symbol) {
	const upperSymbol = symbol.toUpperCase()
	if (!selectedId.value) return
	if (items.value.some((s) => s.toUpperCase() === upperSymbol)) return

	await watchlist.addItem(selectedId.value, upperSymbol)

	items.value = [...items.value, upperSymbol]

	invalidate(`wl-items-${selectedId.value}`)
	invalidate(`wl-detailed-${selectedId.value}`)

	try {
		const { results: [details] } = await $fetch(API.watchlist.get_watchlist([upperSymbol]))
		detailedItems.value = [...detailedItems.value, details]
	} catch {
		detailedItems.value = [...detailedItems.value, {
			symbol: upperSymbol,
			stock_price: null,
			quality_score: null,
			maintenance_update: null,
			result: {},
		}]
	}
}

async function selectWatchlistById(id) {
	selectedId.value = id
	await loadWatchlistData()
}

async function createWatchlist(name) {
	if (!name?.trim()) return

	const created = await watchlist.create(name.trim())
	selectedId.value = created?.id || null
	invalidate("wl-list")
	await fetchWatchlists()
	if (selectedId.value) {
		await loadWatchlistData()
	}
}

function openCreateModal() {
	modalMode.value = "create"
	showCreateModal.value = true
}

function openRenameModal() {
	modalMode.value = "rename"
	showCreateModal.value = true
}

async function submitCreateWatchlist(name) {
	if (!name?.trim()) return
	showCreateModal.value = false
	if (modalMode.value === "create") {
		await createWatchlist(name)
	} else {
		await watchlist.rename(selectedId.value, name)
		invalidate("wl-list")
		await fetchWatchlists()
	}
}

async function removeWatchlist() {
	if (!selectedId.value) return

	await watchlist.delete(selectedId.value)

	watchlists.value = watchlists.value.filter((w) => String(w.id) !== String(selectedId.value))
	invalidate("wl-list")

	const next = watchlists.value[0]?.id || null
	selectedId.value = next

	if (next) {
		invalidate(`wl-items-${next}`)
		invalidate(`wl-detailed-${next}`)
		await loadWatchlistData()
	} else {
		items.value = []
		detailedItems.value = []
		itemsPending.value = false
	}
}

async function removeStock(symbol) {
	if (!selectedId.value) return

	await watchlist.removeItem(selectedId.value, symbol)

	items.value = items.value.filter((s) => s.toUpperCase() !== symbol.toUpperCase())
	detailedItems.value = detailedItems.value.filter((i) => i.symbol?.toUpperCase() !== symbol.toUpperCase())

	invalidate(`wl-items-${selectedId.value}`)
	invalidate(`wl-detailed-${selectedId.value}`)
}

// ── Init ──
onMounted(async () => {
	await fetchWatchlists()
	if (selectedId.value) {
		await loadWatchlistData()
	}
})

// ── Table bundle ──
const wl = reactive({
	itemsPending,
	items: filteredItems,
	getSortDir,
	onSort,
	removeStock,
})
</script>

<template>
	<div class="page">
		<div class="toolbar">
			<div class="toolbar-left">
				<WatchlistSwitcher
					:watchlists
					:selected-id="selectedId"
					@select="selectWatchlistById"
					@create="openCreateModal"
				/>

				<Text variant="label" tone="muted" class="wl-sym-count">{{ symbolCount }} stocks</Text>
			</div>

			<div class="toolbar-right">
				<Input placeholder="Filter stocks..." v-model="filterQuery" has-icon>
					<template #icon>
						<Icon name="material-symbols:search" width="16" />
					</template>
				</Input>

				<button class="icon-btn" style="color: var(--teal);" @click="showAddModal = true">
					<Icon name="material-symbols:add" size="32"/>
				</button>

				<WatchlistMenu
					@create="openCreateModal"
					@rename="openRenameModal"
					@remove="removeWatchlist"
				/>
			</div>
		</div>

		<WatchlistTable :wl="wl" />

		<AddStockModal
			:open="showAddModal"
			:items
			@close="showAddModal = false"
			@add="addStockToWatchlist"
		/>

		<WatchlistCreateModal
			:open="showCreateModal"
			:mode="modalMode"
			:watchlists
			:selected-id="selectedId"
			@close="showCreateModal = false"
			@submit="submitCreateWatchlist"
		/>
	</div>
</template>

<style scoped>
.page {
	display: flex;
	flex-direction: column;
	flex: 1;
}

.toolbar {
	border-bottom: 1px solid var(--border);
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 2rem;
	height: 52px;
	flex-shrink: 0;
	position: relative;
}

.toolbar-left {
	display: flex;
	align-items: center;
	gap: 1.25rem;
}

.toolbar-right {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.wl-sym-count {
	border-left: 1px solid var(--border);
	padding-left: 1rem;
}

.icon-btn {
	background: none;
	border: none;
	padding: 0;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	height: 33px;
}

.icon-btn:hover {
	filter: brightness(1.2);
	background-color: var(--bg-hover);
}
</style>
