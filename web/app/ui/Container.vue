<script setup>
defineProps({
	direction: {
		type: String,
		default: 'column',
		validator: (v) => ['row', 'column'].includes(v)
	},
	hAlign: {
		type: String,
		default: 'start',
		validator: (v) => ['start', 'center', 'end', 'between', 'around', 'evenly'].includes(v)
	},
	vAlign: {
		type: String,
		default: 'center',
		validator: (v) => ['start', 'center', 'end', 'stretch'].includes(v)
	},
	gap: {
		type: String,
		default: 'na',
		validator: (v) => ['na', 'sm', 'md', 'lg'].includes(v)
	},
})
</script>

<template>
	<div :class="[
		'container',
		`container--${direction}`,
		`container--h-${hAlign}`,
		`container--v-${vAlign}`,
		`container--gap-${gap}`,
	]">
		<slot />
	</div>
</template>

<style scoped>
.container {
	display: flex;
	flex: 1;
}

.container--row {
	flex-direction: row;
}

.container--column {
	flex-direction: column;
}

.container--h-start {
	justify-content: flex-start;
}

.container--h-center {
	justify-content: center;
}

.container--h-end {
	justify-content: flex-end;
}

.container--h-between {
	justify-content: space-between;
}

.container--h-around {
	justify-content: space-around;
}

.container--h-evenly {
	justify-content: space-evenly;
}

.container--v-start {
	align-items: flex-start;
}

.container--v-center {
	align-items: center;
}

.container--v-end {
	align-items: flex-end;
}

.container--v-stretch {
	align-items: stretch;
}

.container--gap-na {
	gap: 0;
}

.container--gap-sm {
	gap: 1rem;
}

.container--gap-md {
	gap: 2rem;
}

.container--gap-lg {
	gap: 4rem;
}
</style>
