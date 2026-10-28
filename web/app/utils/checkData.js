
/**
 * Recursively check if object is empty.
 * array.shift() returns first object and removes it from array by mutation. 
 * @param {object[]} data
 * @returns {boolean}
 */
export function validateObjects(...data) {
	if (data.length === 0) return true;
	const obj = data.shift();
	if (obj === undefined || Object.keys(obj).length === 0) return false;
	return validateObjects(...data);
}

/**
 * Check if value is within constraints.
 * 
 * @param {number} value
 * @param {[number | null, number | null]} cons constraints
 * @returns {number} return scale of difference from 1 to 3
 */
export function checkConstraints(value, cons) {
	let [min, max] = cons;
	
	if (min === null) min = value
	if (max === null) max = value

	if (typeof min !== 'number' || typeof max !== 'number')
        throw new Error("Constraints must be numbers.");

    if (value >= min && value <= max) return 1;
	
	return 3;
}