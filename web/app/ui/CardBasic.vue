<!--
USAGE

<CardBasic accent-color="teal" badge="Core" title="Feature Title" description="Feature description." />

<CardBasic num="01" title="Pillar" description="Description text." />

<CardBasic num="01" title="Stats" description="Description" accent-color="purple" badge="Pro" />
-->
<script setup>
defineProps({
	title: {
		type: String,
		default: ''
	},
	description: {
		type: String,
		default: ''
	},
	num: {
		type: String,
		default: ''
	},
	accentColor: {
		type: String,
		default: '',
		validator: (v) => ['', 'teal', 'purple', 'gold', 'blue', 'rose'].includes(v)
	},
	badge: {
		type: String,
		default: ''
	}
})
</script>

<template>
	<div class="card-basic">
		<span v-if="badge" class="basic-badge">{{ badge }}</span>

		<div class="basic-stat-row">
			<div v-if="num" class="basic-stat-num">{{ num }}</div>

			<div>
				<div v-if="accentColor && title" :class="['card-basic-title-row', { 'has-badge': badge }]">
					<div :class="['basic-accent', `basic-accent--${accentColor}`]"></div>
					<h3 class="card-basic-title">{{ title }}</h3>
				</div>
				<h3 v-else-if="title" :class="['card-basic-title', { 'has-badge': badge }]">{{ title }}</h3>

				<p v-if="description" class="basic-stat-desc">{{ description }}</p>
			</div>
		</div>
	</div>
</template>

<style scoped>
.card-basic {
	position: relative;
	padding: 1.5rem;
	transition: background 0.15s;
	/* height: 100%; */
}

.card-basic:hover {
	background: var(--bg-2);
}

.card-basic-title-row {
	display: flex;
	align-items: center;
	margin-bottom: 1rem;
	gap: 8px;
}

.card-basic-title-row.has-badge,
.card-basic-title.has-badge {
	margin-right: 2.5rem;
}

.basic-accent {
	width: 2px;
	align-self: stretch;
	flex-shrink: 0;
}

.basic-accent--teal {
	background: var(--teal);
}

.basic-accent--purple {
	background: var(--purple);
}

.basic-accent--gold {
	background: var(--gold);
}

.basic-accent--blue {
	background: var(--blue);
}

.basic-accent--rose {
	background: var(--rose);
}

.card-basic-title {
	font-size: 16px;
	font-weight: 500;
}

.basic-stat-row {
	display: grid;
	grid-template-columns: auto 1fr;
	align-items: center;
	border-bottom: 1px solid var(--border);
}

.basic-stat-row:last-child {
	border-bottom: none;
}

.basic-stat-num {
	font-size: 2rem;
	font-weight: 300;
	letter-spacing: -0.03em;
	color: var(--teal);
	margin-right: 1.5rem;
}

.basic-stat-desc {
	font-family: var(--font-main);
	font-size: 15px;
	color: var(--fg-2);
}

.basic-feature-desc {
	font-family: var(--font-main);
	font-size: 14px;
	color: var(--fg-2);
	line-height: 1.65;
}

.basic-badge {
	position: absolute;
	top: 1.25rem;
	right: 1.25rem;
	font-size: 10px;
	letter-spacing: 0.1em;
	text-transform: uppercase;
	padding: 0.2rem 0.55rem;
	border: 1px solid var(--border);
	color: var(--fg-3);
}
</style>
