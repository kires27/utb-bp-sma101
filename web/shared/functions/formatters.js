export function styleMedianSignal(raw, median, valueAboveMedianIsGood) {
	if (typeof raw !== "number" || typeof median !== "number") return "val-empty"
	if (median === 0) return "val-empty"

	const diff = Math.abs(raw - median) / Math.abs(median)
	if (diff < 0.05) return "val-close"

	const good = valueAboveMedianIsGood ? raw > median : raw < median
	return good ? "val-pos" : "val-neg"
}

export function formatPrice(price) {
	if (price == null) return `<span class="f-na">—</span>`
	return `$${Number(price).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

/**
 * Takes a snake_case key and converts it to human readable text.
 * @param {string} snakeWord
 * @returns {string}
 */
export function snakeCaseToNormal(snakeWord) {
	switch (snakeWord) {
		case "pb_ratio": return "PB Ratio"
		case "pe_ratio": return "PE Ratio"
	}

	return snakeWord
		.replace(/_/g, " ")
		.replace(/\b\w/g, (c) => c.toUpperCase())
}

export function titleCase(s) {
	return s.replace(/\b\w/g, (c) => c.toUpperCase())
}
