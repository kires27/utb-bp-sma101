import { URI } from "~~/shared/constants/routes";

export default defineNuxtRouteMiddleware((to) => {
	if (to.path === URI.home) {
		return navigateTo(URI.tool.fa);
	}
});
