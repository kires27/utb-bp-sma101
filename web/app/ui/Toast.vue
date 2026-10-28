<script setup>
const props = defineProps({
	message: {
		type: String,
		required: true
	},
	duration: {
		type: Number,
		default: 5000
	},
	theme: {
		type: String,
		default: 'info',
		validator: v => ['info', 'error'].includes(v)
	}
})

const emit = defineEmits(['close'])

// Auto-close after duration
onMounted(() => {
	setTimeout(() => {
		emit('close')
	}, props.duration)
})
</script>

<template>
	<div :class="['toast', `toast--${theme}`]">
		<Text variant="label">{{ message }}</Text>
	</div>
</template>

<style scoped>
.toast {
	padding: 0.4rem 0.9rem;
	animation: fade-toast 0.3s ease;
}
.toast--info {
	border: 1px solid var(--teal-border);
	background: var(--teal-dim);
}
.toast--info :deep(.label) {
	color: var(--teal);
}
.toast--error {
	border: 1px solid var(--rose);
	background: var(--rose-dim);
}
.toast--error :deep(.label) {
	color: var(--rose);
}

@keyframes fade-toast {
	from { opacity: 0; transform: translateY(10px); }
	to { opacity: 1; transform: translateY(0); }
}
</style>
