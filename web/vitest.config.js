import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	resolve: {
		alias: {
			'~~': fileURLToPath(new URL('.', import.meta.url)),
			'@@': fileURLToPath(new URL('.', import.meta.url)),
			'~': fileURLToPath(new URL('./app', import.meta.url)),
			'@': fileURLToPath(new URL('./app', import.meta.url)),
			'#shared': fileURLToPath(new URL('./shared', import.meta.url)),
		},
	},
	test: {
		environment: 'node',
		include: ['tests/unit/**/*.test.js'],
		passWithNoTests: true,
		setupFiles: ['./tests/unit/setup.js'],
	},
});