<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'

const props = defineProps({
	value: { type: Number, required: true },
	vertical: { type: Boolean, default: false },
	thickness: { type: Number, default: 3 },
	color: { type: String, default: 'var(--teal)' },

	fillAnimation: { type: Boolean, default: true },
	duration: { type: Number, default: 600 }
})

const displayValue = ref(0)

onMounted(() => {
	if (!props.fillAnimation) {
		displayValue.value = clamp(props.value)
		return
	}

	requestAnimationFrame(() => {
		displayValue.value = clamp(props.value)
	})
})

watch(
	() => props.value,
	(v) => {
		displayValue.value = clamp(v)
	},
)

function clamp(v: number) {
	return Math.max(0, Math.min(100, v))
}

const fillStyle = computed(() => {
	const v = displayValue.value

	const base = {
		background: props.color,
		transition: props.fillAnimation
			? (props.vertical
				? `height ${props.duration}ms ease`
				: `width ${props.duration}ms ease`)
			: 'none'
	}

	if (props.vertical) {
		return {
			...base,
			height: v + '%',
			width: '100%'
		}
	}

	return {
		...base,
		width: v + '%',
		height: '100%'
	}
})
</script>


<template>
	<div class="track-wrap" :class="{ vertical }">
		<div class="track">
			<div class="track-fill" :style="fillStyle"></div>
		</div>

		<div class="track-labels">
			<Text variant="label">0</Text>
			<Text variant="label">50</Text>
			<Text variant="label">100</Text>
		</div>
	</div>
</template>


<style scoped>
.track-wrap {
	margin-top: 0.5rem;
}

.track {
	background: var(--border);
	overflow: hidden;
	height: v-bind('thickness + "px"');
	width: 100%;
}

.track-wrap.vertical .track {
	width: 20px;
	height: 120px;
}

.track-fill {
	width: 0%;
	height: 100%;
}

.track-labels {
	display: flex;
	justify-content: space-between;
	margin-top: 0.35rem;
	font-size: 9px;
	letter-spacing: 0.08em;
	color: var(--fg-3);
	font-family: var(--font-main);
}
</style>