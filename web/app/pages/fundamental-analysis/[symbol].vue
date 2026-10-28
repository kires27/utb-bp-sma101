<script setup>
import { Icon } from '@iconify/vue'
import { useLocalStorage } from "@vueuse/core"
import { API, URI } from '#shared/constants/routes'
import { SEARCHBAR_HISTORY_KEY, MAX_SEARCHBAR_HISTORY } from '#shared/constants/variables'
import { redirectWithToast } from "~/utils/toast"
import MenuSlider from '~/features/watchlist/components/MenuSlider.vue'

const route = useRoute()
const symbol = computed(() =>
	(route.params.symbol || "").toString().toUpperCase(),
)

const menuSliderRef = ref(null)
function openWatchlistMenu() {
	menuSliderRef.value?.open()
}

const { data: stockDataRaw, error: stockError } = await useAsyncData(
	() => `stock-header-${symbol.value}`,
	async () => {
		const [basic, metric] = await Promise.all([
			$fetch(API.stocks.get_stock(symbol.value)),
			$fetch(API.stocks.get_metric(symbol.value)),
		])

		return { basic, metric }
	},
	{ watch: [symbol], },
)

let redirected = false
function redirectMissingSymbol() {
	if (redirected) return
	redirected = true
	return redirectWithToast(
		URI.tool.fa,
		`Symbol ${symbol.value} is not available`,
		{ theme: "error" },
	)
}

onMounted(() => {
	if (stockError.value || !stockDataRaw.value?.basic) redirectMissingSymbol()
})

watch(stockError, (err) => {
	if (err) redirectMissingSymbol()
})

const stockData = computed(() => {
	const basic = stockDataRaw.value?.basic ?? {}
	const metric = stockDataRaw.value?.metric ?? {}

	return {
		ticker: basic.symbol ?? symbol.value,
		name: basic.name ?? "",
		price: metric.stock_price ?? "—",
		change: Number(metric.regular_market_change_percent ?? 0).toFixed(2) + "%",
		changeAmount: Number(metric.regular_market_change ?? 0).toFixed(2) + "$",
		positive: Number(metric.regular_market_change ?? 0) >= 0,
		sector: basic.sector ?? "",
		exchange: basic.exchange ?? "",
		currency: metric.currency ?? "USD",
	}
})

// ---- live price freshness (client-only: SSR/hydration quirk per AGENTS.md) ----
const isHydrated = ref(false)
const isStale = computed(() => Boolean(stockDataRaw.value?.metric?.stale))
const updatedAt = ref(null) // Date of last known regular_market_time
const ageLabel = ref("")

function syncUpdatedAt() {
	const ts = stockDataRaw.value?.metric?.regular_market_time
	updatedAt.value = ts ? new Date(ts) : null
	tickAge()
}

function tickAge() {
	if (!updatedAt.value) {
		ageLabel.value = ""
		return
	}
	const s = Math.max(0, Math.round((Date.now() - updatedAt.value.getTime()) / 1000))
	ageLabel.value = s < 60 ? `Updated ${s}s ago` : `Updated ${Math.floor(s / 60)}m ago`
}

const supabase = useSupabaseClient()
const stockId = computed(() => stockDataRaw.value?.basic?.id ?? null)
let heartbeat = null
let ageTicker = null
let channel = null

async function refreshMetric() {
	try {
		const fresh = await $fetch(API.stocks.get_metric(symbol.value))
		if (fresh && !fresh.stale) stockDataRaw.value = { ...stockDataRaw.value, metric: fresh }
		syncUpdatedAt()
	} catch {
		// network hiccup — keep current data, next beat retries
	}
}

onMounted(async () => {
	isHydrated.value = true
	syncUpdatedAt()

	// heartbeat: keeps interest alive + refreshes while user stares at page
	heartbeat = setInterval(refreshMetric, 60_000)
	ageTicker = setInterval(tickAge, 10_000)

	await rekeyChannel()
})

onBeforeUnmount(() => {
	clearInterval(heartbeat)
	clearInterval(ageTicker)
	if (channel) supabase.removeChannel(channel)
})

watch(symbol, () => {
	// symbol changed via searchbar: page meta re-runs useAsyncData; rekey channel
	if (!import.meta.client) return
	if (channel) supabase.removeChannel(channel)
	rekeyChannel()
})

