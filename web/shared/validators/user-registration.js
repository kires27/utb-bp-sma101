/**
 * @param {string} email
 * @param {string} password
 * @returns {{ isValid: boolean, errors: { email?: string, password?: string }, checks: { length: boolean, case: boolean, number: boolean } }}
 */
export function validateRegistrationInput(email, password) {
	const checks = {
		length: password.length >= 8,
		case: /[a-z]/.test(password) && /[A-Z]/.test(password),
		number: /[0-9]/.test(password),
	};

	const passwordValid = checks.length && checks.case && checks.number;

	const errors = {};
	if (!email || !email.includes('@')) {
		errors.email = 'Please enter a valid email';
	}
	if (!passwordValid) {
		if (!checks.length) errors.password = 'Password must be at least 8 characters';
		else if (!checks.case) errors.password = 'Password must contain lowercase and uppercase letters';
		else if (!checks.number) errors.password = 'Password must contain a number';
	}

	return {
		isValid: passwordValid && !errors.email,
		errors,
		checks,
	};
}
