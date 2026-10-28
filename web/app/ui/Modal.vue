<script setup>
const props = defineProps({
	open: Boolean,
})

const emit = defineEmits(['close'])

function onKeydown(e) {
	if (e.key === 'Escape') emit('close');
}

watch(() => props.open, (val) => {
	if (val) document.addEventListener('keydown', onKeydown);
	else document.removeEventListener('keydown', onKeydown);
});

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown));
</script>

<template>
	<Teleport to="body">
		<Transition name="modal">
			<div v-if="open" class="modal-overlay" @click.self="emit('close')">
				<div class="modal-panel">
					<button class="modal-close" type="button" @click="emit('close')">
						<Icon name="material-symbols:close" />
					</button>
					<slot />
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.modal-overlay {
	position: fixed;
	inset: 0;
	z-index: 1000;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
}

.modal-panel {
	position: relative;
	background: var(--bg-card);
	border: 1px solid var(--border-hi);
	border-radius: 8px;
	min-width: 500px;
	max-width: 90vw;
	height: 500px;
}

.modal-close {
	position: absolute;
	top: 1rem;
	right: 1rem;
	background: none;
	border: none;
	color: var(--fg-3);
	cursor: pointer;
	padding: 0.25rem;
	display: flex;
	align-items: center;
	justify-content: center;
}

.modal-close:hover {
	color: var(--fg);
}

.modal-enter-active,
.modal-leave-active {
	transition: opacity 0.2s ease;
}

.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
	transition: transform 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
	opacity: 0;
}

.modal-enter-from .modal-panel {
	transform: scale(0.95) translateY(-10px);
}

.modal-leave-to .modal-panel {
	transform: scale(0.95) translateY(-10px);
}
</style>
