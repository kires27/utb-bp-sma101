<script setup>
defineProps({
	/** Dot-grid background overlay */
	bgGrid: {
		type: Boolean,
		default: false,
	},
	width: {
		type: String,
		default: 'na',
		validator: (v) => ['na', 'sm', 'md', 'lg'].includes(v)
	},
	topMargin: {
		type: String,
		default: '',
		validator: (v) => ['', 'sm', 'md', 'lg'].includes(v)
	},
	bottomMargin: {
		type: String,
		default: '',
		validator: (v) => ['', 'sm', 'md', 'lg'].includes(v)
	},
})
</script>

<template>
	<section :class="[
		'section',
		{ 'bg-grid': bgGrid },
		`section--width-${width}`,
		`section--top-${topMargin}`,
		`section--bottom-${bottomMargin}`,
	]">

		<slot />
	</section>
</template>

<style scoped>
.section {
	position: relative;
	/* border-bottom: 1px solid var(--border); */
}

.bg-grid::before {
	content: '';
	position: absolute;
	inset: 0;
	background-image:
		linear-gradient(var(--border) 1px, transparent 1px),
		linear-gradient(90deg, var(--border) 1px, transparent 1px);
	background-size: 60px 60px;
	opacity: 0.8;
	pointer-events: none;
	border-bottom: 1px solid var(--border);
}

.section--width-na {
	/* padding-inline: 0; */
}

.section--width-sm {
	width: 30rem;

}

.section--width-md {
	width: 50rem;
}

.section--width-lg {
	/* width: 100rem; */
	width: min(70rem, 90vw);
}

.section--top-sm {
	margin-top: 2rem;
}

.section--bottom-sm {
	margin-bottom: 2rem;
}

.section--top-md {
	margin-top: 5rem;
}

.section--bottom-md {
	margin-bottom: 5rem;
}

.section--top-lg {
	margin-top: 8rem;
}

.section--bottom-lg {
	margin-bottom: 8rem;
}
</style>
