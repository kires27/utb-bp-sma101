<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const pageId = route.params.member

</script>

<template>
	<h2>{{pageId}}</h2>
</template>

<style scoped>
h2 {
	color: var(--color-text1);
}
</style>