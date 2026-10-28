<script setup>
import { URI } from "#shared/constants/routes";
import { plans, features } from "~/features/homepage/constants/homepage"
import CardPricing from "~/features/homepage/components/CardPricing.vue";
</script>

<template>
	<Section id="hero" width="lg" topMargin="md" bottomMargin="md">
		<div class="hero-split">
			<div class="hero-left">
				<div class="hero-halo" />
				<div class="hero-logo">
					<Branding show="icon" size="lg" />
				</div>
			</div>
			<div class="hero-right">
				<Text variant="hero" tone="green" weight="bold" class="animate-fade-up">HALITE</Text>
				<Text variant="body" tone="muted" class="hero-desc animate-fade-up animate-delay-1">
					Powerful fundamental analysis and intelligent
					watchlists that help you make informed investment
					decisions.
				</Text>
				<div class="hero-actions animate-fade-up animate-delay-2">
					<NuxtLink :to="URI.user.register">
						<Button variant="primary" size="lg">
							Start Free
						</Button>
					</NuxtLink>
					<NuxtLink to="/#features">
						<Button variant="secondary" size="lg">
							Learn More
						</Button>
					</NuxtLink>
				</div>
			</div>
		</div>
	</Section>

	<Section>
		<Container>
			<SectionHeader label="// Features">
				Everything you need to
				<strong>invest smart</strong>
			</SectionHeader>
		</Container>
		<Grid :cols="4" gap="na" bordered>
			<CardBasic v-for="(feature, index) in features" :key="feature.title" :accentColor="feature.accentColor"
				:title="feature.title" :description="feature.description" :num="'0' + (index + 1)" />
		</Grid>
	</Section>

	<Section bgGrid width="lg" topMargin="lg" bottomMargin="lg">
		<div class="cta-logo">
			<Branding show="icon" size="lg" />
		</div>
		<div class="cta-content">
			<Text variant="h2">Ready to invest smarter?</Text>
			<Text variant="body" tone="muted" class="cta-desc">
				Join thousands of investors using HALITE.
			</Text>
			<NuxtLink :to="URI.user.register">
				<Button variant="primary" size="lg">
					Start Free
				</Button>
			</NuxtLink>
		</div>
	</Section>

	<Section width="lg" topMargin="md" bottomMargin="md">
		<SectionHeader label="// Pricing">
			Choose your <strong>plan</strong>
		</SectionHeader>
		<Grid :cols="4">
			<CardPricing v-for="plan in plans" :key="plan.name" v-bind="plan" :class="{
				'pricing-card--premium':
					plan.name === 'Premium'
			}">
				<template #actions>
					<Button :variant="plan.popular
						? 'primary' : 'secondary'" wide>
						{{ plan.buttonText }}
					</Button>
				</template>
			</CardPricing>
		</Grid>
	</Section>

	<Footer />
</template>

<style scoped>
#hero {
	min-height: 100vh;
}

.hero-split {
	display: flex;
	min-height: calc(100vh - 10rem);
}

.hero-left {
	width: 40%;
	background: var(--bg-2);
	display: flex;
	align-items: center;
	justify-content: center;
	position: relative;
	padding: 3rem;
}

.hero-halo {
	position: absolute;
	inset: 0;
	background-image:
		radial-gradient(3px at 50% 50%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 38% 38%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 62% 38%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 38% 62%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 62% 62%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 30% 30%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 70% 30%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 30% 70%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 70% 70%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 25% 50%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 75% 50%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 50% 25%, var(--teal) 50%, transparent 50%),
		radial-gradient(2.5px at 50% 75%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 18% 18%, var(--teal) 50%, transparent 50%),
		radial-gradient(2px at 82% 82%, var(--teal) 50%, transparent 50%);
	background-repeat: no-repeat;
	pointer-events: none;
	opacity: 0.3;
}

.hero-logo {
	transform: scale(4);
	position: relative;
	z-index: 1;
}

.hero-right {
	width: 60%;
	display: flex;
	flex-direction: column;
	justify-content: center;
	padding: 4rem;
}

.hero-desc {
	max-width: 50ch;
	margin-bottom: 2rem;
}

.hero-actions {
	display: flex;
	gap: 1rem;
}

.cta-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	position: relative;
	padding-block: 3rem;
}

.cta-desc {
	margin-bottom: 2rem;
	margin-top: 0.5rem;
}

.cta-logo {
	position: absolute;
	left: -5%;
	top: 50%;
	transform: translateY(-50%) scale(5);
	opacity: 0.15;
	pointer-events: none;
}
</style>

<style>
.pricing-card--premium {
	border-color: var(--gold) !important;
}
</style>
