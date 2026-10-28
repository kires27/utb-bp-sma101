<script setup>
import { cached } from "~/utils/cache"
import { API } from "#shared/constants/routes"
import { formatCurrency } from "~/utils/formatData"

useHead({ title: "MEIC — Company Profile" })

const route = useRoute()
const symbol = computed(() =>
	(route.params.symbol || "").toString().toUpperCase(),
)

const stockData = ref(null)
const events = ref(null)

watch(symbol, async () => {
	stockData.value = null
	events.value = null

	stockData.value = await cached(
		`fa-profile-${symbol.value}`,
		() => $fetch(API.stocks.get_stock(symbol.value)),
	)
	events.value = await cached(
		`fa-events-${symbol.value}`,
		() => $fetch(API.stocks.get_events(symbol.value)),
	)
}, { immediate: true })

// Group dividends by year, newest first — year subtotal shows trend at a glance
const dividendYears = computed(() => {
	const byYear = new Map()
	for (const d of events.value?.dividends ?? []) {
		const year = d.date.slice(0, 4)
		if (!byYear.has(year)) byYear.set(year, [])
		byYear.get(year).push(d)
	}
	return [...byYear.entries()].map(([year, payments]) => ({
		year,
		payments,
		total: payments.reduce((sum, p) => sum + p.amount, 0),
	}))
})

// Dividends are split-adjusted (today-basis) and can be tiny — e.g. NVDA
// 2012 = 0.001875. formatCurrency's default 2 decimals would show 0.00.
// Show 6 decimals for sub-1 amounts, keep normal 2 for the rest.
const formatDividend = (amount) => {
	if (amount == null || isNaN(amount)) return null
	const a = Number(amount)
	return a >= 1
		? formatCurrency(a, stockData.currency, 2)
		: formatCurrency(a, stockData.currency, 6)
}

const companyInfo = computed(() => [
	{ label: "Full Name", value: stockData.value?.name },
	{ label: "Founded", value: "2003" },
	{ label: "Headquarters", value: stockData.value?.address + ", " + stockData.value?.city },
	{ label: "Employees", value: stockData.value?.employees },
	{ label: "Sector", value: stockData.value?.sector },
	{ label: "Industry", value: stockData.value?.industry },
	{ label: "Exchange", value: stockData.value?.exchange },
	{ label: "Currency", value: stockData.value?.currency },
	{ label: "Fiscal Year End", value: "December" },
	{ label: "Website", value: stockData.value?.website, link: true },
])

const description = computed(() => [stockData.value?.description])

const leadership = computed(() => stockData.value?.key_executives ?? [])

// Cap dividend cell at leadership cell height (grid stretches both otherwise)
const leadershipCell = ref(null)
const dividendMaxHeight = ref(null)

let ro = null
watch(leadershipCell, (el) => {
	ro?.disconnect()
	if (!el) {
		dividendMaxHeight.value = null
		return
	}
	const update = () => {
		dividendMaxHeight.value = el.offsetHeight + "px"
	}
	ro = new ResizeObserver(update)
	ro.observe(el)
	update()
}, { immediate: true, flush: "post" })
onBeforeUnmount(() => ro?.disconnect())

</script>

