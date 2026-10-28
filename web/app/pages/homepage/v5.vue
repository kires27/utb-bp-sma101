<script setup>
import logo from "~/assets/brand/logo.png";
import { URI } from "#shared/constants/routes";

const features = [
	{
		icon: "material-symbols:finance-mode-rounded",
		title: "Deep Fundamentals",
		desc: "Automated ratio computation, peer comparison, and"
			+ " quality scoring across 19 key metrics — no"
			+ " spreadsheet required.",
		accent: "var(--teal)",
	},
	{
		icon: "material-symbols:visibility-rounded",
		title: "Signal Clarity",
		desc: "Industry benchmarks with instant percentile"
			+ " rankings. See exactly where a stock stands"
			+ " against its peers.",
		accent: "var(--purple)",
	},
	{
		icon: "material-symbols:monitoring-rounded",
		title: "Smart Watchlists",
		desc: "Real-time alerts, unified dashboards, and"
			+ " cross-portfolio tracking. Your watchlists,"
			+ " your way.",
		accent: "var(--gold)",
	},
	{
		icon: "material-symbols:calculate-rounded",
		title: "DCF Valuation",
		desc: "Run intrinsic value models with customizable"
			+ " assumptions and sensitivity analysis on"
			+ " any ticker.",
		accent: "var(--blue)",
	},
];

const metrics = [
	{ value: "10K+", label: "Stocks Covered" },
	{ value: "19", label: "Key Metrics" },
	{ value: "50+", label: "Industries" },
	{ value: "99.7%", label: "Uptime" },
];

const floatCards = [
	{
		symbol: "AAPL",
		value: "+2.41%",
		up: true,
		dot: "var(--teal)",
		className: "float--1",
	},
	{
		symbol: "S&P 500",
		value: "5,234",
		up: true,
		dot: "var(--blue)",
		className: "float--2",
	},
	{
		symbol: "Portfolio",
		value: "+12.4k",
		up: true,
		dot: "var(--gold)",
		className: "float--3",
	},
	{
		symbol: "VIX",
		value: "13.42",
		up: false,
		dot: "var(--rose)",
		className: "float--4",
	},
];
</script>

