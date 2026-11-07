<script setup>
import { watchDebounced } from "@vueuse/core"
import { cached } from "~/utils/cache"
import { useToast } from "~/utils/toast"
import { API } from "#shared/constants/routes"
import { validateIntrinsicValueInputs } from "#shared/validators/intrinsic-value"
import ivGraph from "~/assets/placeholders/intrinsic-value-graph.png"

const route = useRoute()
const symbol = computed(() =>
	(route.params.symbol || "").toString().toUpperCase(),
)

const inputs = reactive({
	growthDiscount: 15,
	cashFlowDiscount: 10,
	safetyMargin: 25,
	projectionHorizon: 5,
})

const cacheKey = computed(() =>
	`fa-iv-${symbol.value}-${inputs.growthDiscount}-${inputs.cashFlowDiscount}-${inputs.safetyMargin}-${inputs.projectionHorizon}`,
)

useHead(() => ({
	title: `${symbol.value} - Intrinsic Value`,
}))

const analysis = shallowRef(null)
const pending = ref(false)
const error = shallowRef(null)
const { showToast } = useToast()

function blockPlus(e) {
	if (e.key === '+') e.preventDefault()
}

function blockPlusPaste(e) {
	const text = e.clipboardData.getData('text')
	if (text.includes('+')) e.preventDefault()
}

async function fetchAnalysis() {
	// DCF needs ≥3 FY cash flows — POST would just 400 with the same message
	if (!enoughHistory.value) return
	const validation = validateIntrinsicValueInputs({ ...inputs })
	if (!validation.valid) {
		showToast(Object.values(validation.errors)[0], { theme: "error" })
		return
	}

	pending.value = true
	error.value = null
	analysis.value = null

	try {
		const { growthDiscount, cashFlowDiscount, safetyMargin, projectionHorizon } = validation.value
		analysis.value = await cached(cacheKey.value, () =>
			$fetch(API.stocks.get_intrinsic_value(symbol.value), {
				method: "POST",
				body: {
					growthDiscount,
					cashFlowDiscount,
					safetyMargin,
					projectionHorizon,
				},
			}),
		)
	} catch (err) {
		error.value = err
	} finally {
		pending.value = false
	}
}

watchDebounced(
	() => [
		symbol.value,
		inputs.growthDiscount,
		inputs.cashFlowDiscount,
		inputs.safetyMargin,
		inputs.projectionHorizon
	],
	fetchAnalysis,
	{
		debounce: 300,
		immediate: true,
	},
)

/** @type {boolean} */
const upsidePos = computed(() => {
	return analysis.value?.iv_upside[0] >= 0
})

// projection horizon is capped at the stock's real FY cash-flow count —
// the user cannot project more years than data exists for
const maxYears = ref(10)
// the DCF needs the 3 newest FCFs — stocks with fewer FY statements
// than that cannot compute an intrinsic value at all
const enoughHistory = ref(true)

async function fetchMaxYears() {
	try {
		const data = await cached(`iv-maxyears-${symbol.value}`, () =>
			$fetch(API.stocks.get_intrinsic_value(symbol.value))
		)
		const available = data?.available_years ?? 10
		// validator hard-caps at 10 — cap is the true min(available, 10),
		// never inflated: a stock with 4 FY statements caps at 4
		maxYears.value = Math.min(available, 10)
		enoughHistory.value = available >= 3
	} catch {
		maxYears.value = 10
		enoughHistory.value = true
	}
	// also covers the symbol-change case (cap may shrink)
	if (inputs.projectionHorizon > maxYears.value) {
		inputs.projectionHorizon = maxYears.value
	}
}

onMounted(fetchMaxYears)
watch(symbol, fetchMaxYears)

// late-arriving cap (cache miss) — clamp immediately
watch(maxYears, () => {
	if (inputs.projectionHorizon > maxYears.value) {
		inputs.projectionHorizon = maxYears.value
	}
})

// market cap is display-only (model no longer uses it) — fetched from
// stock_quote via the quote endpoint, cached per symbol
const marketCap = shallowRef(null)

async function fetchMarketCap() {
	try {
		const data = await cached(`iv-mcap-${symbol.value}`, () =>
			$fetch(`${API.stocks.get_quote(symbol.value)}?select=market_cap`)
		)
		marketCap.value = data?.market_cap ?? null
	} catch {
		marketCap.value = null
	}
}

onMounted(fetchMarketCap)
watch(symbol, fetchMarketCap)

function formatMarketCap(v) {
	if (v == null) return "—"
	return "$" + Number(v).toLocaleString("en-US", {
		notation: "compact",
		maximumFractionDigits: 2,
	})
}


</script>

