<script setup>
import { ref, watch } from 'vue'
import { API, URI } from '#shared/constants/routes'

const PAGE_SIZE = 20
const search = ref('')
const results = ref([])
const offset = ref(0)
const hasMore = ref(false)
const loadingMore = ref(false)
const initialResults = ref([])
let debounceTimer

const { data: initial } = await useAsyncData('list-of-symbols', () =>
	$fetch(API.stocks.list(0))
)

const initialData = initial.value
results.value = initialData || []
initialResults.value = initialData || []
hasMore.value = initialData && initialData.length === PAGE_SIZE

async function fetchStocks(reset = false) {
	if (reset) {
		offset.value = 0
		results.value = []
		hasMore.value = false
	}

	loadingMore.value = true

	try {
		const q = search.value.trim()

		const data = await $fetch(API.stocks.list(offset.value), {
			query: { q: q }
		})

		if (reset) {
			results.value = data || []
		} else {
			results.value = [...results.value, ...(data || [])]
		}

		hasMore.value = data && data.length === PAGE_SIZE
	} catch (e) {
		console.error(e)
	} finally {
		loadingMore.value = false
	}
}

watch(search, () => {
	clearTimeout(debounceTimer)
	const len = search.value.trim().length
	if (len === 0) {
		results.value = [...initialResults.value]
		offset.value = 0
		hasMore.value = initialResults.value.length === PAGE_SIZE
	} else if (len >= 2) {
		debounceTimer = setTimeout(() => fetchStocks(true), 300)
	}
})

function loadMore() {
	offset.value += PAGE_SIZE
	fetchStocks(false)
}
</script>

<template>
	<Container>
		<Section width="md" topMargin="md" bottomMargin="md">
			<Text variant="h3">
				Available Stocks
			</Text>
			<br />
			<Input v-model="search" placeholder="Search by symbol or name..." />

			<br>
			<Grid :cols="1" :bordered="false">
				<div v-if="results.length > 0">
					<Text variant="label">Tickers: {{ results.length }}</Text>
					<div class="table-row table-header">
						<Text variant="body">#</Text>
						<Text variant="body">Icon</Text>
						<Text variant="body">Symbols</Text>
						<Text variant="body">Name</Text>
					</div>

					<NuxtLink v-for="(stock, index) in results" :key="stock.symbol" :to="URI.tool.fa_financials(stock.symbol)" class="table-row">
						<Text variant="label" class="col-num">{{ index + 1 }}</Text>
						<span class="col-icon">
							<TickerSymbol :title="stock.symbol" :size="28" />
						</span>
						<span class="col-symbol">{{ stock.symbol }}</span>
						<span class="col-name">{{ stock.name }}</span>
					</NuxtLink>
				</div>

				<div v-else-if="!loadingMore && search.trim().length >= 2">
					<Text variant="body">No stocks matching "{{ search }}"</Text>
				</div>

				<div v-if="loadingMore && results.length === 0">
					<Text variant="body">Loading...</Text>
				</div>
			</Grid>

			<br />
			<Button variant="primary" :wide="true" v-if="hasMore" :disabled="loadingMore" @click="loadMore">
				{{ loadingMore ? 'Loading...' : 'Load more' }}
			</Button>
		</Section>

	</Container>
	<Footer></Footer>
</template>

<style scoped>
.table-row {
	display: grid;
	grid-template-columns: 48px 44px 120px 1fr;
	align-items: center;
	padding: 0.6rem 1rem;
}

.table-header {
	background: var(--bg-2);
}

a.table-row {
	color: inherit;
	text-decoration: none;
	cursor: pointer;
}

.table-row:not(.table-header):hover {
	background: var(--bg-hover);
}
</style>
