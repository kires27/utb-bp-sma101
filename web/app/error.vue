<template>
	<div class="error-page">
		<h1>{{ error.statusCode }}</h1>
		<p>{{ error.message }}</p>
		<NuxtLink to="/">Go back home</NuxtLink>
	</div>
</template>

<script setup>
const error = useError();

console.log("asdf");
</script>

<style scoped>
.error-page {
	text-align: center;
	padding: 4rem;
}

.error-page h1 {
	font-size: 5rem;
	color: #ff4d4f;
}

.error-page p {
	font-size: 1.5rem;
	margin: 1rem 0;
}

.error-page a {
	color: #1890ff;
	text-decoration: underline;
}
</style>
