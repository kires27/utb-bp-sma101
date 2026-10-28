<script setup>
useHead({
	title: 'MEIC — About Us'
})

definePageMeta({
	options: {
		footerFullSize: true
	}
})

const pillars = [
	{ num: '01', title: 'Financial Analysis', description: 'Evaluation of company fundamentals using a structured set of financial metrics. Each metric is compared to the industry median to provide a clear view of relative performance.' },
	{ num: '02', title: 'Intrinsic Value', description: 'A discounted cash flow model estimating the long-term value of the business based on historical cash flow growth and conservative assumptions.' },
	{ num: '03', title: 'Company Profile', description: 'A concise qualitative overview providing context about the company\'s business, leadership, and competitive environment.' },
	{ num: '04', title: 'Watchlist', description: 'Watchlist provides an ultimate overview by combining financial data, intrinsic value estimates, and smart filters to help investors monitor companies and spot opportunities at a glance.' }
]

const statItems = [
	{ num: '', title: 'Simple', description: 'Clean interface, no clutter. Everything you need, nothing you don\'t.' },
	{ num: '', title: 'Affordable', description: 'Starting at just €3/month. Professional tools shouldn\'t cost a fortune.' },
	{ num: '', title: 'Effective', description: 'Focus on what matters. Fundamental data, smart alerts, real results.' }
]
</script>

<template>
	<Container gap="lg">
		<Section id="about" width="lg", top-margin="md">
			<Grid :cols="2" gap="lg" :bordered="false">
				<div class="about-text">
					<SectionHeader label="// About">
						Built by investors, <strong>for investors</strong>
					</SectionHeader>

					<Text variant="body">
						We're a small team of passionate investors who grew tired of the complexity and confusion
						in the investing world.
						<strong>Scattered data, expensive tools, and overwhelming information</strong>
						made it difficult to make confident decisions.
					</Text>

					<Text variant="body">
						So we built MEIC for ourselves — a simple, powerful tool that cuts through the noise
						and focuses on what really matters: <strong>fundamental analysis</strong> and
						<strong>smart watchlists</strong>. No overwhelming dashboards, no hidden fees.
					</Text>

					<Text variant="body">
						After seeing real results, we made MEIC publicly available — to help everyone
						invest without the headaches.
					</Text>

					<PullQuote author="The MEIC Team">
						"We built the tool we wished existed. Now it's here for you too."
					</PullQuote>
				</div>
				<Grid :cols="1" gap="sm" alignContent="start">
					<CardBasic v-for="stat in statItems" v-bind="stat" />
				</Grid>
			</Grid>
		</Section>

		<Section id="mission" width="lg">
			<SectionHeader label="// Mission">
				Clarity, Structure, and Insight
			</SectionHeader>

			<Text variant="body">
				Our mission is to make fundamental company analysis clear, structured, and understandable. The
				platform
				is designed around the principles of clarity, simplicity, and grounded positivism — focusing on
				observable financial data and transparent analytical methods. The goal is to help investors evaluate
				companies through consistent financial metrics and structured analysis rather than subjective
				interpretation.
			</Text>

			<PullQuote author="The MEIC Team">
				"Focus on observable financial data, not subjective interpretation."
			</PullQuote>
		</Section>

		<Section id="framework" width="lg">
			<SectionHeader label="// Analysis Framework">
				Four Pillars of Company Evaluation
			</SectionHeader>

			<Grid :cols="1">
				<CardBasic v-for="entry in pillars" v-bind="entry" />
			</Grid>
		</Section>

		<Section id="methodology" width="lg">
			<SectionHeader label="// Methodology">
				How We Analyze Companies
			</SectionHeader>

			<Text variant="body">
				The analytical model is based on several core principles. Financial metrics are evaluated relative
				to
				industry averages in order to provide meaningful comparisons between companies operating in similar
				environments. A composite financial score is derived from normalized metrics and weighted according
				to
				their relevance to long-term financial performance. This score summarizes the overall financial
				position
				of the company while preserving transparency through the individual underlying metrics.
			</Text>
			<br />
			<Text variant="body">
				Intrinsic value estimates are calculated using discounted future cash flows and conservative growth
				assumptions, allowing the model to focus on long-term business performance rather than short-term
				market
				fluctuations.
			</Text>
		</Section>

		<Section id="note" width="lg" bottom-margin="md">
			<SectionHeader label="// Important Note">
				Informational Purposes Only
			</SectionHeader>

			<Text variant="body">
				This platform provides structured financial analysis and valuation models for informational
				purposes. It
				does not constitute investment advice. Investment decisions should always be made based on
				independent
				research and individual judgment.
			</Text>
		</Section>
	</Container>
	<Footer></Footer>
</template>

<style scoped>
.about-text>* {
	margin-bottom: 1.25rem;
}
</style>