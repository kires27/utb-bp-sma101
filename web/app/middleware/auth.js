import { URI } from "~~/shared/constants/routes"

export default defineNuxtRouteMiddleware(async () => {
	const { data } = await useSupabaseClient().auth.getUser()

	if (!data.user) {
		return navigateTo(URI.user.login);
	}
})