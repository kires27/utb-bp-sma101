<script setup>
useHead({ title: "MEIC — Disclaimer" })

definePageMeta({
	options: {
		footerFullSize: true,
	},
})
</script>

<template>
	<Container>
		<Section id="intro" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// Disclaimer">
				Informational purposes only
			</SectionHeader>

			<Text variant="body-sm" tone="muted">
				Last updated: January 2026
			</Text>

			<br />

			<Text variant="body">
				This disclaimer governs your use of the MEIC platform. The information
				provided on MEIC is for general informational and educational purposes
				only. By using the platform, you acknowledge and agree to this
				disclaimer.
			</Text>
		</Section>

		<Section id="advice" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 01">
				Not Financial Advice
			</SectionHeader>

			<Text variant="body">
				MEIC does not provide financial advice, investment advice, or
				recommendations of any kind. The data, analysis, and valuation models
				presented on the platform are for informational purposes only and
				should not be construed as a solicitation or offer to buy or sell any
				securities.
			</Text>

			<Text variant="body">
				You should not rely on any information on MEIC as a substitute for
				professional financial advice. Always consult a qualified financial
				advisor before making investment decisions.
			</Text>
		</Section>

		<Section id="accuracy" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 02">
				Data Accuracy
			</SectionHeader>

			<Text variant="body">
				We strive to provide accurate and up-to-date information, but we make
				no representations or warranties regarding the completeness, accuracy,
				or reliability of any data on the platform. Financial data may be
				delayed, incomplete, or contain errors.
			</Text>

			<Text variant="body">
				Data is sourced from public filings and third-party providers. We
				recommend verifying any critical information against official sources
				before making decisions based on it.
			</Text>
		</Section>

		<Section id="liability" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 03">
				Limitation of Liability
			</SectionHeader>

			<Text variant="body">
				To the fullest extent permitted by law, MEIC and its operators shall
				not be liable for any direct, indirect, incidental, consequential, or
				special damages arising out of or in connection with your use of the
				platform, including any financial losses.
			</Text>

			<Text variant="body">
				This limitation applies regardless of the theory of liability and
				whether or not we have been advised of the possibility of such
				damages.
			</Text>
		</Section>

		<Section id="external" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 04">
				External Links
			</SectionHeader>

			<Text variant="body">
				The platform may contain links to third-party websites or resources.
				We are not responsible for the content, accuracy, or practices of
				these external sites. Accessing them is at your own risk.
			</Text>
		</Section>

		<Section id="changes" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 05">
				Changes to This Disclaimer
			</SectionHeader>

			<Text variant="body">
				We reserve the right to update this disclaimer at any time. Changes
				will be posted on this page and will take effect immediately upon
				publication. Your continued use of the platform after changes
				constitutes acceptance of the updated disclaimer.
			</Text>
		</Section>

		<Section id="contact" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 06">
				Contact
			</SectionHeader>

			<Text variant="body">
				If you have questions about this disclaimer, please contact us at
				<strong>legal@meic.com</strong>.
			</Text>
		</Section>
	</Container>
	<Footer />
</template>
