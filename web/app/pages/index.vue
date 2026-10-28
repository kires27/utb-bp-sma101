<script setup>
import { plans, features } from "~/features/homepage/constants/homepage"
import CardPricing from "~/features/homepage/components/CardPricing.vue";
import HeroSection from "~/features/homepage/components/HeroSection.vue";
</script>

<template>

	<Container gap="lg">
		<HeroSection />

		<Section id="features" width="lg">
			<SectionHeader label="// Features">
				Everything you need to <strong>invest smart</strong>
			</SectionHeader>

			<Grid :cols="4" >
				<CardBasic v-for="feature in features" :key="feature.title" v-bind="feature" />
			</Grid>
		</Section>
		
		<Section id="pricing" width="lg">
			<SectionHeader label="// Pricing">
				Choose your <strong>plan</strong>
			</SectionHeader>

			<Grid :cols="4" >
				<CardPricing v-for="plan in plans" :key="plan.name" v-bind="plan">
					<template #actions>
						<Button :variant="plan.popular ? 'primary' : 'secondary'" wide>
							{{ plan.buttonText }}
						</Button>
					</template>
				</CardPricing>
			</Grid>
		</Section>
	</Container>

	<Footer />
</template>

<style scoped>
#pricing {
	margin-bottom: 5rem;
}
</style>
