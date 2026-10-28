<script setup>
import { cached } from "~/utils/cache"
import {
	convertToDate,
} from "~/utils/formatData.js"
import { snakeCaseToNormal } from "#shared/functions/formatters"
import { roundAnyNumber } from "#shared/functions/numeric"
import { styleMedianSignal } from "#shared/functions/formatters"
import { API } from "#shared/constants/routes"
import graph from "~/assets/placeholders/financials-graph.png"

const route = useRoute()
const symbol = computed(() =>
	(route.params.symbol || "").toString().toUpperCase(),
)

useHead(() => ({ title: symbol.value + " - Financials" }))

const analysis = ref(null)
const pending = ref(true)
const error = ref(null)

watch(symbol, async () => {
	pending.value = true
	error.value = null
	analysis.value = null

	try {
		analysis.value = await cached(
			`fa-financials-${symbol.value}`,
			() => $fetch(API.stocks.get_financials(symbol.value)),
		)
		
		console.log("maintenance_update:", analysis.value?.maintenance_update)
	} catch (e) {
		error.value = e
	} finally {
		pending.value = false
	}
}, { immediate: true })

function formatMetricValue(key, raw) {
	if (raw === null || raw === undefined) return "Nan"
	if (analysis.value?.result?.[key]?.isPercentage) {
		return `${roundAnyNumber(raw, 2)}%`
	}
	return roundAnyNumber(raw)
}

function formatMedianComparison(val) {
	if (val == null) return "—"
	const pct = (val * 100).toFixed(1)
	return pct > 0 ? `+${pct}%` : `${pct}%`
}
</script>

<template>
	<div class="content">
		<!-- Left Panel -->
		<div class="left-panel">
			<!-- <div class="panel-header">
				<Text variant="label" class="update-tag">
					{{ convertToDate(analysis?.maintenance_update) ?? "" }}
				</Text>
			</div> -->

			<div v-if="pending" class="state-msg">
				<Text variant="body">Loading...</Text>
			</div>
			<div v-else-if="error" class="state-msg state-error">
				<Text variant="body">Error: {{ error.message }}</Text>
			</div>

			<div v-else-if="analysis?.result" class="metrics-cols">
				<div v-for="groupKey in analysis.groups" :key="groupKey" class="metrics-group">
					<Text variant="label" tone="muted">{{ groupKey }}</Text>
					<hr>

					<template v-for="(val, key) in analysis.result" :key="key">
						<div v-if="val.group === groupKey" class="metric-row">
							<Text variant="body-sm">{{ snakeCaseToNormal(key) }}</Text>
							<Text variant="body-sm" weight="medium"
								:class="styleMedianSignal(val.value, val.median, val.valueAboveMedianIsGood)">
								{{ formatMetricValue(key, val.value) }}
							</Text>
							<Text variant="body-sm" tone="purple">
								{{ formatMetricValue(key, val.median).toString() || '—' }}
							</Text>
						</div>
					</template>
				</div>
			</div>
		</div>

		<!-- Right Panel -->
		<div class="right-panel">
			<div class="quality-block">
				<div>
					<Text variant="label" tone="muted">Financial Quality Score</Text>
					<hr>
				</div>

				<div class="score-cards">
					<div :class="['score-bubble', (analysis?.median_comparison ?? 0) > 0 ? 'sc--pos' : 'sc--neg']">
						<Text variant="h2" class="sc-val">{{ analysis?.quality_score ?? "—" }}</Text>
						<Text variant="body-sm" tone="muted">Score</Text>
					</div>
					<div :class="['score-bubble', (analysis?.median_comparison ?? 0) > 0 ? 'sc--pos' : 'sc--neg']">
						<Text variant="h2" class="sc-val">{{ formatMedianComparison(analysis?.median_comparison) }}</Text>
						<Text variant="body-sm" tone="muted">Higher than average</Text>
					</div>
				</div>

				<ChartSingleBar :value="analysis?.quality_score ?? 0" :fillAnimation="true" :duration="900"
					:thickness="5">
				</ChartSingleBar>
			</div>

			<!-- GRAPH -->
			<div>
				<img :src="graph" alt="graph">
			</div>
		</div>
	</div>
</template>

<style scoped>
.content {
	display: grid;
	grid-template-columns: 2fr 1fr;
}

/* ── Layout ── */
.left-panel {
	/* border-right: 1px solid var(--border); */
	padding: 1.5rem;
}

.right-panel {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
}
.right-panel > div:last-child {
  flex: 1;
  display: flex;
}

img {
  width: 100%;
  height: 100%;
    object-fit:fill;

}

/* ── Panel header — shared pattern ── */
.panel-header {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	padding-bottom: 0.6rem;
	border-bottom: 1px solid var(--border);
	margin-bottom: 1.25rem;
}

.update-tag {
	font-size: 10px;
	letter-spacing: 0.06em;
	color: var(--fg-3);
	font-family: var(--font-main);
}

/* ── State messages ── */
.state-msg {
	padding: 2rem 0;
	font-size: 11px;
	letter-spacing: 0.06em;
	color: var(--fg-3);
	font-family: var(--font-main);
}

.state-error {
	color: var(--rose);
}

/* ── Metrics grid ── */
.metrics-cols {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0 2rem;
}

.metrics-group {
	margin-bottom: 1.5rem;
}

hr {
	border: none;
	height: 1px;
	background-color: var(--border);
}


.metric-row {
	display: grid;
	grid-template-columns: 3fr 1fr 1fr;
	gap: 12px;
	align-items: center;
	padding: 0.38rem 0.4rem;
	transition: background 0.1s;
}

.metric-row:hover {
	background: var(--bg-hover);
}

.val-pos {
	color: var(--teal);
}

.val-neg {
	color: var(--rose);
}

.val-empty {
	color: var(--fg-3);
}

.val-close {
	color: var(--gold);
}


/* ── Quality block ── */
.quality-block {
	padding: 1.5rem;
	border-bottom: 1px solid var(--border);
}

.score-cards {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 0.6rem;
	margin: 1rem 0;
}

.score-bubble {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 1rem;
	gap: 0.5rem;
}

.sc--pos {
	border-color: var(--teal);
}

.sc--neg {
	border-color: var(--rose);
}



/* ── Responsive ── */
@media (max-width: 800px) {

	.right-panel {
		border-top: 1px solid var(--border);
	}

	.metrics-cols {
		grid-template-columns: 1fr;
	}
}
</style>