<template>
	<Container>
		<div v-if="stockData" class="profile-grid">

			<!-- Company Info -->
			<div class="cell">
				<div class="cell-header">
					<Text variant="label">Company Info</Text>
				</div>
				<table class="info-table">
					<tbody>
						<tr v-for="(item, idx) in companyInfo" :key="idx">
							<td><Text variant="body-sm" tone="muted">{{ item.label }}</Text></td>
							<td>
								<a v-if="item.link" :href="item.value" target="_blank" rel="noopener noreferrer">
									<Text variant="body-sm" tone="green" link>{{ item.value }} ↗</Text>
								</a>
								<Text v-else variant="body-sm">{{ item.value }}</Text>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- <img :src="priceGraph" alt="" class="description-cell"> -->

			<!-- Description -->
			<div class="cell description-cell">
				<div class="cell-header">
					<Text variant="label">Description</Text>
				</div>
				<Text v-for="(text, idx) in description" :key="idx" variant="body-sm" tone="muted" class="desc-text">
					{{ text }}
				</Text>
			</div>

			<!-- Leadership -->
			<div ref="leadershipCell" class="cell">
				<div class="cell-header">
					<Text variant="label">Leadership</Text>
				</div>
				<div v-for="person in leadership" :key="person.name" class="person-row">
					<div class="person-avatar">
						<Icon name="material-symbols:person-outline" class="person-avatar-icon" />
					</div>
					<div class="person-info">
						<Text variant="body-sm" weight="medium">{{ person.name }}</Text>
						<Text variant="body-sm" tone="muted">{{ person.title }}</Text>
					</div>
					<Text v-if="person.age" variant="body-sm" tone="muted" class="person-since">age: {{ person.age
					}}</Text>
				</div>
			</div>

			<!-- Dividend History -->
			<div class="cell dividend-cell" :style="{ maxHeight: dividendMaxHeight }">
				<div class="cell-header">
					<Text variant="label">Dividend History</Text>
				</div>
				<template v-if="dividendYears.length">
					<div class="dividend-summary">
						<Text variant="body-sm" tone="muted">
							{{ formatDividend(dividendYears[0].payments[0].amount) }} latest · {{ (events.dividends ?? []).length }} payments since
							{{ dividendYears[dividendYears.length - 1].year }}
						</Text>
					</div>
					<div class="scroll-list">
						<div v-for="y in dividendYears" :key="y.year" class="year-group">
							<div class="year-header">
								<Text variant="body-sm" weight="medium">{{ y.year }}</Text>
								<Text variant="body-sm" tone="muted">
									{{ y.payments.length }} payments · {{ formatDividend(y.total) }}
								</Text>
							</div>
							<div v-for="p in y.payments" :key="p.date" class="payment-row">
								<Text variant="body-sm" tone="muted">{{ p.date }}</Text>
								<Text variant="body-sm">{{ formatDividend(p.amount) }}</Text>
							</div>
						</div>
					</div>
				</template>
				<Text v-else variant="body-sm" tone="muted">No dividend history</Text>
			</div>

			<!-- Stock Splits -->
			<div class="cell">
				<div class="cell-header">
					<Text variant="label">Stock Splits</Text>
				</div>
				<table v-if="events?.splits?.length" class="info-table">
					<tbody>
						<tr v-for="s in events.splits" :key="s.date">
							<td><Text variant="body-sm" weight="medium">{{ s.factor }}:1</Text></td>
							<td><Text variant="body-sm" tone="muted">{{ s.date }}</Text></td>
						</tr>
					</tbody>
				</table>
				<Text v-else variant="body-sm" tone="muted">No stock splits</Text>
			</div>

		</div>
	</Container>
</template>

<style scoped>
/* ── Grid ── */
.profile-grid {
	display: grid;
	grid-template-columns: 1fr 1fr 1fr;
	border-left: 1px solid var(--border);
	border-top: 1px solid var(--border);
	margin-bottom: 2rem;
}

.profile-grid>* {
	border-right: 1px solid var(--border);
	border-bottom: 1px solid var(--border);
}

/* ── Cell ── */
.cell {
	padding: 1.5rem;
	display: flex;
	flex-direction: column;
}

/* ── Description spans 2 columns ── */
.description-cell {
	grid-column: span 2;
}

/* ── Cell header — shared pattern ── */
.cell-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding-bottom: 0.6rem;
	border-bottom: 1px solid var(--border);
	margin-bottom: 1rem;
}

/* ── Info table ── */
.info-table {
	width: 100%;
	border-collapse: collapse;
}

.info-table tr {
	border-bottom: 1px solid var(--border);
	transition: background 0.1s;
}

.info-table tr:last-child {
	border-bottom: none;
}

.info-table tr:hover {
	background: rgba(255, 255, 255, 0.02);
}

.info-table td {
	padding: 0.5rem 0;
	vertical-align: top;
}

.info-table td:first-child {
	color: var(--fg-3);
	width: 45%;
}

.info-table td:last-child {
	text-align: right;
}

/* ── Dividend cell — shrink to content, capped at leadership height (via JS) ── */
.dividend-cell {
	align-self: start;
	max-height: 10rem;
}

/* ── Dividend scroll list ── */
.dividend-summary {
	padding-bottom: 0.6rem;
	border-bottom: 1px solid var(--border);
	margin-bottom: 0.8rem;
}

.scroll-list {
	flex: 1;
	min-height: 20rem;
	overflow-y: auto;
	scrollbar-width: thin;
	scrollbar-color: var(--border-hi) transparent;
}

.year-group {
	margin-bottom: 0.8rem;
}

.year-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0.4rem 0.5rem;
	background: var(--bg-hover);
	position: sticky;
	top: 0;
}

.payment-row {
	display: flex;
	justify-content: space-between;
	padding: 0.35rem 0.5rem 0.35rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

.payment-row:last-child {
	border-bottom: none;
}

/* ── Description ── */
.desc-text {
	margin-bottom: 1rem;
}

.desc-text:last-of-type {
	margin-bottom: 0;
}

/* ── Leadership ── */
.person-row {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	padding: 0.6rem 0;
	border-bottom: 1px solid var(--border);
	transition: background 0.1s;
}

.person-row:last-child {
	border-bottom: none;
}

.person-row:hover {
	background: rgba(255, 255, 255, 0.02);
}

.person-avatar {
	width: 30px;
	height: 30px;
	background: var(--bg-hover);
	border: 1px solid var(--border-hi);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.person-avatar-icon {
	width: 18px;
	height: 18px;
	color: var(--fg-3);
}

.person-info {
	flex: 1;
}

/* ── Responsive ── */
@media (max-width: 900px) {
	.profile-grid {
		grid-template-columns: 1fr;
	}
}
</style>
