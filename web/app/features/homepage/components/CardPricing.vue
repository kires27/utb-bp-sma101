<script setup>
defineProps({
	name: {
		type: String,
		required: true,
	},
	price: {
		type: String,
		required: true,
	},
	period: {
		type: String,
		default: "/month",
	},
	description: {
		type: String,
		required: true,
	},
	features: {
		type: Array,
		required: true,
	},
	popular: {
		type: Boolean,
		default: false,
	},
})
</script>

<template>
	<div :class="['pricing-card', { 'pricing-card--popular': popular }]">
		<div v-if="popular" class="popular-mark">
			<Text variant="label" tone="muted">Most Popular</Text>
		</div>
		<Text variant="label" tone="muted" class="plan-name">{{ name }}</Text>
		<Text variant="h1">{{ price }}</Text>
		<Text variant="label" tone="muted" class="plan-period">{{ period }}</Text>
		<Text variant="body-sm" tone="muted" class="plan-desc">{{ description }}</Text>
		<ul class="plan-features">
			<li v-for="(feature, index) in features" :key="index" class="plan-feature">
				<span class="plan-feature-check">✓</span>
				<Text variant="body-sm" tone="muted">{{ feature }}</Text>
			</li>
		</ul>
		<div v-if="$slots.actions" class="pricing-actions">
			<slot name="actions" />
		</div>
	</div>
</template>

<style scoped>
.pricing-card {
	position: relative;
	padding: 1.5rem;
	display: flex;
	flex-direction: column;
}

.pricing-card--popular {
	background: var(--bg-2);
}

.popular-mark {
	position: absolute;
	top: 0;
	left: 1.5rem;
	background: var(--teal);
	padding: 0.25rem 0.7rem;
}

.popular-mark .text {
	color: #0c0c0f;
}

.plan-name {
	margin-bottom: 1.25rem;
	padding-top: 1rem;
}

.plan-price {
	font-size: 2.75rem;
	font-weight: 300;
	letter-spacing: -0.03em;
	line-height: 1;
	margin-bottom: 0.25rem;
}

.plan-period {
	margin-bottom: 0.75rem;
}

/* .plan-desc {
	border-bottom: 1px solid var(--border);
	padding-bottom: 1rem;
	margin-bottom: 1rem;
} */

.plan-features {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	flex: 1;
	margin-bottom: 1.5rem;
}

.plan-feature {
	display: flex;
	align-items: flex-start;
	gap: 0.5rem;
}

.plan-feature-check {
	color: var(--teal);
	flex-shrink: 0;
	margin-top: 2px;
}

.pricing-actions {
	margin-top: auto;
}
</style>
