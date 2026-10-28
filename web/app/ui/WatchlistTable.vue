<script setup>
import { computed, ref } from "vue"
import { WATCHLIST_SHAPE } from "#shared/logic/watchlist-shape"
import { snakeCaseToNormal, titleCase } from "#shared/functions/formatters"
import { URI } from "#shared/constants/routes"
import { styleMedianSignal } from "#shared/functions/formatters"
import WatchlistSkeleton from "~/features/watchlist/components/Skeleton.vue"

const router = useRouter()

const props = defineProps({
	wl: Object,
	readonly: Boolean,
})

const items = computed(() => props.wl?.items ?? [])

const hoveredSymbol = ref(null)
function onHoverIn(symbol) { hoveredSymbol.value = symbol }
function onHoverOut() { hoveredSymbol.value = null }

const columns = Object.keys(WATCHLIST_SHAPE)

const groupHeaders = computed(() => {
	const headers = []
	for (const key of columns) {
		const group = WATCHLIST_SHAPE[key].group
		const last = headers[headers.length - 1]
		if (last && last.group === group) {
			last.colspan++
		} else {
			headers.push({ group, label: group ? titleCase(group) : "", colspan: 1 })
		}
	}
	return headers
})

function isGroupStart(key) {
	return !!WATCHLIST_SHAPE[key]?.groupStart
}

function formatCell(key, item) {
	const shape = WATCHLIST_SHAPE[key]
	const inResult = item.result && key in item.result
	const v = inResult ? item.result[key]?.value : item[key]
	const median = inResult ? item.result[key]?.median ?? null : null

	if (v == null) return `<span class="f-na">—</span>`

	const cls = styleMedianSignal(v, median, shape?.valueAboveMedianIsGood)

	let text
	if (shape?.isPercentage && typeof v === "number") {
		text = `${(v * 100).toFixed(1)}%`
	} else if (typeof v === "number") {
		text = v.toLocaleString("en-US", { maximumFractionDigits: 2 })
	} else {
		text = `${v}`
	}

	return `<span class="${cls}">${text}</span>`
}	
</script>

<template>
	<div class="table-wrap">
		<table>
			<thead>
				<tr class="tr-groups">
					<th class="th-group th-index" colspan="1"></th>
					<th v-for="(header, i) in groupHeaders" :key="i" class="th-group" :colspan="header.colspan">
						<Text variant="label" tone="muted">{{ header.label }}</Text>
					</th>
				</tr>
				<tr class="tr-cols">
					<th class="th-index col-first" @click.stop>
						<Text variant="label">#</Text>
					</th>
					<th v-for="key in columns" :key="key"
						:class="{ 'col-first': isGroupStart(key), sorted: wl.getSortDir(key) }" @click="wl.onSort(key)">
						<Text variant="label">{{ snakeCaseToNormal(key) }}</Text>
						<span class="sort-indicator" v-if="wl.getSortDir(key)">
							{{ wl.getSortDir(key) === "asc" ? "↓" : "↑" }}
						</span>
					</th>
				</tr>
			</thead>
			<tbody v-if="wl.itemsPending">
				<WatchlistSkeleton v-for="r in 6" :key="r" :columns="columns" :row-index="r - 1" />
			</tbody>
			<tbody v-else-if="items.length">
				<tr v-for="(item, index) in items" :key="item.symbol || Math.random()"
					@mouseleave="!readonly && onHoverOut()">
					<td class="td-index" @mouseenter="!readonly && onHoverIn(item.symbol)">
						<div class="td-index-inner">
							<button v-if="!readonly && hoveredSymbol === item.symbol" class="row-action-btn"
								@click.stop="wl.removeStock(item.symbol)">✕</button>
							<Text v-else variant="label" tone="muted">{{ index + 1 }}</Text>
						</div>
					</td>
					<td v-for="key in columns" :key="key" class="td-val" :class="{ 'g-start': isGroupStart(key) }"
						@mouseenter="!readonly && key === 'symbol' && onHoverIn(item.symbol)">
						<template v-if="key === 'symbol'">
							<div class="ticker-cell" @click.stop="router.push(URI.tool.fa_financials(item.symbol))">
								<Text variant="label">{{ item.symbol }}</Text>
							</div>
						</template>
						<Text v-else variant="body-sm" weight="medium" v-html="formatCell(key, item)" />
					</td>
				</tr>
			</tbody>
			<tbody v-else>
				<tr>
					<td :colspan="columns.length + 1" class="empty-row">
						<Text variant="label" tone="muted">No stocks in the watchlist</Text>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<style scoped>
