import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: './tests/e2e',
	outputDir: './tests/output/artifacts',
	fullyParallel: false,
	reporter: [
		['list'],
		['html', { outputFolder: './tests/output/report', open: 'never' }],
	],
	use: {
		baseURL: 'http://localhost:3000',
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: {
		command: 'pnpm dev',
		url: 'http://localhost:3000',
		reuseExistingServer: true,
		timeout: 120_000,
	},
});