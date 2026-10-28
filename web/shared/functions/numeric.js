/**
 * is positive number?
 * @param {*} value 
 * @returns 
 */
export function isRealNumber(value) {
	return Number.isSafeInteger(value) && value > 0
}

/**
 * Returns `true` only for values whose type is `number`
 * and which are not `NaN`.
 * @param {*} value - Value to check.
 * @returns {boolean} Whether value is valid number.
 */
export function isNumber(value) {
	return typeof value === 'number' && !Number.isNaN(value);
}

/**
 * Round big to (B,M,T) or small number to decimal places
 * @param {number} num
 * @param {number} [decimals=3]
 * @returns {number | null} The rounded number, or null if input is invalid.
 */
export function roundAnyNumber(num, decimals = 3) {
	if (typeof num !== 'number' || Number.isNaN(num)) return null
	if (!Number.isInteger(decimals)) return null;

	const absNum = Math.abs(num);
	let result;

	if (absNum >= 1_000_000_000_000) {
		result = (num / 1_000_000_000_000).toFixed(1) + " T";
	} else if (absNum >= 1_000_000_000) {
		result = (num / 1_000_000_000).toFixed(1) + " B";
	} else if (absNum >= 1_000_000) {
		result = (num / 1_000_000).toFixed(1) + " M";
	} else {
		const factor = Math.pow(10, decimals)
		return Math.round(num * factor) / factor
	}

	// Remove trailing ".0"
	return result.replace(/\.0(?=\s)/, "");
}
