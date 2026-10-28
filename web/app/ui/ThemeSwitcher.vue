<script setup>
import { ref, onMounted, watch } from "vue";

const themes = {
	"light": "#ffffff",
	"dark": "#231e2b"
}
const theme = ref("light");

onMounted(() => {
	const savedTheme = localStorage.getItem("theme");
	if (savedTheme && Object.keys(themes).includes(savedTheme)) {
		theme.value = savedTheme;
	}
	document.body.setAttribute("data-theme", theme.value);
});

watch(theme, (newTheme, oldTheme) => {
	if (newTheme !== oldTheme && document.body) {
		document.body.setAttribute("data-theme", newTheme);
		localStorage.setItem("theme", newTheme);
	}
});
</script>

<template>
	<div class="theme-box">
		<button
			v-for="themeName in Object.keys(themes)"
			:key="themeName"
			@click="theme = themeName"
			:style="{ backgroundColor: themes[themeName] }"
		/>
	</div>
</template>

<style scoped>
.theme-box {
	display: flex;
	gap: 8px;
	margin: 8px;
	border-radius: 12px;
}
button {
	width: 25px;
	height: 25px;
	border-radius: 50%;
	border: 1px solid var(--color-accent);
	transition: border 0.1s ease;

}
button:hover {
	border: 3px solid var(--color-accent);
}
</style>

