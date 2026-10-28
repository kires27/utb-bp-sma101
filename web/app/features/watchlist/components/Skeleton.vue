<script setup>
defineProps({
	rowIndex: { type: Number, default: 0 },
	columns: { type: Array, default: () => [] },
})
</script>

<template>
	<tr :style="{ opacity: 1 - rowIndex * 0.12 }">
		<td class="sk-idx">
			<div class="sk sk--sm" :style="{ animationDelay: `${rowIndex * 0.06}s` }" />
		</td>
		<td v-for="key in columns" :key="key" class="sk-cell">
			<div
				class="sk"
				:style="{ animationDelay: `${rowIndex * 0.06}s` }"
			/>
		</td>
	</tr>
</template>

<style scoped>
.sk-idx {
	width: 2.2rem;
	min-width: 2.2rem;
	max-width: 2.2rem;
	padding: 0.35rem 0;
	text-align: center;
	border-bottom: 1px solid var(--border);
}

.sk-cell {
	padding: 0.35rem 0.6rem;
	border-bottom: 1px solid var(--border);
	vertical-align: middle;
	white-space: nowrap;
	text-align: center;
}

.sk {
	height: 24px;
	margin: 0 4px;
	border-radius: 2px;
	width: calc(100% - 8px);
	background: linear-gradient(
		90deg,
		var(--bg-2) 0%,
		var(--border-hi) 50%,
		var(--bg-2) 100%
	);
	background-size: 200% 100%;
	animation: shimmer 1.6s ease-in-out infinite;
}

.sk--sm {
	width: 16px;
}

@keyframes shimmer {
	0% {
		background-position: 150% 0;
	}
	100% {
		background-position: -50% 0;
	}
}
</style>