<template>
	<div class="page">
		<!-- Navigation -->
		<nav class="nav" aria-label="Primary">
			<div class="nav-inner">
				<NuxtLink to="/" class="nav-brand" aria-label="HALITE home">
					<img :src="logo" alt="" class="nav-logo" />
					<span class="nav-wordmark">HALITE</span>
				</NuxtLink>
				<div class="nav-links">
					<a href="#features" class="nav-link">Features</a>
					<a href="#metrics" class="nav-link">Metrics</a>
				</div>
				<div class="nav-actions">
					<NuxtLink :to="URI.user.login" class="nav-btn nav-btn--ghost">
						Sign In
					</NuxtLink>
					<NuxtLink :to="URI.user.register" class="nav-btn nav-btn--solid">
						Get Started
					</NuxtLink>
				</div>
			</div>
		</nav>

		<!-- Hero -->
		<section class="hero" aria-label="Hero">
			<div class="hero-bg">
				<div class="nebula nebula--1" aria-hidden="true" />
				<div class="nebula nebula--2" aria-hidden="true" />
				<div class="nebula nebula--3" aria-hidden="true" />
			</div>

			<!-- Floating data cards -->
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
				>{{ card.value }}</span>
			</div>

			<div class="hero-content">
				<div class="hero-emblem">
					<img :src="logo" alt="" class="hero-logo" />
				</div>
				<h1 class="hero-title">
					<span class="hero-title-line">See through</span>
					<span class="hero-title-line hero-title-em">the noise.</span>
				</h1>
				<p class="hero-desc">
					Fundamental analysis, reimagined. Automated ratios, peer
					benchmarking, and intelligent watchlists — everything you
					need to invest with clarity.
				</p>
				<div class="hero-actions">
					<NuxtLink
						:to="URI.user.register"
						class="btn btn--primary"
					>
						Get Started Free
						<Icon
							name="material-symbols:arrow-forward-rounded"
							class="btn-icon"
							aria-hidden="true"
						/>
					</NuxtLink>
					<a href="#features" class="btn btn--ghost">
						Explore Features
					</a>
				</div>
			</div>

			<div class="hero-scroll" aria-hidden="true">
				<span class="scroll-label">Scroll</span>
				<span class="scroll-line" />
			</div>
		</section>

		<!-- Features -->
		<section id="features" class="features" aria-label="Features">
			<div class="section-inner">
				<header class="section-head">
					<span class="section-tag">// Capabilities</span>
					<h2 class="section-title">
						Everything you need to<br />
						<strong>invest with conviction</strong>
					</h2>
				</header>
				<div class="feat-grid">
					<article
						v-for="(f, i) in features"
						:key="f.title"
						class="feat-card"
						tabindex="0"
					>
						<div
							class="feat-accent"
							:style="{ background: f.accent }"
							aria-hidden="true"
						/>
						<div class="feat-body">
							<div
								class="feat-icon-ring"
								:style="{ '--ring': f.accent }"
							>
								<Icon
									:name="f.icon"
									class="feat-icon"
									aria-hidden="true"
								/>
							</div>
							<h3 class="feat-title">{{ f.title }}</h3>
							<p class="feat-desc">{{ f.desc }}</p>
						</div>
					</article>
				</div>
			</div>
		</section>

		<!-- Metrics -->
		<section id="metrics" class="metrics" aria-label="Metrics">
			<div class="metrics-bg" aria-hidden="true" />
			<div class="section-inner">
				<div class="metrics-grid">
					<div
						v-for="m in metrics"
						:key="m.label"
						class="metric-item"
					>
						<span class="metric-value">{{ m.value }}</span>
						<span class="metric-label">{{ m.label }}</span>
					</div>
				</div>
			</div>
		</section>

		<!-- CTA -->
		<section class="cta" aria-label="Call to action">
			<div class="cta-glow-bg" aria-hidden="true" />
			<div class="section-inner">
				<div class="cta-card">
					<div class="cta-watermark" aria-hidden="true">
						<img :src="logo" alt="" />
					</div>
					<div class="cta-content">
						<h2 class="cta-title">
							Ready to see clearly?
						</h2>
						<p class="cta-desc">
							Join thousands of investors using HALITE to make
							smarter, data-driven decisions. No credit card
							required.
						</p>
						<NuxtLink
							:to="URI.user.register"
							class="btn btn--primary btn--lg"
						>
							Start Free Today
							<Icon
								name="material-symbols:arrow-forward-rounded"
								class="btn-icon"
								aria-hidden="true"
							/>
						</NuxtLink>
					</div>
				</div>
			</div>
		</section>

		<!-- Footer -->
		<footer class="footer">
			<div class="section-inner">
				<div class="footer-inner">
					<div class="footer-brand">
						<img :src="logo" alt="" class="footer-logo" />
						<span class="footer-wordmark">HALITE</span>
					</div>
					<nav class="footer-nav" aria-label="Footer">
						<a href="/docs" class="footer-link">Docs</a>
						<a href="/privacy" class="footer-link">Privacy</a>
						<a href="/terms" class="footer-link">Terms</a>
					</nav>
					<p class="footer-copy">
						&copy; {{ new Date().getFullYear() }} HALITE.
						All rights reserved.
					</p>
				</div>
			</div>
		</footer>
	</div>
</template>

<style scoped>
/* ============ PAGE ============ */

.page {
	background: var(--bg);
	color: var(--fg);
	font-family: var(--font-sans);
	overflow-x: hidden;
}

/* ============ NAV ============ */

.nav {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 100;
	background: rgba(12, 12, 15, 0.72);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border-bottom: 1px solid var(--border);
}

.nav-inner {
	max-width: var(--container-max);
	margin: 0 auto;
	display: flex;
	align-items: center;
	height: var(--header-height);
	padding: 0 2rem;
	gap: 2rem;
}

.nav-brand {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	text-decoration: none;
	flex-shrink: 0;
}

.nav-logo {
	width: 22px;
	height: 22px;
}

.nav-wordmark {
	font-family: var(--font-main);
	font-size: 0.875rem;
	font-weight: 700;
	color: var(--fg);
	letter-spacing: 0.04em;
}

.nav-links {
	display: flex;
	gap: 1.75rem;
	margin-left: 1rem;
}

