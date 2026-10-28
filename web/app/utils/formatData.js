/**
 * Converts a human-readable string or an array of human-readable strings
 * into a hyphen-separated format with all lowercase letters.
 * @param {string | string[]} input example: Value Analysis -> value-analysis
 * @returns {string | string[]} - The formatted string or array of formatted strings.
 */
export function stringToDashed(input) {
	/**
	 * Helper function to convert a single string to hyphen-separated format
	 * @param {string} str
	 * @returns {string}
	 */
	const convertString = (str) => {
		return str
			.toLowerCase() // Convert the string to lowercase
			.replace(/\s+/g, '-') // Replace spaces (and any extra whitespace) with hyphens
			.replace(/-+/g, '-') // Replace multiple hyphens with a single hyphen
			.trim(); // Remove leading/trailing hyphens
	};

	// Check if input is an array or a single string
	if (Array.isArray(input)) {
		return input.map(convertString); // Process each string in the array
	} else if (typeof input === 'string') {
		return convertString(input); // Process the single string
	} else {
		throw new TypeError('Input must be a string or an array of strings');
	}
}



/**
 * Converts a hyphen-separated string or an array of hyphen-separated strings
 * into a human-readable format with words capitalized and separated by spaces.
 * @param {string | string[]} input example: value-analysis -> Value Analysis
 * @returns {string | string[]} - The formatted string or array of formatted strings.
 */
export function dashedToString(input) {
	/**
	 * Helper function to format a single string
	 * @param {string} str
	 * @returns {string}
	 */
	const formatString = (str) => {
		return str
			.split("-") // Split the string on hyphen
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1)) // Capitalize each word
			.join(" "); // Join words with a space
	};

	if (Array.isArray(input)) {
		return input.map(formatString); // Process each string in the array
	} else if (typeof input === "string") {
		return formatString(input); // Process the single string
	} else {
		throw new TypeError("Input must be a string or an array of strings");
	}
}




/**
 * @param {string} word
 */
export function capitalizeFirstLetter(word) {
	return word.charAt(0).toUpperCase() + word.slice(1);
}

/**
 * Format a number as currency string.
 * @param {number|null} value
 * @param {string} currency - ISO code e.g. "USD", "EUR"
 * @param {number} decimals
 * @returns {string|null}
 */
export function formatCurrency(value, currency = "USD", decimals = 2) {
	if (value == null || isNaN(value)) return null;
	const symbolMap = { USD: "$", EUR: "€", GBP: "£", JPY: "¥" };
	const symbol = symbolMap[currency] ?? currency + " ";
	return symbol + Number(value).toFixed(decimals);
}




/**
 * @param {object} dict
 * @param {string} findKey
 * @return {Array<any>}
 */
export function flattenDictionary(dict, findKey) {

	/** * @type {any[]} */
	const result = [];

	/** 
	 * @param {Object | any} obj
	 */
	function flattenHelper(obj, parentKey = '') {
		for (const key in obj) {
			if (obj.hasOwnProperty(key)) {
				const newKey = parentKey ? `${parentKey}.${key}` : key;

				if (key === findKey) {
					result.push(obj[key]);
				} else if (typeof obj[key] === 'object' && obj[key] !== null) {
					flattenHelper(obj[key], newKey);
				}
			}
		}
	}

	flattenHelper(dict);
	return result;
}





/**
 * Decode number string value to int or float
 * @param {string} value 
 * @returns {number | null}
 */
export function decodeData(value) {
	try {
		return parseInt(value)
	} catch (e) { }

	try {
		return parseFloat(value)
	} catch (e) { }

	return null;
}

/**
 * takes parameter like '2025-08-15T22:00:01+00:00' and converts it to human readable text: August 16, 2025 at 12:00:01 AM
 * @param {any} isoString
 * @returns {string}
 */
export function convertToDate(isoString) {
	const date = new Date(isoString)

	const prettyDate = date.toLocaleString("en-US", {
		year: "numeric",
		month: "long",
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	})

	return prettyDate;
}


