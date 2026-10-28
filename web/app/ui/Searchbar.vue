<script setup>
import { ref, computed, onBeforeUnmount } from "vue"
import { onClickOutside } from "@vueuse/core"

const DEBOUNCE_MS = 300

const search = ref("")
const results = ref([])
const focused = ref(false)
const loading = ref(false)

let debounceTimer
const wrapRef = ref(null)

const props = defineProps({
	placeholder: {
		type: String,
		default: "Search stocks...",
	},
})

const emit = defineEmits(["select"])

onClickOutside(wrapRef, () => { focused.value = false })
onBeforeUnmount(() => clearTimeout(debounceTimer))

function handleInput() {
	clearTimeout(debounceTimer)
	const q = search.value.trim()
	if (q.length < 2) {
		results.value = []
		return
	}
	debounceTimer = setTimeout(async () => {
		loading.value = true
		try {
			const data = await $fetch(`/api/stock/search/${q}`)
			results.value = data ?? []
		} catch {
			results.value = []
		} finally {
			loading.value = false
		}
	}, DEBOUNCE_MS)
}

function select(symbol, { clearSearch = false } = {}) {
	emit("select", symbol)
	focused.value = false
	if (clearSearch) {
		search.value = ""
		results.value = []
	}
}

const showResults = computed(
	() =>
		focused.value &&
		search.value.trim().length >= 2 &&
		(results.value.length > 0 || loading.value),
)
</script>

<template>
	<div class="searchbar-wrap" ref="wrapRef">
		<Input v-model="search" type="text" :placeholder="placeholder" has-icon has-button
			autocomplete="off"
			@update:model-value="handleInput"
			@focus="focused = true">
			<template #icon>
				<Icon name="material-symbols:search" />
			</template>
			<template #status>
				<Text v-if="loading" variant="label">loading...</Text>
				<Text v-else-if="search.length >= 2 && results.length === 0" variant="label">nothing found.</Text>
			</template>
		</Input>
		
		<div v-if="showResults" class="searchbar-dropdown">
			<button v-for="item in results" :key="item.symbol" class="dropdown-item"
				@click="select(item.symbol, { clearSearch: true })">
				<TickerSymbol :title="item.symbol" :size="24" />
				<Text variant="body">{{ item.symbol }}</Text>
				<Text variant="label">{{ item.name }}</Text>
				<Text variant="label" tone="muted">{{ item.exchange }}</Text>

				<slot name="menuAction" :item="item" />
			</button>
		</div>
	</div>
</template>

<style scoped>
.searchbar-wrap {
	position: relative;
	width: 100%;
}

.searchbar-dropdown {
	position: absolute;
	top: calc(100% + 2px);
	left: 0;
	right: 0;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	z-index: 100;
}


.dropdown-item {
	display: grid;
	grid-template-columns: 24px minmax(60px, auto) 1fr auto auto;
	align-items: center;
	gap: 0.7rem;
	padding: 0.6rem 0.85rem;
	background: none;
	border: none;
	border-bottom: 1px solid var(--border);
	cursor: pointer;
	text-align: left;
	width: 100%;
	transition: background 0.1s;
}

.dropdown-item:last-of-type {
	border-bottom: none;
}

.dropdown-item:hover {
	background: var(--bg-hover);
}

.item-icon {
	color: var(--fg-3);
	width: 14px;
	height: 14px;
	flex-shrink: 0;
}

.dropdown-footer {
	padding: 0.5rem 0.85rem;
	border-top: 1px solid var(--border);
	display: flex;
	justify-content: flex-end;
}
</style>
