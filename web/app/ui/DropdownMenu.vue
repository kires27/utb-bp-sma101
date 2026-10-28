<script setup>
import { computed } from "vue"

const props = defineProps({
	open: {
		type: Boolean,
		default: false,
	},
	align: {
		type: String,
		default: 'start',
		validator: (v) => ['start', 'center', 'end'].includes(v)
	}
})

const alignStyle = computed(() => {
	const style = {}
	if (props.align === 'end') {
		style.right = '0'
		style.left = 'auto'
	} else if (props.align === 'center') {
		style.left = '50%'
		style.transform = 'translateX(-50%)'
	}
	return style
})
</script>

<template>
	<div class="dropdown-menu" :class="{ open }" :style="alignStyle">
		<slot />
	</div>
</template>

<style scoped>
.dropdown-menu {
	position: absolute;
	top: calc(100% + 4px);
	display: flex;
	flex-direction: column;
	min-width: 180px;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
	z-index: 300;
	opacity: 0;
	transform: translateY(-6px);
	pointer-events: none;
	transition: opacity 0.15s, transform 0.15s;
}

.dropdown-menu::before {
	content: '';
	position: absolute;
	bottom: 100%;
	left: 0;
	right: 0;
	height: 6px;
}

.dropdown-menu.open {
	opacity: 1;
	transform: translateY(0);
	pointer-events: all;
}

</style>
