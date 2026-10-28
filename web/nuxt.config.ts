// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	compatibilityDate: "2025-07-15",
	devtools: { enabled: true },
	modules: [
		"@nuxt/eslint",
		"@nuxt/fonts",
		"@nuxt/icon",
		"@nuxt/image",
		"@nuxtjs/supabase",
	],
	eslint: {},
	runtimeConfig: {
		supabaseUrl: process.env.SUPABASE_URL,
		supabaseKey: process.env.SUPABASE_KEY,
		supabaseSecretKey: process.env.SUPABASE_SECRET_KEY,
		public: {},
	},
	supabase: {
		redirect: false,
		url: process.env.SUPABASE_URL,
		key: process.env.SUPABASE_KEY,
	},
	components: [
		{ path: "~/ui", pathPrefix: false },
	],
	css: [
		"~/styles/app.css",
	],
	alias: {}
});