.nav-link {
	font-family: var(--font-main);
	font-size: 0.75rem;
	color: var(--fg-2);
	text-decoration: none;
	letter-spacing: 0.05em;
	text-transform: uppercase;
	transition: color 0.2s;
	padding: 0.25rem 0;
}

.nav-link:hover {
	color: var(--fg);
}

.nav-link:focus-visible {
	outline: 1px solid var(--teal);
	outline-offset: 4px;
}

.nav-actions {
	margin-left: auto;
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.nav-btn {
	font-family: var(--font-main);
	font-size: 0.75rem;
	text-decoration: none;
	padding: 0.45rem 1rem;
	border-radius: 6px;
	transition: all 0.2s;
	letter-spacing: 0.03em;
}

.nav-btn--ghost {
	color: var(--fg-2);
	border: 1px solid transparent;
}

.nav-btn--ghost:hover {
	color: var(--fg);
	background: var(--bg-hover);
}

.nav-btn--ghost:focus-visible {
	outline: 1px solid var(--teal);
	outline-offset: 2px;
}

.nav-btn--solid {
	background: var(--teal);
	color: #000;
	font-weight: 600;
	border: 1px solid var(--teal);
}

.nav-btn--solid:hover {
	filter: brightness(1.15);
}

.nav-btn--solid:focus-visible {
	outline: 1px solid var(--teal);
	outline-offset: 2px;
}

/* ============ BUTTONS (custom) ============ */

.btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.5rem;
	font-family: var(--font-main);
	font-size: 0.8125rem;
	font-weight: 500;
	letter-spacing: 0.04em;
	text-decoration: none;
	padding: 0.7rem 1.5rem;
	border-radius: 10px;
	cursor: pointer;
	transition: all 0.25s ease;
	border: 1px solid transparent;
	white-space: nowrap;
}

.btn-icon {
	font-size: 1.2em;
	transition: transform 0.25s ease;
}

.btn--primary {
	background: var(--teal);
	border-color: var(--teal);
	color: #000;
	font-weight: 600;
}

.btn--primary:hover {
	filter: brightness(1.2);
	transform: translateY(-1px);
	box-shadow: 0 8px 24px rgba(77, 184, 158, 0.25);
}

.btn--primary:hover .btn-icon {
	transform: translateX(3px);
}

.btn--primary:active {
	transform: translateY(0);
	filter: brightness(0.95);
}

.btn--primary:focus-visible {
	outline: 2px solid var(--teal);
	outline-offset: 3px;
}

.btn--ghost {
	background: transparent;
	border-color: var(--border-hi);
	color: var(--fg);
}

.btn--ghost:hover {
	background: var(--bg-hover);
	border-color: var(--border);
	transform: translateY(-1px);
}

.btn--ghost:active {
	transform: translateY(0);
}

.btn--ghost:focus-visible {
	outline: 2px solid var(--border-hi);
	outline-offset: 3px;
}

.btn--lg {
	padding: 0.9rem 2rem;
	font-size: 0.875rem;
}

/* ============ HERO ============ */

.hero {
	position: relative;
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
	padding: var(--header-height) 2rem 4rem;
}

/* Nebula blobs */

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

/* Float cards */

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

/* Hero content */

.hero-content {
	position: relative;
	z-index: 2;
	text-align: center;
	max-width: 700px;
}

.hero-emblem {
	margin-bottom: 1.5rem;
}

.hero-logo {
	width: 52px;
	height: 52px;
	margin: 0 auto;
	filter: drop-shadow(0 0 20px rgba(77, 184, 158, 0.2));
}

.hero-title {
	font-family: var(--font-main);
	font-size: 3.5rem;
	line-height: 1.15;
	font-weight: 300;
	letter-spacing: -0.02em;
	margin-bottom: 1.5rem;
}

.hero-title-line {
	display: block;
}

.hero-title-em {
	color: var(--teal);
	font-weight: 600;
}

.hero-desc {
	font-family: var(--font-sans);
	font-size: 1.0625rem;
	line-height: 1.7;
	color: var(--fg-2);
	max-width: 56ch;
	margin: 0 auto 2.5rem;
}

