<script setup>
import { useWatchlist } from "~/features/watchlist/provider";

const watchlist = useWatchlist();

const props = defineProps({
	symbol: {
		type: String,
		required: true,
	},
});

const emit = defineEmits(['close', 'update']);

const isOpen = ref(false);
const isLoading = ref(false);
const watchlists = ref([]);
const isCreating = ref(false);
const newWatchlistName = ref('');
const newWatchlistInputRef = ref(null);
const newWatchlistId = ref(null);

const symbolUpper = computed(() => props.symbol.toUpperCase());

function open() {
	isOpen.value = true;
	fetchWatchlists();
}

function close() {
	isOpen.value = false;
	isCreating.value = false;
	newWatchlistName.value = '';
	newWatchlistId.value = null;
	emit('close');
}

async function fetchWatchlists() {
	isLoading.value = true;
	try {
		watchlists.value = await watchlist.list(symbolUpper.value);
	} catch (err) {
		console.error('Failed to fetch watchlists:', err);
	} finally {
		isLoading.value = false;
	}
}

function startCreating() {
	isCreating.value = true;
	nextTick(() => {
		newWatchlistInputRef.value?.focus();
	});
}

function cancelCreating() {
	isCreating.value = false;
	newWatchlistName.value = '';
}

async function confirmCreate() {
	if (!newWatchlistName.value.trim()) return;

	try {
		const result = await watchlist.create(newWatchlistName.value.trim());

		if (result) {
			watchlists.value.unshift({
				...result,
				hasStock: false,
			});
			newWatchlistId.value = result.id;
		}

		isCreating.value = false;
		newWatchlistName.value = '';
	} catch (err) {
		console.error('Failed to create watchlist:', err);
	}
}

async function toggleStock(item) {
	try {
		if (item.hasStock) {
			await watchlist.removeItem(item.id, symbolUpper.value);
		} else {
			await watchlist.addItem(item.id, symbolUpper.value);
		}

		// Toggle local state
		item.hasStock = !item.hasStock;
		emit('update', {
			watchlistId: item.id,
			symbol: symbolUpper.value,
			action: item.hasStock ? 'add' : 'remove'
		});
	} catch (err) {
		console.error('Failed to toggle stock:', err);
	}
}

// Handle escape key
onMounted(() => {
	const handleEscape = (e) => {
		if (e.key === 'Escape' && isOpen.value) {
			close();
		}
	};
	document.addEventListener('keydown', handleEscape);
	onUnmounted(() => {
		document.removeEventListener('keydown', handleEscape);
	});
});

defineExpose({ open, close });
</script>

<template>
	<Teleport to="body">
		<Transition name="slider">
			<div v-if="isOpen" class="menu-slider-overlay" @click.self="close">
				<div class="menu-slider">
					<div class="slider-header">
						<div class="slider-title">
							<Icon name="material-symbols:playlist-add" />
							<Text Text variant="h3">Add to Watchlist</Text>
						</div>
						<Button variant="secondary" class="slider-close" @click="close">
							<Icon name="material-symbols:close" />
						</Button>
					</div>

					<div class="slider-content">
						<div class="stock-badge">
							<span class="stock-symbol">{{ symbolUpper }}</span>
						</div>

						<div v-if="isLoading" class="slider-loading">
							<Icon name="material-symbols:progress-activity" class="animate-spin" />
							<Text variant="body">Loading watchlists...</Text>
						</div>

						<div v-else-if="watchlists.length === 0 && !isCreating" class="slider-empty">
							<Icon name="material-symbols:playlist-add-check" />
							<Text variant="body">No watchlists yet</Text>
							<Text variant="label" class="empty-hint">Create your first watchlist below</Text>
						</div>

						<div v-else class="watchlist-list">
							<!-- New watchlist input row (at top when creating) -->
							<div v-if="isCreating" class="watchlist-item watchlist-item--new">
								<div class="watchlist-info">
									<Icon name="material-symbols:playlist-add" class="new-icon" />
									<input ref="newWatchlistInputRef" v-model="newWatchlistName" type="text"
										class="input input--sm" placeholder="Watchlist name"
										@keyup.enter="confirmCreate" @keyup.esc="cancelCreating" />
								</div>
								<Button variant="primary" size="sm" :disabled="!newWatchlistName.trim()"
									@click="confirmCreate">
									<Icon name="material-symbols:check" />
								</Button>
							</div>

							<!-- Existing watchlists -->
							<div v-for="watchlist in watchlists" :key="watchlist.id" class="watchlist-item"
								:class="{ 'is-new': watchlist.id === newWatchlistId }">
								<div class="watchlist-info">
									<Icon name="material-symbols:playlist-play" class="watchlist-icon" />
									<span class="watchlist-name">{{ watchlist.name }}</span>
								</div>
								<Button variant="secondary" size="sm" :class="watchlist.hasStock ? 'btn--success' : ''"
									@click="toggleStock(watchlist)">
									<Icon :name="watchlist.hasStock
										? 'material-symbols:check'
										: 'material-symbols:add'" />
								</Button>
							</div>
						</div>
					</div>

					<div class="slider-footer">
						<Button v-if="!isCreating" wide variant="primary" @click="startCreating">
							<Icon name="material-symbols:add" />
							Create New Watchlist
						</Button>
						<Button v-else wide variant="secondary" @click="cancelCreating">
							<Icon name="material-symbols:close" />
							Cancel
						</Button>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.menu-slider-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.5);
	z-index: 1000;
	display: flex;
	justify-content: flex-end;
}

