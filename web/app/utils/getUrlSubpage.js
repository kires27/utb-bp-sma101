
/**
 * @param {string} url
 * @param {number} index
 */
export function extractSubpage(url, index = -1) {
	const word = url.split("/");
	const filtered = word.filter((x) => x.length > 0);
	const length = index >= 0 && index<=filtered.length-1 ? index : filtered.length-1;
	return filtered[length];
}
