<script setup>
defineProps({
	modelValue: {
		type: Boolean,
		default: false
	}
})

defineEmits(['update:modelValue'])
</script>

<template>
	<label class="toggle">
		<input
			type="checkbox"
			class="toggle-input"
			:checked="modelValue"
			@change="$emit('update:modelValue', $event.target.checked)"
		/>
		<span class="toggle-track"></span>
		<span class="toggle-thumb"></span>
	</label>
</template>

<style scoped>
.toggle {
	position: relative;
	width: 36px;
	height: 18px;
	cursor: pointer;
	flex-shrink: 0;
	display: block;
}

.toggle-input {
	opacity: 0;
	width: 0;
	height: 0;
	position: absolute;
}

.toggle-track {
	position: absolute;
	inset: 0;
	background: var(--bg-hover);
	border: 1px solid var(--border-hi);
	transition: all 0.2s;
}

.toggle-thumb {
	position: absolute;
	top: 3px;
	left: 3px;
	width: 10px;
	height: 10px;
	background: var(--fg-3);
	transition: all 0.2s;
}

.toggle-input:checked ~ .toggle-track {
	background: var(--teal-dim);
	border-color: var(--teal-border);
}

.toggle-input:checked ~ .toggle-thumb {
	background: var(--teal);
	transform: translateX(18px);
}
</style>
