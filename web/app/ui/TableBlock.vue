<script setup>
import { computed } from "vue";
import { checkConstraints } from "~/utils/checkData";
import { roundAnyNumber } from "~/utils/numberData";

defineProps({
	title: String,
	data: Object,
	criteria: {
		type: Object,
		default: () => ({}) // changed from array to object for proper key access
	},
	styling: {
		type: String,
		default: ""
	}
});

const criteriaKeys = computed(() => Object.keys(props.criteria));

/**
 * @param {number} value
 * @param {[number|null, number|null]} constraints
 * @returns {string}
 */
function valueScaling(value, constraints) {
	const scale = checkConstraints(value, constraints);
	if (scale === 1) return "green";
	else if (scale === 3) return "red";
	else return "";
}
</script>

<template>
	<div class="container" :style="styling">
		<h1 v-if="title" class="MSFont20">{{ title }}</h1>

		<template v-if="data">
			<div v-for="(value, key, i) in data" :key="i" v-if="criteriaKeys.includes(key) && value !== null"
				class="entry">
				<span class="MSFont16w">{{ key }}</span>
				<span class="MSFont16w" :class="valueScaling(value, criteria[key])">
					{{ roundAnyNumber(value, 2) }}
				</span>
			</div>
		</template>
	</div>
</template>

<style scoped>
div.container {
	display: flex;
	flex-direction: column;
	width: fit-content;
	gap: 8px;
	border: 1.5px solid var(--neutral500);
	padding: 1rem;
	border-radius: 10px;
}

div.container * {
	margin: 0;
}

div.entry {
	display: flex;
	justify-content: space-between;
	gap: 5rem;
	padding: 2px 0;
}

div.entry:not(:last-child) {
	border-bottom: 1px solid var(--neutral500);
	padding-bottom: 8px;
}

.even {
	background-color: var(--neutral600);
}

.green {
	color: var(--systemGreen300);
}

.red {
	color: var(--systemRed300);
}
</style>