.hero-actions {
	display: flex;
	gap: 1rem;
	justify-content: center;
	flex-wrap: wrap;
}

/* Scroll indicator */

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
	background: linear-gradient(
		to bottom,
		var(--fg-3),
		transparent
	);
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

/* ============ FEATURES ============ */

.features {
	padding: 6rem 2rem 7rem;
	position: relative;
	background: var(--bg-2);
}

.section-inner {
	max-width: var(--container-max);
	margin: 0 auto;
}

.section-head {
	text-align: center;
	margin-bottom: 4rem;
}

.section-tag {
	display: inline-block;
	font-family: var(--font-main);
	font-size: 0.6875rem;
	color: var(--teal);
	letter-spacing: 0.15em;
	text-transform: uppercase;
	margin-bottom: 1rem;
}

.section-title {
	font-family: var(--font-main);
	font-size: 2.25rem;
	line-height: 1.25;
	font-weight: 300;
	color: var(--fg);
}

.section-title strong {
	font-weight: 600;
	color: var(--teal);
}

.feat-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 1.25rem;
}

.feat-card {
	position: relative;
	display: flex;
	background: var(--bg);
	border: 1px solid var(--border);
	border-radius: 14px;
	overflow: hidden;
	transition: transform 0.3s ease, box-shadow 0.3s ease;
	cursor: default;
}

.feat-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
	border-color: var(--border-hi);
}

.feat-card:focus-visible {
	outline: 2px solid var(--teal);
	outline-offset: 2px;
}

.feat-accent {
	width: 4px;
	flex-shrink: 0;
}

.feat-body {
	padding: 1.75rem 1.75rem 2rem;
}

.feat-icon-ring {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 1px solid var(--border);
	background: var(--bg-2);
	margin-bottom: 1.25rem;
	transition: border-color 0.3s, background 0.3s;
}

.feat-card:hover .feat-icon-ring {
	border-color: var(--ring, var(--border-hi));
	background: color-mix(in srgb, var(--ring, var(--teal)) 8%, var(--bg-2));
}

.feat-icon {
	font-size: 1.25rem;
	color: var(--fg-2);
	transition: color 0.3s;
}

.feat-card:hover .feat-icon {
	color: var(--ring, var(--teal));
}

.feat-title {
	font-family: var(--font-main);
	font-size: 1rem;
	font-weight: 600;
	margin-bottom: 0.5rem;
	color: var(--fg);
}

.feat-desc {
	font-family: var(--font-sans);
	font-size: 0.875rem;
	line-height: 1.65;
	color: var(--fg-2);
	max-width: 42ch;
}

/* ============ METRICS ============ */

.metrics {
	padding: 5rem 2rem;
	position: relative;
	overflow: hidden;
}

.metrics-bg {
	position: absolute;
	inset: 0;
	background: linear-gradient(
		180deg,
		var(--bg-2) 0%,
		var(--bg) 50%,
		var(--bg-2) 100%
	);
	pointer-events: none;
}

.metrics-grid {
	position: relative;
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 2rem;
	text-align: center;
}

.metric-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.4rem;
}

.metric-value {
	font-family: var(--font-main);
	font-size: 3rem;
	font-weight: 600;
	color: var(--fg);
	letter-spacing: -0.02em;
	line-height: 1;
}

.metric-label {
	font-family: var(--font-main);
	font-size: 0.75rem;
	color: var(--fg-3);
	letter-spacing: 0.12em;
	text-transform: uppercase;
}

/* ============ CTA ============ */

.cta {
	padding: 7rem 2rem 8rem;
	position: relative;
	overflow: hidden;
	background: var(--bg-2);
}

.cta-glow-bg {
	position: absolute;
	inset: 0;
	background:
		radial-gradient(
			ellipse 60% 50% at 50% 20%,
			rgba(77, 184, 158, 0.08) 0%,
			transparent 70%
		),
		radial-gradient(
			ellipse 40% 40% at 30% 80%,
			rgba(139, 126, 200, 0.06) 0%,
			transparent 70%
		);
	pointer-events: none;
}

.cta-card {
	position: relative;
	max-width: 600px;
	margin: 0 auto;
	background: rgba(255, 255, 255, 0.02);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border: 1px solid var(--border-hi);
	border-radius: 20px;
	padding: 4rem 3rem;
	text-align: center;
	overflow: hidden;
}

