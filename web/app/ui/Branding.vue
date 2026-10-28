<script setup>
import { URI } from "~~/shared/constants/routes"
import logo from "~/assets/brand/logo.png"

defineProps({
	size: {
		type: String,
		default: "md",
		validator: (v) => ["sm", "md", "lg"].includes(v),
	},
	show: {
		type: String,
		default: "icon",
		validator: (v) => ["icon", "name"].includes(v),
	}
})

const textVariant = { sm: "body", md: "h3", lg: "h2" };
</script>

<template>
	<NuxtLink :to="URI.home" :class="['logo', `logo--${size}`]">
		<div v-if="show != 'name'" class="logo-mark" :style="{ '--mask-url': `url(${logo})` }" />

		<Text v-if="show != 'icon'" :variant="textVariant[size]" weight="bold">HALITE</Text>
	</NuxtLink>
</template>

<style scoped>
.text {
	word-spacing: 2px;
}

.logo {
	position: relative;
	display: inline-flex;
	align-items: center;
}

.logo-mark {
	position: absolute;
	left: 2px;
	z-index: 0;
	display: block;
	flex-shrink: 0;
	width: 36px;
	height: 36px;
	object-fit: contain;
	background-color: white;

	-webkit-mask: var(--mask-url) no-repeat center;
	mask: var(--mask-url) no-repeat center;

	-webkit-mask-size: contain;
	mask-size: contain;
}

.logo--sm .logo-mark {
	width: 28px;
	height: 28px;
}

.logo--lg .logo-mark {
	width: 48px;
	height: 48px;
}
</style>
