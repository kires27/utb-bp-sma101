<script setup>
import { computed } from 'vue'

const props = defineProps({
	/** Number of columns */
	cols: {
		type: Number,
		default: 3,
		validator: (v) => [1, 2, 3, 4, 6].includes(v),
	},
	/** Grid gap */
	gap: {
		type: String,
		default: 'na',
		validator: (v) => ['na', 'sm', 'md', 'lg'].includes(v),
	},
	/** Toggle grid borders */
	bordered: {
		type: Boolean,
		default: true,
	},
	/** Vertical alignment of rows within grid */
	alignContent: {
		type: String,
		default: 'stretch',
		validator: (v) => ['stretch', 'start', 'center', 'end', 'space-between', 'space-around', 'space-evenly'].includes(v),
	},
})

const gapMap = {
	na: '0',
	sm: '1rem',
	md: '2rem',
	lg: '4rem',
}

const isFlush = computed(() => props.gap === 'na')

const colStyle = computed(() => ({
	display: 'grid',
	gridTemplateColumns: `repeat(${props.cols}, 1fr)`,
	gap: gapMap[props.gap],
	alignContent: props.alignContent,
}))
</script>


<template>
	<div :class="{ 'grid-border': bordered, 'grid-border--flush': bordered && isFlush }" :style="colStyle">
		<slot />
	</div>
</template>


<style scoped>
/* Gap > 0: cells never touch, so give each one a full self-contained border */
.grid-border:not(.grid-border--flush) > :deep(*) {
	/* box-shadow: 0 0 0 1px var(--border); */
	border: 1px solid var(--border);
}

/* Gap = 0: cells touch, so avoid double-drawn shared edges entirely.
   Each cell draws only its top+left; the container closes off the
   outer right/bottom edge (works even with a partial last row). */
.grid-border--flush {
	border-right: 1px solid var(--border);
	border-bottom: 1px solid var(--border);
}

.grid-border--flush > :deep(*) {
	border-top: 1px solid var(--border);
	border-left: 1px solid var(--border);
}
</style>