.cta-watermark {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	opacity: 0.04;
	pointer-events: none;
}

.cta-watermark img {
	width: 200px;
	height: auto;
}

.cta-content {
	position: relative;
	z-index: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.cta-title {
	font-family: var(--font-main);
	font-size: 2rem;
	font-weight: 400;
	margin-bottom: 1rem;
	line-height: 1.2;
}

.cta-desc {
	font-family: var(--font-sans);
	font-size: 1rem;
	line-height: 1.7;
	color: var(--fg-2);
	max-width: 44ch;
	margin: 0 auto 2rem;
}

/* ============ FOOTER ============ */

.footer {
	padding: 2rem;
	border-top: 1px solid var(--border);
	background: var(--bg);
}

.footer-inner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 1.5rem;
	flex-wrap: wrap;
}

.footer-brand {
	display: flex;
	align-items: center;
	gap: 0.5rem;
}

.footer-logo {
	width: 18px;
	height: 18px;
}

.footer-wordmark {
	font-family: var(--font-main);
	font-size: 0.8125rem;
	font-weight: 700;
	color: var(--fg);
	letter-spacing: 0.04em;
}

.footer-nav {
	display: flex;
	gap: 1.5rem;
}

.footer-link {
	font-family: var(--font-main);
	font-size: 0.75rem;
	color: var(--fg-2);
	text-decoration: none;
	transition: color 0.2s;
}

.footer-link:hover {
	color: var(--fg);
}

.footer-link:focus-visible {
	outline: 1px solid var(--teal);
	outline-offset: 2px;
}

.footer-copy {
	font-family: var(--font-sans);
	font-size: 0.75rem;
	color: var(--fg-3);
}

/* ============ RESPONSIVE ============ */

@media (max-width: 900px) {
	.hero-title {
		font-size: 2.5rem;
	}

	.feat-grid {
		grid-template-columns: 1fr;
	}

	.metrics-grid {
		grid-template-columns: repeat(2, 1fr);
		gap: 2.5rem;
	}

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
	.nav-links {
		display: none;
	}

	.nav-inner {
		padding: 0 1rem;
		gap: 1rem;
	}

	.nav-btn {
		font-size: 0.6875rem;
		padding: 0.35rem 0.75rem;
	}

	.nav-btn--ghost {
		display: none;
	}

	.hero {
		padding: var(--header-height) 1.25rem 3rem;
	}

	.hero-title {
		font-size: 1.75rem;
	}

	.hero-desc {
		font-size: 0.9375rem;
	}

	.hero-actions {
		flex-direction: column;
		align-items: stretch;
	}

	.hero-actions .btn {
		justify-content: center;
	}

	.hero-scroll {
		display: none;
	}

	.float-card {
		display: none;
	}

	.features {
		padding: 4rem 1.25rem 5rem;
	}

	.section-title {
		font-size: 1.5rem;
	}

	.feat-card:hover {
		transform: none;
	}

	.feat-body {
		padding: 1.5rem;
	}

	.metrics {
		padding: 3rem 1.25rem;
	}

	.metric-value {
		font-size: 2rem;
	}

	.cta {
		padding: 4rem 1.25rem;
	}

	.cta-card {
		padding: 2.5rem 1.5rem;
		border-radius: 16px;
	}

	.cta-title {
		font-size: 1.5rem;
	}

	.footer-inner {
		flex-direction: column;
		text-align: center;
	}

	.footer-nav {
		justify-content: center;
	}

	.btn--lg {
		width: 100%;
		justify-content: center;
	}
}

@media (prefers-reduced-motion: reduce) {
	.nebula,
	.float-card,
	.hero-scroll .scroll-line,
	.hero-logo {
		animation: none;
	}

	.float-card {
		animation: none;
	}

	.feat-card {
		transition: none;
	}

	.feat-card:hover {
		transform: none;
	}

	.btn {
		transition: none;
	}

	.btn:hover {
		transform: none;
	}

	.btn:active {
		transform: none;
	}

	.btn--primary:hover .btn-icon {
		transform: none;
	}
}
</style>
