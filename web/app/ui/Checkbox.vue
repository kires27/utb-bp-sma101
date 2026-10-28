<script setup>
defineProps({
	modelValue: {
		type: Boolean,
		default: false
	},
	label: {
		type: String,
		default: ''
	}
})

defineEmits(['update:modelValue'])
</script>

<template>
	<label class="checkbox-label">
		<input type="checkbox" class="checkbox" :checked="modelValue" @change="$emit('update:modelValue', $event.target.checked)" />
		<Text variant="label" tone="muted" link>{{ label }}</Text>
	</label>
</template>

<style scoped>
.checkbox-label {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	cursor: pointer;
	font-size: 11px;
	color: var(--fg-3);
}

.checkbox {
	appearance: none;
	width: 14px;
	height: 14px;
	border: 1px solid var(--border-hi);
	background: var(--bg-2);
	cursor: pointer;
	flex-shrink: 0;
}

.checkbox:checked {
	background: var(--teal);
	border-color: var(--teal);
}
</style>
