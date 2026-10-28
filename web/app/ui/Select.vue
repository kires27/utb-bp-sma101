<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
	modelValue: { default: '' },
	placeholder: { type: String, default: '' },
	options: { type: Array, default: () => [] },
	error: { type: Boolean, default: false },
	errorText: { type: String, default: 'Error' }
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const wrapperRef = ref(null)
const activeIdx = ref(-1)

const normalizedOptions = computed(() =>
	props.options.map(o => typeof o === 'string' ? { value: o, label: o } : o)
)

const selectedLabel = computed(() => {
	const found = normalizedOptions.value.find(o => o.value === props.modelValue)
	return found ? found.label : ''
})

function toggle() {
	open.value = !open.value
	if (!open.value) activeIdx.value = -1
}

function select(val) {
	emit('update:modelValue', val)
	open.value = false
	activeIdx.value = -1
}

function onTriggerKeydown(e) {
	if (e.key === 'Enter' || e.key === ' ') {
		e.preventDefault()
		toggle()
	}
	if (e.key === 'Escape' && open.value) {
		open.value = false
		activeIdx.value = -1
	}
}

function onDropdownKeydown(e) {
	const items = normalizedOptions.value
	if (e.key === 'ArrowDown') {
		e.preventDefault()
		activeIdx.value = activeIdx.value < items.length - 1 ? activeIdx.value + 1 : 0
	}
	if (e.key === 'ArrowUp') {
		e.preventDefault()
		activeIdx.value = activeIdx.value > 0 ? activeIdx.value - 1 : items.length - 1
	}
	if (e.key === 'Enter' && activeIdx.value >= 0) {
		e.preventDefault()
		select(items[activeIdx.value].value)
	}
	if (e.key === 'Escape') {
		open.value = false
		activeIdx.value = -1
	}
}

function onClickOutside(e) {
	if (wrapperRef.value && !wrapperRef.value.contains(e.target)) {
		open.value = false
		activeIdx.value = -1
	}
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
	<div ref="wrapperRef" class="select-wrapper">
		<div
			class="select-row"
			:class="{ 'select-row--open': open, 'select-row--error': error }"
			tabindex="0"
			role="combobox"
			:aria-expanded="open"
			@click="toggle"
			@keydown="onTriggerKeydown"
		>
			<span class="select-value" :class="{ 'select-value--placeholder': !selectedLabel }">
				{{ selectedLabel || placeholder }}
			</span>
			<Icon
				name="material-symbols:expand-more"
				class="select-chevron"
				:class="{ 'select-chevron--open': open }"
			/>
		</div>

		<Transition name="dropdown">
			<div v-if="open" ref="listRef" class="select-dropdown" @keydown="onDropdownKeydown">
				<div
					v-for="(opt, i) in normalizedOptions"
					:key="opt.value"
					class="select-option"
					:class="{
						'select-option--selected': opt.value === modelValue,
						'select-option--active': i === activeIdx
					}"
					@click="select(opt.value)"
					@mouseenter="activeIdx = i"
				>
					{{ opt.label }}
				</div>
			</div>
		</Transition>

		<span v-if="error && errorText" class="select-error">{{ errorText }}</span>
	</div>
</template>

<style scoped>
.select-wrapper {
	position: relative;
	width: 100%;
}

.select-row {
	display: flex;
	align-items: center;
	gap: 0.6rem;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	padding: 0.5rem 0.85rem;
	transition: border-color 0.15s;
	flex-shrink: 0;
	color: var(--fg-3);
	cursor: pointer;
	user-select: none;
}

.select-row:focus-visible,
.select-row--open {
	border-color: var(--teal);
	outline: none;
}

.select-row--error {
	border-color: var(--rose);
}

.select-value {
	flex: 1;
	font-family: var(--font-main);
	font-size: 12px;
	color: var(--fg);
	letter-spacing: 0.04em;
}

.select-value--placeholder {
	color: var(--fg-3);
}

.select-chevron {
	color: var(--fg-3);
	flex-shrink: 0;
	transition: transform 0.15s;
}

.select-chevron--open {
	transform: rotate(180deg);
}

.select-dropdown {
	position: absolute;
	top: 100%;
	left: 0;
	right: 0;
	z-index: 100;
	margin-top: 2px;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	max-height: 220px;
	overflow-y: auto;
}

.select-option {
	padding: 0.5rem 0.85rem;
	font-family: var(--font-main);
	font-size: 12px;
	color: var(--fg);
	letter-spacing: 0.04em;
	cursor: pointer;
	transition: background 0.1s;
}

.select-option:hover,
.select-option--active {
	background: var(--bg-hover);
}

.select-option--selected {
	color: var(--teal);
}

.dropdown-enter-active,
.dropdown-leave-active {
	transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}

.select-error {
	display: block;
	font-size: 11px;
	color: var(--rose);
	margin-top: 0.35rem;
}
</style>
