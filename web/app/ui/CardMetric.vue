<script setup>
defineProps({
	label: {
		type: String,
		required: true
	},
	value: {
		type: [String, Number],
		required: true
	},
	tagVariant: {
		type: String,
		default: null,
		validator: (v) => v === null || ['info', 'warning'].includes(v)
	},
	tagLabel: {
		type: String,
		default: ''
	}
})
</script>

<template>
	<div class="metric-card">
		<div class="metric-label">{{ label }}</div>
		<div class="metric-value">
			{{ value }}
			<Tag v-if="tagVariant" :theme="tagVariant" :label="tagLabel" />
		</div>
	</div>
</template>

<style scoped>
.metric-card {
	background: var(--bg-2);
	border: 1px solid var(--border);
	padding: 0.75rem;
	text-align: center;
}

.metric-label {
	font-size: 10px;
	letter-spacing: 0.12em;
	text-transform: uppercase;
	color: var(--fg-3);
	margin-bottom: 0.3rem;
}

.metric-value {
	font-size: 20px;
	font-weight: 500;
	letter-spacing: -0.02em;
}
</style>
