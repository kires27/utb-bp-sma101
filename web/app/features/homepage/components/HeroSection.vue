<script setup>
import logo from "~/assets/brand/logo.png";
import { URI } from "#shared/constants/routes";
import { floatCards } from "~/features/homepage/constants/homepage";
</script>

<template>
	<section class="hero" aria-label="Hero">
		<div class="hero-bg" aria-hidden="true">
			<div class="nebula nebula--1" />
			<div class="nebula nebula--2" />
			<div class="nebula nebula--3" />
		</div>

		<div class="hero-emblem" aria-hidden="true">
			<img :src="logo" alt="" class="hero-logo" />
		</div>

		<div
			v-for="card in floatCards"
			:key="card.symbol"
			class="float-card"
			:class="card.className"
			aria-hidden="true"
		>
			<span class="float-dot" :style="{ background: card.dot }" />
			<span class="float-symbol">{{ card.symbol }}</span>
			<span
				class="float-value"
				:class="{ 'float-value--up': card.up, 'float-value--dn': !card.up }"
			>
				{{ card.value }}
			</span>
		</div>

		<div class="hero-content">
			<span class="hero-name">HALITE</span>

			
			<Text variant="hero" weight="light">
				<span class="hero-title-line">See through</span>
				<span class="hero-title-line hero-title-em">the noise.</span>
			</Text>

			<Text variant="body" tone="muted" class="hero-desc">
				Fundamental analysis, reimagined. Automated ratios, peer
				benchmarking, and intelligent watchlists — everything you need
				to invest with clarity.
			</Text>

		</div>

		<div class="hero-scroll" aria-hidden="true">
			<span class="scroll-label">Scroll</span>
			<span class="scroll-line" />
		</div>
	</section>
</template>

<style scoped>
.hero {
	position: relative;
	min-height: 95vh;
	width: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
	padding: calc(var(--header-height) / 2) 2rem 4rem;
}

.hero-name {
	font-size: 8rem;
	color: var(--fg);
	font-weight: 800;

}

.hero-bg {
	position: absolute;
	inset: 0;
	pointer-events: none;
	overflow: hidden;
}

.nebula {
	position: absolute;
	border-radius: 50%;
	filter: blur(100px);
	opacity: 0.3;
}

.nebula--1 {
	width: 600px;
	height: 600px;
	top: -15%;
	right: -10%;
	background: radial-gradient(
		circle,
		var(--teal) 0%,
		var(--purple) 50%,
		transparent 70%
	);
	animation: drift 20s ease-in-out infinite alternate;
}

.nebula--2 {
	width: 500px;
	height: 500px;
	bottom: -10%;
	left: -8%;
	background: radial-gradient(
		circle,
		var(--gold) 0%,
		var(--rose) 40%,
		transparent 70%
	);
	animation: drift 25s ease-in-out infinite alternate-reverse;
}

.nebula--3 {
	width: 400px;
	height: 400px;
	top: 40%;
	left: 50%;
	background: radial-gradient(
		circle,
		var(--blue) 0%,
		var(--teal) 40%,
		transparent 70%
	);
	animation: drift 18s ease-in-out infinite alternate;
}

@keyframes drift {
	0% {
		transform: translate(0, 0) scale(1);
	}
	100% {
		transform: translate(40px, -30px) scale(1.08);
	}
}

.float-card {
	position: absolute;
	z-index: 1;
	display: flex;
	align-items: center;
	gap: 0.6rem;
	background: rgba(255, 255, 255, 0.03);
	backdrop-filter: blur(16px);
	-webkit-backdrop-filter: blur(16px);
	border: 1px solid var(--border);
	border-radius: 10px;
	padding: 0.6rem 1rem;
	pointer-events: none;
}

.float-dot {
	width: 7px;
	height: 7px;
	border-radius: 50%;
	flex-shrink: 0;
}

.float-symbol {
	font-family: var(--font-main);
	font-size: 0.6875rem;
	font-weight: 600;
	color: var(--fg-2);
	letter-spacing: 0.03em;
}

.float-value {
	font-family: var(--font-main);
	font-size: 0.75rem;
	font-weight: 500;
}

.float-value--up {
	color: var(--teal);
}

.float-value--dn {
	color: var(--rose);
}

.float--1 {
	top: 18%;
	right: 8%;
	animation: float 6s ease-in-out infinite;
}

.float--2 {
	top: 55%;
	right: 5%;
	animation: float 8s ease-in-out infinite 1.5s;
}

.float--3 {
	bottom: 22%;
	left: 6%;
	animation: float 7s ease-in-out infinite 0.75s;
}

.float--4 {
	top: 30%;
	left: 5%;
	animation: float 9s ease-in-out infinite 2.5s;
}

@keyframes float {
	0%, 100% {
		transform: translateY(0);
	}
	50% {
		transform: translateY(-14px);
	}
}

.hero-content {
	position: relative;
	z-index: 2;
	text-align: center;
	max-width: 700px;
}

.hero-emblem {
	position: absolute;
	inset: 0;
	z-index: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	pointer-events: none;
}

.hero-logo {
	width: 90vmin;
	height: 90vmin;
	opacity: 0.1;
	mix-blend-mode: screen;
	filter: invert(1) sepia(0.6) saturate(3) hue-rotate(140deg) ;
	will-change: transform;
	animation: drift 40s ease-in-out infinite alternate;
}

.hero::before {
	content: "";
	position: absolute;
	inset: 15%;
	background: var(--purple);
	filter: blur(100px);
	opacity: 0.15;
	pointer-events: none;
}

.hero-title-line {
	display: block;
}

.hero-title-em {
	color: var(--teal);
	font-weight: 600;
}

.hero-desc {
	max-width: 56ch;
	margin: 1.5rem auto 2.5rem;
}

.hero-actions {
	display: flex;
	gap: 1rem;
	justify-content: center;
	flex-wrap: wrap;
}

.btn-icon {
	font-size: 1.2em;
}

.hero-scroll {
	position: absolute;
	bottom: 2.5rem;
	left: 50%;
	transform: translateX(-50%);
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
	opacity: 0.4;
}

.scroll-label {
	font-family: var(--font-main);
	font-size: 0.625rem;
	text-transform: uppercase;
	letter-spacing: 0.15em;
	color: var(--fg-3);
}

.scroll-line {
	width: 1px;
	height: 32px;
	background: linear-gradient(to bottom, var(--fg-3), transparent);
	animation: scrollPulse 2s ease-in-out infinite;
}

@keyframes scrollPulse {
	0%, 100% {
		opacity: 1;
		transform: scaleY(1);
	}
	50% {
		opacity: 0.3;
		transform: scaleY(0.6);
	}
}

@media (max-width: 900px) {
	.float--3,
	.float--4 {
		display: none;
	}

	.float--1 {
		top: 12%;
		right: 4%;
	}

	.float--2 {
		top: 50%;
		right: 3%;
	}
}

@media (max-width: 640px) {
	.hero {
		padding: 2rem 1.25rem 3rem;
	}

	.hero-desc {
		font-size: 0.9375rem;
	}

	.hero-actions {
		flex-direction: column;
		align-items: stretch;
	}

	.hero-actions :deep(.btn) {
		width: 100%;
		justify-content: center;
	}

	.hero-scroll {
		display: none;
	}

	.hero-logo {
		width: 100vmin;
		height: 100vmin;
		opacity: 0.07;
	}

	.float-card {
		display: none;
	}
}

@media (prefers-reduced-motion: reduce) {
	.nebula,
	.float-card,
	.hero-logo,
	.hero-scroll .scroll-line {
		animation: none;
	}
}
</style>
