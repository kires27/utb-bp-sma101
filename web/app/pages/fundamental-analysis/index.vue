<script setup>
import { ref, watch } from "vue"
import { useLocalStorage } from "@vueuse/core"
import { API, URI } from "#shared/constants/routes"
import { SEARCHBAR_HISTORY_KEY, MAX_SEARCHBAR_HISTORY } from '#shared/constants/variables'
import { cached } from "~/utils/cache"

const history = useLocalStorage(SEARCHBAR_HISTORY_KEY, [])
const historyData = ref([])
const historyLoading = ref(false)

async function fetchHistoryData() {
	if (history.value.length === 0) {
		historyData.value = []
		return
	}
	historyLoading.value = true
	try {
		const cacheKey = `search-history:${[...history.value].sort().join(',')}`
		const { results } = await cached(cacheKey, () => $fetch(API.stocks.get_search_history(history.value)))
		historyData.value = results
	} catch {
		historyData.value = history.value.map(sym => ({ symbol: sym, name: sym, price: null }))
	} finally {
		historyLoading.value = false
	}
}

watch(history, fetchHistoryData, { immediate: true })

function pushHistory(symbol) {
	history.value = [symbol, ...history.value.filter((s) => s !== symbol)].slice(0, MAX_SEARCHBAR_HISTORY)
}

function clearHistory() {
	history.value = []
}

function onSelect(symbol) {
	pushHistory(symbol)
	navigateTo(URI.tool.fa_financials(symbol))
}
</script>

<template>
	<Container hAlign="center">
		<Section width="md" topMargin="lg" bottomMargin="lg">
			<Text variant="h3">Research a stock</Text>
			<Text variant="label">
				Search by ticker symbol or company name to view
				financials, intrinsic value, and profile data.
			</Text>

			<Searchbar @select="onSelect" style="margin: 1rem 0 2rem 0;" />

			<div v-if="historyData.length">
				<div class="recent-header">
					<Text variant="label">Recent Symbols</Text>
					<Button size="sm" @click="clearHistory">Clear</Button>
				</div>

				<div v-if="historyLoading"><Text variant="label">Loading...</Text></div>
				<!-- <div v-else class="recent-grid"> -->
				<Grid v-else :cols="3" gap="sm">
					<NuxtLink v-for="item in historyData" :key="item.symbol" :to="URI.tool.fa_financials(item.symbol)">
						<CardBasic :title="item.symbol"
							:description="`${item.name}${item.price != null ? ' · $' + Number(item.price).toFixed(2) : ''}`" />
					</NuxtLink>
				</Grid>
				<!-- </div> -->
			</div>
		</Section>
	</Container>
	<Footer :full-mode="false"></Footer>
</template>

<style scoped>
.recent-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 1rem;
}

.recent-grid {
	display: grid;
	grid-auto-flow: column;
	grid-auto-columns: min-content;
	gap: 0.75rem;
}
</style>
