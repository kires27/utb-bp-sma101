<script setup>
defineProps({
	label: {
		type: String,
		required: true
	},
	theme: {
		type: String,
		default: 'info',
		validator: (v) => ['info', 'error', 'sector'].includes(v)
	},
	border: {
		type: Boolean,
		default: false
	},
	dot: {
		type: Boolean,
		default: false
	}
})
</script>

<template>
	<div :class="[
		'tag',
		`color--${theme}`,
		{ border },
	]">
		<span v-if="dot" class="dot"></span>
		<Text variant="label" v-bind="$attrs">{{ label }}</Text>
	</div>
</template>

<style scoped>
.tag {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
}

.tag :deep(*) {
	color: inherit;
}

.color--info {
	color: var(--teal);
}

.color--info.border {
	background: var(--teal-dim);
	border-color: var(--teal-border);
}

.color--error {
	color: var(--rose);
}

.color--error.border {
	background: var(--rose-dim);
	border-color: rgba(196, 122, 122, 0.3);
}

.color--sector {
	color: var(--purple);
}

.color--sector.border {
	background: rgba(139, 126, 200, 0.10);
	border-color: rgba(139, 126, 200, 0.25);
}

.border {
	border: 1px solid;
	padding: 0.3rem 0.6rem;

}

.dot {
	width: 6px;
	height: 6px;
	border-radius: 50%;
	flex-shrink: 0;
	background: currentColor;
	animation: pulse 2s infinite;
}

@keyframes pulse {

	0%,
	100% {
		opacity: 1;
	}

	50% {
		opacity: 0.3;
	}
}
</style>
