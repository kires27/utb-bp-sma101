<script setup>
defineProps({
	variant: {
		type: String,
		default: 'secondary',
		validator: (v) => ['primary', 'secondary', 'danger'].includes(v)
	},
	size: {
		type: String,
		default: 'md',
		validator: (v) => ['sm', 'md', 'lg'].includes(v)
	},
	wide: {
		type: Boolean,
		default: false
	},
	type: {
		type: String,
		default: 'button'
	},
	disabled: {
		type: Boolean,
		default: false
	},
	border: {
		type: Boolean,
		default: true
	}
})
</script>

<template>
	<button :type="type" :disabled="disabled" :class="[
		'btn',
		`btn--${variant}`,
		{ 'btn--sm': size === 'sm' },
		{ 'btn--lg': size === 'lg' },
		{ 'btn--full': wide },
		{ 'btn--no-border': !border }
	]">
		<slot />
	</button>
</template>

<style scoped>
.btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.5rem;
	font-family: var(--font-main);
	font-size: 12px;
	font-weight: 400;
	letter-spacing: 0.08em;
	white-space: nowrap;
	padding: 0.55rem 1.15rem;
	border: 1px solid var(--border-hi);
	background: transparent;
	color: var(--fg-2);
	cursor: pointer;
	transition: var(--transition);
}

.btn:hover {
	background: var(--bg-hover);
	color: var(--fg);
}

.btn--sm {
	font-size: 10px;
	padding: 0.35rem 0.75rem;
}

.btn--lg {
	font-size: 14px;
	padding: 0.75rem 1.75rem;
}

.btn--full {
	width: 100%;
}

.btn--no-border {
	border-color: transparent;
}

.btn--primary {
	background: var(--teal);
	border-color: var(--teal);
	color: #000;
	font-weight: 600;
}

.btn--primary:hover {
	background: var(--teal);
	border-color: var(--teal);
	color: #000;
	filter: brightness(1.2);
}

.btn--danger {
	border-color: rgba(196, 122, 122, 0.3);
	color: var(--rose);
}

.btn--danger:hover {
	background: var(--rose-dim);
}

.btn:disabled {
	opacity: 0.5;
	cursor: not-allowed;
}

.btn:disabled:hover {
	background: transparent;
	color: var(--fg-2);
}
</style>
