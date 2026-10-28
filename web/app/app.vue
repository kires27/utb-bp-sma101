<script setup>
import { useToast } from "~/utils/toast"

const { toasts, removeToast } = useToast()
</script>

<template>
	<NuxtLayout>
		<NuxtPage />

		<div class="toast-stack">
			<Toast v-for="t in toasts" :key="t.id" :message="t.message" :theme="t.theme"
				@close="removeToast(t.id)" />
		</div>
	</NuxtLayout>
</template>

<style scoped>
.toast-stack {
	position: fixed;
	bottom: 70px;
	right: 2.5rem;
	display: flex;
	flex-direction: column-reverse;
	gap: 0.5rem;
	z-index: 999;
}
</style>
