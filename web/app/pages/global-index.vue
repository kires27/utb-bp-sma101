<script setup>
import { ref, reactive, onMounted } from "vue"
import { API } from "#shared/constants/routes"
import { cached, invalidatePrefix } from "~/utils/cache"

useHead({ title: "MEIC — Global Index" })

const stocks = ref([])
const offset = ref(0)
const loading = ref(false)
const hasMore = ref(true)

async function loadStocks(reset = false) {
	if (reset) {
		stocks.value = []
		offset.value = 0
		invalidatePrefix("gi-")
	}
	loading.value = true
	try {
		const data = await cached(`gi-${offset.value}`, () =>
			$fetch(API.stocks.global_index(offset.value)),
		)
		stocks.value.push(...data)
		hasMore.value = data.length === 20
	} catch {
		// keep current data on error
	}
	loading.value = false
}

function loadMore() {
	offset.value += 20
	loadStocks()
}

onMounted(() => loadStocks())

const wl = reactive({
	itemsPending: loading,
	items: stocks,
	getSortDir: () => null,
	onSort: () => {},
	removeStock: null,
})
</script>

<template>
	<Container max-width="100vw">
		<WatchlistTable :wl="wl" readonly />

		<div class="button-section">
			<Button
				v-if="hasMore"
				variant="primary"
				:wide="true"
				:disabled="loading"
				@click="loadMore"
			>
				{{ loading ? "Loading..." : "Load more" }}
			</Button>
		</div>
	</Container>
</template>

<style scoped>
.button-section {
	padding: 1rem;
	max-width: 500px;
	margin: auto;
}
</style>
