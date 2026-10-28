import { readDocument, get_document_names } from "#root/src/database/functions";

/**
 * Find the closest date to the target date from the keys of an object.
 *
 * @param {Object} searchObject - Object with date keys (formatted as 'YYYY-MM-DD').
 * @param {string|Date} targetDate - Target date string (formatted as 'MM/DD/YYYY') or Date object.
 * @returns {Object|null} - The object with the closest date or null if the input is invalid.
 */
export function findClosestDate(searchObject, targetDate) {
    if (!searchObject || Object.keys(searchObject).length === 0) {
        return null;
    }

	console.log(searchObject);
	console.log(targetDate);

    const target = convertToDate(targetDate);
	console.log(target);
	console.log(typeof target);

    // @ts-ignore
    if (isNaN(target)) {
        throw new Error("Invalid target date");
    }

    /** Convert object keys to an array of Date objects */
    const dates = Object.keys(searchObject).map((dateStr) =>
        convertToDate(dateStr)
    );

    /** Find the closest date */
    const closestDate = dates.reduce((closest, date) => {
        // @ts-ignore
        return Math.abs(date - target) < Math.abs(closest - target)
            ? date
            : closest;
    }, dates[0]);

    const closestDateStr = new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    }).format(closestDate);

    // @ts-ignore
    return { [closestDateStr]: searchObject[closestDateStr] };
}

/**
 * Compresses a number into a lossless string format.
 * @param {number | number[]} input - The number to compress.
 * @returns {string | string[]} The compressed string representation of the number.
 */
export function compressNumber(input) {
    if (Array.isArray(input)) {
        return input.map((num) => num.toString());
    } else if (typeof input === "number") {
        return input.toString();
    } else {
        throw new TypeError("Input must be a number or an array of numbers.");
    }
}


/**
 * @param {string} symbol
 * @param {string} statement ex. "income statement" | "balance sheet" | "cash flow"
 * @param {number} nod - number of documents to get
 * @returns {Promise<object[] | any>}
 */
export async function getStatementContent(symbol, statement, nod = 1) {
    const document_names = await get_document_names(
		joinPath("/", "stocks", symbol, statement),
        nod
    );
    const data = [];

    // @ts-ignore
    for (const [index, name] of document_names.entries()) {
        if (index >= nod) break;

        data.push(
            await readDocument(
				joinPath("/", "stocks", symbol, statement, name)
            )
        );
    }

    return data;
}

/**
 * @param {string} char 
 * @param  {...string} segments 
 * @returns 
 */
export function joinPath(char, ...segments) {
    return segments
        .map((part) => part.replace(/^\/+|\/+$/g, "")) // Remove leading/trailing slashes
        .filter((part) => part.length > 0) // Remove empty segments
        .join(char);
}