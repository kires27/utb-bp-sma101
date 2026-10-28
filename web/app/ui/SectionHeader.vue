<script setup>
defineProps({
	label: {
		type: String,
		default: null,
	},
})
</script>

<template>
	<div class="section-header" v-bind="$attrs">
		<Text v-if="label" variant="label" tone="muted" class="section-header-label">{{ label }}</Text>
		<Text variant="h2" class="section-header-title">
			<slot />
		</Text>
	</div>
</template>

<style scoped>
.section-header {
	margin-bottom: 2rem;
}

.section-header-label {
	display: block;
	margin-bottom: 0.75rem;
}
</style>