async function rekeyChannel() {
	if (!stockId.value) return
	// realtime push: any poller/other-user refresh lands here without polling
	await supabase.realtime.setAuth()
	channel = supabase
		.channel(`stock-metric-${symbol.value}`)
		.on(
			"postgres_changes",
			{
				event: "UPDATE",
				schema: "public",
				table: "stock_metric",
				filter: `stock_id=eq.${stockId.value}`,
			},
			(payload) => {
				stockDataRaw.value = {
					...stockDataRaw.value,
					metric: { ...stockDataRaw.value?.metric, ...payload.new },
				}
				syncUpdatedAt()
			}
		)
		.subscribe()
}

// history
const history = useLocalStorage(SEARCHBAR_HISTORY_KEY, [])

function onSelect(newSymbol) {
	pushHistory(newSymbol)
	const segments = route.path.split('/').filter(Boolean)
	const currentTab = segments[segments.length - 1] || 'financials'
	navigateTo(`${URI.tool.fa}/${newSymbol}/${currentTab}`)
}

function pushHistory(symbol) {
	history.value = [symbol, ...history.value.filter((s) => s !== symbol)].slice(0, MAX_SEARCHBAR_HISTORY)
}
</script>

<template>
	<Container >
		<div class="shell-search">
			<Section width="md">
				<Searchbar @select="onSelect" />
			</Section>
		</div>

		<Section width="lg">
			<div class="stock-hero">
				<TickerSymbol :title="stockData.ticker" :size="44" />
				<div class="stock-name-block">
					<Text variant="h3" weight="medium">{{ symbol }}</Text>
					<Text variant="label" tone="muted">
						{{ stockData.name }}&nbsp;·&nbsp;{{
							stockData.exchange
						}}&nbsp;·&nbsp;{{ stockData.currency }}
					</Text>
				</div>
				<div class="stock-price-block">
					<Text variant="h3" weight="bold">{{ stockData.price }}</Text>
					<Text variant="body-sm" :tone="stockData.positive ? 'green' : 'red'">
						{{ stockData.positive ? "▲" : "▼" }}
						{{ stockData.changeAmount }}
						({{ stockData.change }})
					</Text>
					<Text v-if="isHydrated" variant="label" :tone="isStale ? 'red' : 'muted'">
						<template v-if="isStale">⚠ stale</template>
						<template v-else-if="ageLabel">{{ ageLabel }}</template>
					</Text>
				</div>
				<Button variant="primary" size="sm" alt="add to watchlist" @click="openWatchlistMenu">
					<Icon icon="material-symbols:playlist-add" width="22" height="22" />
				</Button>
			</div>

			<div class="tab-bar">
				<NuxtLink :to="URI.tool.fa_financials(symbol)" active-class="tab-active">
					<Button :border="false">

						<Text variant="body" weight="bold" link>
							Financials
						</Text>
					</Button>

				</NuxtLink>
				<NuxtLink :to="URI.tool.fa_iv(symbol)" active-class="tab-active">
					<Button :border="false">

						<Text variant="body" weight="bold" link>
							Intrinsic Value
						</Text>
					</Button>

				</NuxtLink>
				<NuxtLink :to="URI.tool.fa_stock_profile(symbol)" active-class="tab-active">
					<Button :border="false">
						<Text variant="body" weight="bold" link>
							Profile
						</Text>
					</Button>
				</NuxtLink>
			</div>

			<NuxtPage keepalive />

			<MenuSlider ref="menuSliderRef" :symbol="symbol" />
		</Section>
	</Container>
	<Footer :full-mode="false"></Footer>
</template>

<style scoped>
.shell-search {
	border-bottom: 1px solid var(--border);
	/* background: var(--bg-2); */
	padding: 1rem 0;
	width: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.stock-hero {
	display: flex;
	align-items: stretch;
	gap: 1.5rem;
	padding: 1.5rem 0;
	border-bottom: 1px solid var(--border);
}

.stock-logo {
	width: 44px;
	height: 44px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 16px;
	font-weight: 700;
	color: white;
	flex-shrink: 0;
	background: var(--rose);
}

.stock-name-block {
	flex: 1;
}



.stock-meta {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.market-status {
	display: flex;
	align-items: center;
	gap: 0.4rem;
	font-size: 10px;
	color: var(--teal);
}

.stock-price-block {
	text-align: right;
}

.stock-change {
	margin-top: 0.25rem;
}

.stock-change.pos {
	color: var(--teal);
}

.stock-change.neg {
	color: var(--rose);
}

.tab-bar {
	display: flex;
	align-items: center;
	padding: 1rem 0;
	/* gap: 2rem; */
}

.tab-active :deep(.text) {
	color: var(--teal);
	font-weight: bold;
}
</style>
