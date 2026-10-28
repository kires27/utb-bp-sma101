<script setup>
import { computed } from 'vue'

const props = defineProps({
	title: { type: String, required: true },
	size: { type: Number, default: 64 },
	round: { type: Boolean, default: false },
	gradient: { type: Boolean, default: false },
})

// Generate deterministic color
function stringToColor(str) {
	let hash = 0
	for (let i = 0; i < str.length; i++) {
		hash = str.charCodeAt(i) + ((hash << 5) - hash)
	}
	return `hsl(${hash % 360}, 70%, 60%)`
}

// Complementary gradient color
function complementColor(hue) {
	const complementHue = (hue + 40) % 360
	return `hsl(${complementHue}, 70%, 60%)`
}

const letter = computed(() => props.title.charAt(0).toUpperCase())

const backgroundStyle = computed(() => {
	const baseColor = stringToColor(props.title)
	if (!props.gradient) return { '--bg': baseColor }

	const hueMatch = baseColor.match(/\d+/)
	const hue = hueMatch ? parseInt(hueMatch[0]) : 200
	const gradientColor = complementColor(hue)

	return {
		'--bg1': baseColor,
		'--bg2': gradientColor,
	}
})
</script>

<template>
	<div class="auto-icon" :class="{ round }" :style="{
		width: `${size}px`,
		height: `${size}px`,
		fontSize: `${size / 1.5}px`,
		...backgroundStyle,
	}">
		{{ letter }}
	</div>
</template>

<style scoped>
.auto-icon {
	display: flex;
	align-items: center;
	justify-content: center;
	color: white;
	font-weight: bold;
	user-select: none;
	/* border-radius: 8px; */
	background: var(--bg, hsl(210, 70%, 60%));
	background: linear-gradient(135deg, var(--bg1, var(--bg)), var(--bg2, var(--bg)));
}

.auto-icon.round {
	border-radius: 50%;
}
</style>
