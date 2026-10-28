<script setup>
import { ref } from "vue"

const props = defineProps({
	watchlists: { type: Array, default: () => [] },
	selectedId: { type: [Number, String], default: null },
})

const emit = defineEmits(["select", "create"])

const showSwitcher = ref(false)

function select(id) {
	emit("select", id)
	showSwitcher.value = false
}

function create() {
	showSwitcher.value = false
	emit("create")
}
</script>

<template>
	<div class="wl-switcher" :class="{ open: showSwitcher }">
		<Button variant="secondary" @click.stop="showSwitcher = !showSwitcher">
			<Text variant="body-sm">{{
				watchlists.find((w) => w.id === selectedId)?.name || "Select Watchlist"
			}}</Text>
			<span class="wl-chevron">▾</span>
		</Button>

		<DropdownMenu :open="showSwitcher">
			<div v-for="wl in watchlists" :key="wl.id" class="wl-item"
				:class="{ active: selectedId === wl.id }" @click="select(wl.id)">
				<div class="wl-item-left">
					<Text variant="label">{{ wl.name }}</Text>
				</div>
				<span class="wl-item-check">✓</span>
			</div>
			<Button variant="secondary" wide @click="create">
				<Text variant="label" tone="green" weight="light">+ New Watchlist</Text>
			</Button>
		</DropdownMenu>

		<div v-if="showSwitcher" class="overlay" @click="showSwitcher = false"></div>
	</div>
</template>

<style scoped>
.wl-switcher {
	position: relative;
}

.wl-chevron {
	font-size: 10px;
	color: var(--fg-3);
	margin-top: 1px;
	transition: transform 0.15s, color 0.12s;
}

.wl-switcher.open .wl-chevron {
	transform: rotate(180deg);
	color: var(--teal);
}

.wl-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.6rem 1rem;
	cursor: pointer;
	transition: background 0.1s;
	border-bottom: 1px solid var(--border);
}

.wl-item:last-of-type {
	border-bottom: none;
}

.wl-item:hover {
	background: var(--bg-hover);
}

.wl-item.active {
	background: var(--teal-dim);
}

.wl-item-left {
	display: flex;
	align-items: center;
	gap: 0.6rem;
}

.wl-item-check {
	font-size: 10px;
	color: var(--teal);
	opacity: 0;
}

.wl-item.active .wl-item-check {
	opacity: 1;
}

.overlay {
	position: fixed;
	inset: 0;
	z-index: 250;
}
</style>
