<script setup>
defineProps({
	author: {
		type: String,
		default: null,
	},
})
</script>

<template>
	<blockquote class="pullquote" v-bind="$attrs">
		<p class="quote-text">
			<slot />
		</p>
		<span v-if="author" class="quote-author">{{ author }}</span>
	</blockquote>
</template>

<style scoped>
.pullquote {
	border-left: 2px solid var(--teal);
	padding-left: 1.25rem;
	margin-top: 2rem;
}

.quote-text {
	font-family: var(--font-main);
	font-size: 13px;
	font-style: italic;
	color: var(--fg-2);
	margin-bottom: 0.5rem;
}

.quote-author {
	font-size: 10px;
	letter-spacing: 0.12em;
	text-transform: uppercase;
	color: var(--fg-3);
}
</style>
