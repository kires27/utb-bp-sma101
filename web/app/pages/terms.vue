<script setup>
useHead({ title: "MEIC — Terms of Service" })

definePageMeta({
	options: {
		footerFullSize: true,
	},
})
</script>

<template>
	<Container>
		<Section id="intro" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// Terms of Service">
				Using MEIC responsibly
			</SectionHeader>

			<Text variant="body-sm" tone="muted">
				Last updated: January 2026
			</Text>

			<br />

			<Text variant="body">
				These Terms of Service govern your use of the MEIC platform. By
				accessing or using MEIC, you agree to these terms. If you do not agree,
				please do not use the service.
			</Text>
		</Section>

		<Section id="account" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 01">
				Account Registration
			</SectionHeader>

			<Text variant="body">
				You are responsible for maintaining the confidentiality of your account
				credentials. You must provide accurate and complete information when
				creating an account. You may not use another person's account without
				permission.
			</Text>

			<Text variant="body">
				You must be at least 18 years old to use the platform. By creating an
				account, you represent that you meet this requirement.
			</Text>
		</Section>

		<Section id="use" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 02">
				Acceptable Use
			</SectionHeader>

			<Text variant="body">
				You agree to use MEIC only for lawful purposes and in accordance with
				these terms. You may not use the platform to violate any laws,
				infringe on intellectual property rights, or distribute harmful
				content.
			</Text>

			<Text variant="body">
				You may not attempt to gain unauthorized access to any part of the
				platform, interfere with its operation, or scrape data in a manner
				that degrades service performance.
			</Text>
		</Section>

		<Section id="disclaimer" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 03">
				No Investment Advice
			</SectionHeader>

			<Text variant="body">
				MEIC provides financial data, analysis tools, and valuation models for
				informational and educational purposes only. Nothing on the platform
				constitutes investment advice, a recommendation, or a solicitation to
				buy or sell securities.
			</Text>

			<Text variant="body">
				All investment decisions are your own responsibility. Past performance
				does not guarantee future results. You should consult a qualified
				financial advisor before making investment decisions.
			</Text>
		</Section>

		<Section id="subscription" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 04">
				Subscriptions & Billing
			</SectionHeader>

			<Text variant="body">
				Certain features require a paid subscription. Subscription fees are
				billed in advance on a monthly or annual basis, depending on your
				selected plan. You may cancel your subscription at any time through
				your settings page.
			</Text>

			<Text variant="body">
				Upon cancellation, you retain access to paid features until the end of
				the current billing period. No refunds are provided for partial
				periods.
			</Text>
		</Section>

		<Section id="termination" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 05">
				Termination
			</SectionHeader>

			<Text variant="body">
				We reserve the right to suspend or terminate your access to the
				platform if you violate these terms. You may delete your account at
				any time through your settings page.
			</Text>

			<Text variant="body">
				Upon termination, your access to the platform and your data will be
				removed within 30 days, except as required to comply with legal
				obligations.
			</Text>
		</Section>

		<Section id="liability" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 06">
				Limitation of Liability
			</SectionHeader>

			<Text variant="body">
				MEIC is provided "as is" without warranties of any kind, either
				express or implied. We are not liable for any damages arising from
				your use of the platform, including but not limited to financial
				losses from investment decisions made using our tools.
			</Text>
		</Section>

		<Section id="contact" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 07">
				Contact
			</SectionHeader>

			<Text variant="body">
				If you have questions about these terms, please contact us at
				<strong>legal@meic.com</strong>.
			</Text>
		</Section>
	</Container>
	<Footer />
</template>
