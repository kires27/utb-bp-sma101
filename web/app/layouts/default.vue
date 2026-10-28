<script setup>
</script>

<template>
	<main id="content">
		<Header />
		<slot />
	</main>
</template>

<style scoped>
main#content {
	min-height: 100vh;
	display: flex;
	flex-direction: column;
}
</style>