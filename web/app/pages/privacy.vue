<script setup>
useHead({ title: "MEIC — Privacy Policy" })

definePageMeta({
	options: {
		footerFullSize: true,
	},
})
</script>

<template>
	<Container>
		<Section id="intro" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// Privacy Policy">
				Your data, your control
			</SectionHeader>

			<Text variant="body-sm" tone="muted">
				Last updated: January 2026
			</Text>

			<br />

			<Text variant="body">
				This Privacy Policy explains how MEIC collects, uses, and protects your
				personal information when you use our platform. We take your privacy
				seriously and are committed to being transparent about our practices.
			</Text>
		</Section>

		<Section id="information" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 01">
				Information We Collect
			</SectionHeader>

			<Text variant="body">
				<strong>Account Information.</strong>
				When you create an account, we collect your email address and a
				password. You may also choose to provide a display name.
			</Text>

			<Text variant="body">
				<strong>Usage Data.</strong>
				We collect anonymous information about how you interact with the
				platform, such as the pages you visit, features you use, and the stocks
				you search for. This helps us improve the service.
			</Text>

			<Text variant="body">
				<strong>Cookies.</strong>
				We use essential cookies to keep you logged in and maintain session
				state. No third-party tracking cookies are used.
			</Text>
		</Section>

		<Section id="use" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 02">
				How We Use Your Information
			</SectionHeader>

			<Text variant="body">
				We use the information we collect to operate, maintain, and improve the
				platform. This includes providing you with access to features,
				responding to inquiries, sending service-related communications, and
				analyzing usage patterns to enhance the user experience.
			</Text>

			<Text variant="body">
				We do not sell your personal information to third parties. We do not use
				your data for advertising or marketing purposes outside of the platform
				itself.
			</Text>
		</Section>

		<Section id="sharing" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 03">
				Data Sharing
			</SectionHeader>

			<Text variant="body">
				We may share your information with service providers who help us operate
				the platform (hosting, database, email delivery). These providers are
				contractually bound to protect your data and use it only for the
				services they provide to us.
			</Text>

			<Text variant="body">
				We may disclose your information if required by law or in response to a
				valid legal request. We will notify you if such a request is made,
				unless prohibited by law.
			</Text>
		</Section>

		<Section id="security" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 04">
				Data Security
			</SectionHeader>

			<Text variant="body">
				We implement industry-standard security measures to protect your data.
				All connections to the platform are encrypted using TLS. Passwords are
				hashed and never stored in plain text. Access to production data is
				restricted to authorized personnel only.
			</Text>
		</Section>

		<Section id="rights" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 05">
				Your Rights
			</SectionHeader>

			<Text variant="body">
				Depending on your jurisdiction, you may have the right to access,
				correct, or delete your personal information. You may also request a
				copy of the data we hold about you. To exercise these rights, contact us
				at the email address below.
			</Text>

			<Text variant="body">
				You can delete your account at any time through your settings page.
				Upon deletion, your personal information is permanently removed from our
				systems within 30 days.
			</Text>
		</Section>

		<Section id="contact" width="lg" topMargin="sm" bottomMargin="sm">
			<SectionHeader label="// 06">
				Contact
			</SectionHeader>

			<Text variant="body">
				If you have questions about this Privacy Policy or how your data is
				handled, please contact us at
				<strong>privacy@meic.com</strong>.
			</Text>
		</Section>
	</Container>
	<Footer />
</template>
