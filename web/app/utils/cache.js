const store = new Map()
const MAX = 100

export function cached(key, fn) {
	const entry = store.get(key)
	if (entry) return Promise.resolve(entry.data)

	return fn().then((data) => {
		if (store.size >= MAX) {
			const oldest = store.keys().next().value
			store.delete(oldest)
		}
		store.set(key, { data })
		return data
	})
}

export function invalidate(key) {
	store.delete(key)
}

export function invalidatePrefix(prefix) {
	for (const k of store.keys()) {
		if (k.startsWith(prefix)) store.delete(k)
	}
}

export function clearCache() {
	store.clear()
}
