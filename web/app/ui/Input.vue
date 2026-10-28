<script setup>
defineOptions({ inheritAttrs: false })

const props = defineProps({
	modelValue: {
		default: ''
	},
	type: {
		type: String,
		default: 'text',
		validator: (v) => ['text', 'email', 'number', 'password'].includes(v)
	},
	placeholder: {
		type: String,
		default: ''
	},
	error: {
		type: Boolean,
		default: false
	},
	errorText: {
		type: String,
		default: 'Error'
	}
})

defineEmits(['update:modelValue', 'focus'])

const showPassword = ref(false)

const inputType = computed(() => {
	if (props.type === 'password') return showPassword.value ? 'text' : 'password';
	return props.type;
})
</script>

<template>
	<div class="input-wrapper">
		<div class="input-row">
			<slot name="icon" />

			<input :type="inputType" :placeholder="placeholder" :value="modelValue" v-bind="$attrs"
				:class="['input', { 'input--error': error }]"
				@input="$emit('update:modelValue', $event.target.value)"
				@focus="$emit('focus', $event)" />

			<button v-if="type === 'password'" type="button" class="password-toggle"
				@click="showPassword = !showPassword">
				<Icon :name="showPassword ? 'material-symbols:visibility-off' : 'material-symbols:visibility'" />
			</button>

			<slot name="status" />
		</div>

		<span v-if="error && errorText" class="input-error">{{ errorText }}</span>
	</div>
</template>

<style scoped>
.input-wrapper {
	width: 100%;
}

.input-row {
	display: flex;
	align-items: center;
	gap: 0.6rem;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	padding: 0.5rem 0.85rem;
	transition: border-color 0.15s;
	flex-shrink: 0;
	color: var(--fg-3);

}

.input-row:focus-within {
	border-color: var(--teal);
}

.input {
	flex: 1;
	background: none;
	border: none;
	outline: none;
	font-family: var(--font-main);
	font-size: 12px;
	color: var(--fg);
	letter-spacing: 0.04em;
}

.input::placeholder {
	color: var(--fg-3);
}

.input[type="number"]::-webkit-inner-spin-button,
.input[type="number"]::-webkit-outer-spin-button {
	-webkit-appearance: none;
	margin: 0;
}

.input[type="number"] {
	-moz-appearance: textfield;
}

.password-toggle {
	display: flex;
	align-items: center;
	background: none;
	border: none;
	color: var(--fg-3);
	cursor: pointer;
	padding: 0;
	flex-shrink: 0;
}

.password-toggle:hover {
	color: var(--fg);
}

.input-row:has(.input--error) {
	border-color: var(--rose);
}

.input-error {
	display: block;
	font-size: 11px;
	color: var(--rose);
	margin-top: 0.35rem;
}
</style>