.table-wrap {
	--cell-padding-x: 0.6rem;
	--cell-padding-y: 0.35rem;
	overflow-x: auto;
	overflow-y: auto;
	scrollbar-gutter: stable;
}

table {
	width: 100%;
	border-collapse: collapse;
	min-width: 1100px;
}

/* ── Index column ── */
.th-index,
.td-index {
	width: 2.2rem;
	min-width: 2.2rem;
	max-width: 2.2rem;
}

.td-index {
	padding: 0;
	text-align: center;
	vertical-align: middle;
}

.th-index {
	padding: var(--cell-padding-y) var(--cell-padding-x);
}

.td-index-inner {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	padding: var(--cell-padding-y) var(--cell-padding-x);
}

.td-index-inner:has(.row-action-btn) {
	cursor: pointer;
}

.row-action-btn {
	border: none;
	background: none;
	color: var(--rose);
	cursor: pointer;
	padding: 0;
	font-size: 14px;
	line-height: 1;
}

/* ── Group header row ── */
.tr-groups {
	background: var(--bg-2);
}

.th-group {
	text-align: center;
	padding: var(--cell-padding-y) var(--cell-padding-x);
	white-space: nowrap;
	border-left: 1px solid var(--border-hi);
	border-bottom: 1px solid var(--border-hi);
}

/* ── Column label row ── */
.tr-cols {
	background: var(--bg-2);
}

.tr-cols th {
	position: relative;
	padding: var(--cell-padding-y) var(--cell-padding-x);
	text-align: center;
	cursor: pointer;
	user-select: none;
	border-bottom: 1px solid var(--border);
}

.tr-cols th :deep(.text--label) {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.tr-cols th:hover :deep(.text--label) {
	color: var(--blue);
}

.tr-cols th.sorted :deep(.text--label) {
	color: var(--blue);
}

.col-first {
	border-left: 1px solid var(--border-hi);
}

.sort-indicator {
	position: absolute;
	right: 0.25rem;
	top: 50%;
	transform: translateY(-50%);
	font-size: 10px;
	line-height: 1;
	color: var(--blue);
}

/* ── Body ── */
tbody tr {
	border-bottom: 1px solid var(--border);
	cursor: default;
	animation: rowIn 0.2s ease backwards;
}

tbody tr:last-child {
	border-bottom: none;
}

tbody tr:nth-child(1) {
	animation-delay: 0.02s;
}

tbody tr:nth-child(2) {
	animation-delay: 0.04s;
}

tbody tr:nth-child(3) {
	animation-delay: 0.06s;
}

tbody tr:nth-child(4) {
	animation-delay: 0.08s;
}

tbody tr:nth-child(5) {
	animation-delay: 0.10s;
}

tbody tr:nth-child(6) {
	animation-delay: 0.12s;
}

tbody tr:nth-child(7) {
	animation-delay: 0.14s;
}

tbody tr:nth-child(8) {
	animation-delay: 0.16s;
}

tbody tr:nth-child(9) {
	animation-delay: 0.18s;
}

tbody tr:hover {
	background: var(--bg-hover);
	transition: background 0.15s ease;
}

@keyframes rowIn {
	from {
		opacity: 0;
		transform: translateY(3px);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}



/* ── Cells ── */
td {
	padding: var(--cell-padding-y) var(--cell-padding-x);
	vertical-align: middle;
	white-space: nowrap;
	text-align: center;
	font-variant-numeric: tabular-nums;
}

td :deep(.text--body-sm) {
	display: inline-block;
}



.g-start {
	border-left: 1px solid var(--border);
}

/* ── Symbol / ticker cell ── */
.ticker-cell {
	cursor: pointer;
	text-align: right;
}

/* ── Formatting helpers ── */
.f-na {
	color: var(--fg-3);
}

:deep(.val-pos) {
	color: var(--teal);
}

:deep(.val-neg) {
	color: var(--rose);
}

:deep(.val-close) {
	color: var(--gold);
}

:deep(.val-empty) {
	color: var(--fg);
}

.f-unit {
	font-size: 8.5px;
	color: var(--fg-3);
}

/* ── States ── */
.empty-row {
	text-align: center;
	padding: 3rem 0;
}


</style>
