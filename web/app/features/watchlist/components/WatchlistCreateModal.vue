<script setup>
import { ref, watch } from "vue"

const props = defineProps({
	open: Boolean,
	mode: { type: String, default: "create" },
	watchlists: { type: Array, default: () => [] },
	selectedId: { type: [Number, String], default: null },
})

const emit = defineEmits(["close", "submit"])

const name = ref("")

watch(() => props.open, (val) => {
	if (val) {
		if (props.mode === "rename") {
			const found = props.watchlists.find(
				(w) => String(w.id) === String(props.selectedId),
			)
			name.value = found?.name || ""
		} else {
			name.value = ""
		}
	}
})

function onSubmit() {
	if (!name.value?.trim()) return
	emit("submit", name.value.trim())
}
</script>

<template>
	<Modal :open="open" @close="emit('close')">
		<div class="create-wl-modal">
			<Text variant="h3">{{ mode === "create" ? "Create Watchlist" : "Rename Watchlist" }}</Text>
			<Input v-model="name" placeholder="Watchlist name..." />
			<Button variant="primary" @click="onSubmit">{{ mode === "create" ? "Create" : "Rename" }}</Button>
		</div>
	</Modal>
</template>

<style scoped>
.create-wl-modal {
	padding: 1.5rem;
	display: flex;
	flex-direction: column;
	gap: 1rem;
}
</style>
