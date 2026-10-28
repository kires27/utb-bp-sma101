<script setup>
import { ref } from "vue"

const emit = defineEmits(["create", "rename", "remove"])

const showMenu = ref(false)

const HOLD_DURATION = 1200
const isHolding = ref(false)
const holdComplete = ref(false)
let holdTimer = null

function startHold() {
	if (holdComplete.value) return
	isHolding.value = true
	holdTimer = setTimeout(() => {
		holdComplete.value = true
		isHolding.value = false
		emit("remove")
		showMenu.value = false
		setTimeout(() => {
			holdComplete.value = false
		}, 150)
	}, HOLD_DURATION)
}

function cancelHold() {
	isHolding.value = false
	clearTimeout(holdTimer)
}
</script>

<template>
	<div class="menu-wrap" @mouseenter="showMenu = true" @mouseleave="showMenu = false">
		<button class="icon-btn" style="color: var(--fg);">
			<Icon name="mage:dots" size="22" />
		</button>
		<DropdownMenu align="end" :open="showMenu">
			<button class="menu-item" @click="emit('create')">Create Watchlist</button>
			<button class="menu-item" @click="emit('rename')">Rename Watchlist</button>
			<button
				class="danger-btn"
				:class="{ holding: isHolding }"
				@pointerdown="startHold"
				@pointerup="cancelHold"
				@pointerleave="cancelHold"
				@pointercancel="cancelHold"
				@contextmenu.prevent
				@click.prevent
			>
				<span class="danger-btn__fill" :style="{ '--hold-duration': `${HOLD_DURATION}ms` }" />
				<span class="danger-btn__label">Delete Watchlist</span>
			</button>
		</DropdownMenu>
	</div>
</template>

<style scoped>
.menu-wrap {
	position: relative;
}

.icon-btn {
	background: none;
	border: none;
	padding: 0;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	height: 33px;
}

.icon-btn:hover {
	filter: brightness(1.2);
	background-color: var(--bg-hover);
}

.menu-item {
	background: transparent;
	border: none;
	padding: 0.6rem 1rem;
	color: var(--fg-2);
	display: flex;
	position: relative;
	gap: 0.5rem;
	cursor: pointer;
	width: 100%;
	box-sizing: border-box;
	font-family: var(--font-main);
	font-size: 12px;
	transition: background 0.15s, color 0.15s;
}

.menu-item:hover,
.menu-item:focus {
	background: var(--bg-hover);
	color: var(--fg);
}

.menu-item:focus,
.menu-item:active {
	background: var(--bg-2);
	outline: none;
}

.menu-item::before {
	content: '';
	position: absolute;
	top: 50%;
	left: 0;
	transform: translateY(-50%);
	width: 2px;
	height: 0;
	background: var(--teal);
	transition: height 0.15s;
}

.menu-item:focus::before,
.menu-item:focus:active::before {
	height: 60%;
}

.danger-btn {
	background: transparent;
	border: none;
	padding: 0.6rem 1rem;
	color: var(--rose);
	display: flex;
	position: relative;
	gap: 0.5rem;
	cursor: pointer;
	width: 100%;
	box-sizing: border-box;
	font-family: var(--font-main);
	font-size: 12px;
	transition: background 0.15s, color 0.15s;
	overflow: hidden;
	text-align: left;
	user-select: none;
	-webkit-user-select: none;
	-webkit-touch-callout: none;
	touch-action: none;
}

.danger-btn__label {
	position: relative;
	z-index: 1;
}

.danger-btn__fill {
	position: absolute;
	inset: 0;
	width: 0%;
	background: color-mix(in srgb, var(--rose) 25%, transparent);
	transition: width 0s linear;
	pointer-events: none;
}

.danger-btn.holding .danger-btn__fill {
	width: 100%;
	transition: width var(--hold-duration) cubic-bezier(0.15, 0.65, 0.5, 0.85);
}
</style>