.menu-slider {
	width: 100%;
	max-width: 420px;
	background: var(--bg);
	border-left: 1px solid var(--border);
	display: flex;
	flex-direction: column;
	height: 100%;
	overflow: hidden;
}

.slider-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 1.25rem 1.5rem;
	border-bottom: 1px solid var(--border);
	background: var(--bg-2);
}

.slider-title {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 14px;
	font-weight: 600;
	letter-spacing: 0.02em;
	color: var(--fg);
	margin: 0;
}

.slider-close {
	width: 32px;
	height: 32px;
	display: flex;
	align-items: center;
	justify-content: center;
	background: transparent;
	border: 1px solid var(--border);
	border-radius: 4px;
	color: var(--fg-3);
	cursor: pointer;
	transition: all var(--transition);
}

.slider-close:hover {
	border-color: var(--border-hi);
	color: var(--fg);
	background: var(--bg-hover);
}

.slider-content {
	flex: 1;
	overflow-y: auto;
	padding: 1.5rem;
}

.stock-badge {
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 1.5rem;
}

.stock-symbol {
	font-size: 24px;
	font-weight: 700;
	letter-spacing: -0.02em;
	color: var(--fg);
	background: var(--bg-2);
	border: 1px solid var(--border-hi);
	padding: 0.5rem 1rem;
	border-radius: 4px;
	font-family: var(--font-main);
}

.slider-loading,
.slider-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 0.75rem;
	padding: 3rem 1rem;
	color: var(--fg-3);
	font-size: 13px;
}

.slider-empty .material-symbols-icon {
	font-size: 48px;
	opacity: 0.3;
}

.empty-hint {
	font-size: 12px;
	color: var(--fg-2);
}

.watchlist-list {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.watchlist-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 1rem;
	padding: 0.875rem 1rem;
	background: var(--bg-2);
	border: 1px solid var(--border);
	border-radius: 4px;
	transition: all var(--transition);
}

.watchlist-item:hover {
	border-color: var(--border-hi);
	background: var(--bg-card);
}

.watchlist-item.is-new {
	border-color: var(--teal-border);
	background: var(--teal-dim);
}

.watchlist-item--new {
	background: var(--bg-card);
	border-style: dashed;
}

.watchlist-info {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	flex: 1;
	min-width: 0;
}

.watchlist-icon,
.new-icon {
	font-size: 20px;
	color: var(--fg-3);
	flex-shrink: 0;
}

.new-icon {
	color: var(--teal);
}

.watchlist-name {
	font-size: 13px;
	font-weight: 500;
	color: var(--fg);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.input--sm {
	flex: 1;
	font-size: 13px;
	padding: 0.5rem 0.75rem;
	background: var(--bg);
	border: 1px solid var(--border-hi);
	border-radius: 4px;
	color: var(--fg);
}

.input--sm:focus {
	outline: none;
	border-color: var(--teal);
}

.btn--success {
	background: var(--teal);
	border: 1px solid var(--teal);
	color: var(--bg);
}

.btn--success:hover {
	background: var(--teal-dim);
	border-color: var(--teal-border);
	color: var(--teal);
}

.slider-footer {
	padding: 1.25rem 1.5rem;
	border-top: 1px solid var(--border);
	background: var(--bg-2);
}

/* Slide animation */
.slider-enter-active,
.slider-leave-active {
	transition: opacity 0.2s ease;
}

.slider-enter-from,
.slider-leave-to {
	opacity: 0;
}

.slider-enter-active .menu-slider,
.slider-leave-active .menu-slider {
	transition: transform 0.25s ease;
}

.slider-enter-from .menu-slider,
.slider-leave-to .menu-slider {
	transform: translateX(100%);
}

.slider-enter-to .menu-slider,
.slider-leave-from .menu-slider {
	transform: translateX(0);
}

/* Spin animation for loading */
@keyframes spin {
	from {
		transform: rotate(0deg);
	}

	to {
		transform: rotate(360deg);
	}
}

.animate-spin {
	animation: spin 1s linear infinite;
}
</style>
