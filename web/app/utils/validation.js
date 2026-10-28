/**
 * returns boolean validation and error message if invalid
 * @typedef {Object} ValidationResult
 * @property {boolean} isValid - Whether the email is valid
 * @property {string} errorMsg - Error message if invalid
 */

/** @type {ValidationResult} */
const VALIDATION_OBJECT = {
	isValid: true,
	errorMsg: ""
}

/**
 * @param {string} email 
 * @returns {ValidationResult} 
 */
export function validateEmail(email) {
	const result = {...VALIDATION_OBJECT};
	if (!email.includes('@')) {
		result.errorMsg = 'Invalid email';
		result.isValid = false;
	}
	
	return result;
}

/**
 * @param {string} password 
 * @returns {[boolean, string]} returns boolean validation and error message if invalid
 */
export function validatePassword(password) {
	const result = {...VALIDATION_OBJECT};

	if (password.length < 8) {
		result.errorMsg = 'Password must be at least 8 characters';
		result.isValid = false;
	}

	return result;
}