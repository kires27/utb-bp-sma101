<script setup>
import logo from "~/assets/brand/logo.png"
import { URI } from "~~/shared/constants/routes";

defineProps({
	fullMode: {
		type: Boolean,
		default: true,
	},
})

const email = ref("")

const footerLinks = {
	product: [
		{ label: "List of symbols", to: URI.listStocks },
		{ label: "Features", to: "/#features" },
		{ label: "Pricing", to: "/#pricing" },
		{ label: "Roadmap", to: "#" },
	],
	resources: [
		{ label: "Help Center", to: "#" },
		{ label: "Tutorials", to: "#" },
		{ label: "Market Data", to: "#" },
		{ label: "API Docs", to: "#" },
	],
	company: [
		{ label: "About", to: URI.about },
		{ label: "Blog", to: "#" },
		{ label: "Contact", to: "#" },
		{ label: "Support", to: "#" },
	],
}

const year = new Date().getFullYear();
</script>

<template>
	<div class="footer">
		<!-- <div v-if="fullMode"> -->
		<div v-if="false">
			<Section width="lg" topMargin="sm" bottomMargin="sm" class="footer-top">
				<div class="footer-col--brand">
					<Branding show="name" />

					<Text variant="body-sm" tone="muted" class="footer-desc">
						Make investing easy with powerful fundamental analysis tools and smart
						watchlists. Track, analyze, and grow your portfolio.
					</Text>
					<div style="display: flex;">
						<Input v-model="email" type="email" placeholder="your@email.com" has-button>
						</Input>
						<Button size="md">
							<Icon name="material-symbols:search" />
						</Button>
					</div>
				</div>

				<div class="footer-col">
					<Text variant="label" class="footer-col-title">Product</Text>
					<ul class="footer-links">
						<li v-for="link in footerLinks.product" :key="link.label">
							<NuxtLink :to="link.to">
								<Text variant="body-sm" tone="muted" link>{{ link.label }}</Text>
							</NuxtLink>
						</li>
					</ul>
				</div>

				<div class="footer-col">
					<Text variant="label" class="footer-col-title">Resources</Text>
					<ul class="footer-links">
						<li v-for="link in footerLinks.resources" :key="link.label">
							<NuxtLink :to="link.to">
								<Text variant="body-sm" tone="muted" link>{{ link.label }}</Text>
							</NuxtLink>
						</li>
					</ul>
				</div>

				<div class="footer-col footer-col--last">
					<Text variant="label" class="footer-col-title">Company</Text>
					<ul class="footer-links">
						<li v-for="link in footerLinks.company" :key="link.label">
							<NuxtLink :to="link.to">
								<Text variant="body-sm" tone="muted" link>{{ link.label }}</Text>
							</NuxtLink>
						</li>
					</ul>
				</div>
			</Section>
		</div>

		<Section class="footer-bottom">
			<Text variant="body-sm" tone="muted">©{{ year }} Halite. All rights reserved.</Text>
			<div class="footer-legal">
				<NuxtLink :to="URI.privacy">
					<Text variant="body-sm" tone="muted" link>Privacy Policy</Text>
				</NuxtLink>
				<NuxtLink :to="URI.terms">
					<Text variant="body-sm" tone="muted" link>Terms of Service</Text>
				</NuxtLink>
				<NuxtLink :to="URI.disclaimer">
					<Text variant="body-sm" tone="muted" link>Disclaimer</Text>
				</NuxtLink>
			</div>
		</Section>
	</div>
</template>

<style scoped>
.footer {
	border-top: 1px solid var(--border);
	display: flex;
	flex-direction: column;
	align-items: center;
}

.footer-top {
	display: flex;
	justify-content: space-between;
}

.footer-col--brand {
	width: 300px;
}

.footer-col {
	width: 150px;
}


.footer-desc {
	margin-bottom: 1.25rem;
}

.footer-col-title {
	display: block;
	margin-bottom: 1.25rem;
}

.footer-links {
	display: flex;
	flex-direction: column;
	gap: 0.6rem;
}

.footer-bottom {
	border-top: 1px solid var(--border);
	padding: 1rem 3rem;
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
}

.footer-legal {
	display: flex;
	gap: 1.5rem;
}
</style>
