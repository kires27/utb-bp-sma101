import { test, expect } from '@playwright/test';

test('registering with existing email shows "already exists" error', async ({ page }) => {
	const email = `doran86203@diarshop.com`;

	await page.goto('/auth/register', { waitUntil: 'networkidle' });

	await page.getByPlaceholder('Email or mobile phone number').fill(email);
	await page.getByPlaceholder('Password', { exact: true }).fill('Password1');
	await page.getByPlaceholder('Confirm password').fill('Password1');

	await page.getByRole('button', { name: 'SIGN UP', exact: true }).click();
	await expect(page.locator('.error-text')).toContainText('An account with this email already exists');
});