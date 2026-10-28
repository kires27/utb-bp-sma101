let toastId = 0

export function useToast() {
	const toasts = useState("toasts", () => [])

	function showToast(message, opts = {}) {
		toasts.value.push({
			id: ++toastId,
			message,
			theme: opts.theme || "info",
			duration: opts.duration ?? 5000,
		})
	}

	function removeToast(id) {
		toasts.value = toasts.value.filter((t) => t.id !== id)
	}

	return { toasts, showToast, removeToast }
}

export function redirectWithToast(url, message, opts = {}) {
	const { showToast } = useToast()
	showToast(message, opts)
	return navigateTo(url, { replace: true })
}