<template>
	<div class="content-split">
		<div class="panel-header">
			<Text variant="label">Analysis Insight</Text>
		</div>

		<div class="panel-header">
			<Text variant="body">
				Cash flow growth for last {{ analysis?.agr_years || "N" }} years
				has maintained a CAGR of
				<strong style="color: var(--teal);">
					{{ analysis?.annual_growth_rate?.[1] }}%
				</strong>
				This volatility is accounted for in the
				risk-adjusted terminal multiple.

			</Text>
		</div>

		<div class="panel-header">
			<Text variant="label">Assumptions</Text>
		</div>

		<div class="input-group">
			<Text variant="label">Projection Horizon (YEARS)</Text>
			<Input v-model.number="inputs.projectionHorizon" type="number" min="3" :max="maxYears" step="1" :disabled="!enoughHistory" @keydown="blockPlus" @paste="blockPlusPaste" />
			<Text variant="label">Growth Discount Rate (%)</Text>
			<Input v-model.number="inputs.growthDiscount" type="number" min="0" max="100" step="0.5" @keydown="blockPlus" @paste="blockPlusPaste" />
			<Text variant="label">Cash Flow Discount Rate (%)</Text>
			<Input v-model.number="inputs.cashFlowDiscount" type="number" min="0" max="100" step="0.5" @keydown="blockPlus" @paste="blockPlusPaste" />
			<Text variant="label">Margin of Safety (%)</Text>
			<Input v-model.number="inputs.safetyMargin" type="number" min="0" max="100" step="1" @keydown="blockPlus" @paste="blockPlusPaste" />
		</div>

		<div class="result-row">
			<Text variant="body">Intrinsic Value: </Text>
			<Text variant="h3" v-if="analysis && !pending">
				${{ analysis.intrinsic_value[1] }}
			</Text>
			<Text variant="h3" v-else-if="pending">...</Text>
			<Text variant="h3" v-else-if="error" style="color: var(--rose)">
				{{ error.data?.message || error.message || "Error fetching data" }}
			</Text>
		</div>

		<div class="result-row">
			<Text variant="body">Market Cap:</Text>
			<Text variant="h3" v-if="marketCap != null">
				{{ formatMarketCap(marketCap) }}
			</Text>
			<Text variant="h3" v-else-if="pending">...</Text>
			<Text variant="h3" v-else-if="error" style="color: var(--rose)">
				{{ error.data?.message || error.message || "Error fetching data" }}
			</Text>
			<Text variant="h3" v-else>—</Text>
		</div>

		<div class="result-grid">
			<Text variant="body" style="color: var(--teal)">
				Intrinsic Value Per Share:
			</Text>

			<Tag :theme="upsidePos ? 'info' : 'error'" :label="analysis?.iv_upside[1] + ' upside'" border />

			<Text Text variant="h3" :style="{ color: upsidePos ? 'var(--teal)' : 'var(--rose)' }"
				v-if="analysis && !pending">
				${{ analysis.intrinsic_value_per_share[1] }}
			</Text>
			<Text variant="h3" v-else-if="pending">...</Text>
			<Text variant="h3" v-else-if="error" style="color: var(--rose)">
				{{ error.data?.message || error.message || "Error fetching data" }}
			</Text>
		</div>

		<div class="panel-header">
			<Text variant="label">Projected Free Cash Flow</Text>
		</div>

		<div>
			<img :src="ivGraph" alt="iv" class="chart-img" style="height: 100%;">
		</div>
	</div>
</template>

<style scoped>
.content-split {
	display: grid;
	grid-template-columns: 1fr 1fr;
	border: 1px solid var(--border);
	grid-template-areas:
		"a x"
		"b y"
		"c y"
		"d y"
		"e y"
		"f y"
		"g y";

	&>* {
		border: 1px solid var(--border);
	}

	&> :nth-child(1) {
		grid-area: a;
	}

	&> :nth-child(2) {
		grid-area: b;
	}

	&> :nth-child(3) {
		grid-area: c;
	}

	&> :nth-child(4) {
		grid-area: d;
	}

	&> :nth-child(5) {
		grid-area: e;
	}

	&> :nth-child(6) {
		grid-area: f;
	}

	&> :nth-child(7) {
		grid-area: g;
	}

	&> :nth-child(8) {
		grid-area: x;
	}

	&> :nth-child(9) {
		grid-area: y;
	}
}


.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 1rem 1.5rem 0.6rem;
}


.input-group {
	display: flex;
	flex-direction: column;
	padding: 1rem 1.5rem 1.25rem;
	gap: 4px;
}

.input-group>*:nth-child(even) {
	margin-bottom: 0.75rem;
}

.result-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0.85rem 1.5rem;
}

.result-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	align-items: center;
	justify-items: start;
	padding: 1.25rem 1.5rem;
	gap: 4px;
	grid-template-areas:
		"a c"
		"b c";

	&> :nth-child(1) {
		grid-area: a;
	}

	&> :nth-child(2) {
		grid-area: b;
	}

	&> :nth-child(3) {
		grid-area: c;
		justify-self: end;
	}
}


/* ── Responsive ── */
@media (max-width: 900px) {
	.content-split {
		grid-template-columns: 1fr;
		grid-template-areas:
			"a"
			"b"
			"c"
			"d"
			"e"
			"f"
			"g"
			"x"
			"y";
	}

	.content-split> :nth-child(-n+7) {
		border-right: none;
		border-bottom: 1px solid var(--border);
	}
}
</style>
