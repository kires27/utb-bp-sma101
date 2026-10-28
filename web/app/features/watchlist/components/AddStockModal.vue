<script setup>
import { URI } from "#shared/constants/routes"

const props = defineProps({
	open: Boolean,
	items: { type: Array, default: () => [] },
})

const emit = defineEmits(["close", "add"])

function isInWatchlist(symbol) {
	const upperSymbol = symbol.toUpperCase()
	return props.items.some((s) => {
		if (typeof s === "string") return s.toUpperCase() === upperSymbol
		return s.symbol?.toUpperCase() === upperSymbol
	})
}

function handleSelect(symbol) {
	navigateTo(URI.tool.fa_financials(symbol))
}

function handleAdd(symbol) {
	emit("add", symbol)
}
</script>

<template>
	<Modal :open="open" @close="emit('close')">
		<div class="add-stock-modal">
			<Text variant="h3">Add Stock</Text>
			<Searchbar @select="handleSelect" placeholder="Search company...">
				<template #menuAction="{ item }">
					<Button variant="secondary" size="sm" :disabled="isInWatchlist(item.symbol)"
						@click.stop="handleAdd(item.symbol)">
						<Icon :name="isInWatchlist(item.symbol)
							? 'material-symbols:check-circle'
							: 'material-symbols:playlist-add'" />
					</Button>
				</template>
			</Searchbar>
		</div>
	</Modal>
</template>

<style scoped>
.add-stock-modal {
	padding: 1.5rem;
	display: flex;
	flex-direction: column;
	gap: 1rem;
}
</style>
