<script setup>
import { useSupabaseUser, useSupabaseClient } from "#imports"
import { URI } from '#shared/constants/routes'
import { Icon } from '@iconify/vue'

const user = useSupabaseUser()
const client = useSupabaseClient()
const route = useRoute()

const menuOpen = ref(false)
const isHydrated = ref(false)

onMounted(() => {
	isHydrated.value = true
})

function closeMenu() {
	menuOpen.value = false
}

watch(() => route.fullPath, closeMenu)

async function logout() {
	await client.auth.signOut()
	await navigateTo(URI.user.login)
}
</script>

<template>
	<header class="header">
		<div class="header-inner">
			<div class="header-left">
				<button class="menu-btn" aria-label="Menu" @click="menuOpen = !menuOpen">
					<Icon :icon="menuOpen ? 'material-symbols:close' : 'material-symbols:menu'" width="24" />
				</button>

				<nav class="nav">
					<NuxtLink :to="URI.tool.fa">
						<Text variant="body" link>
							investing
						</Text>
					</NuxtLink>
					
					
					<NuxtLink :to="URI.tool.watchlist">
						<Text variant="body" link>
							watchlists
						</Text>
					</NuxtLink>

					<NuxtLink :to="URI.listStocks">
						<Text variant="body" link>
							symbols
						</Text>
					</NuxtLink>
					
				</nav>
			</div>


			<div class="header-right">
				<template v-if="isHydrated && user">
					<Button>
						<Icon icon="material-symbols:notifications" width="16" height="16" />
					</Button>
					<NuxtLink :to="URI.user.settings">
					<Button variant="primary" class="profile-icon">
						<Icon icon="mdi:gear" width="16" height="16" />
					</Button>
					</NuxtLink>
					<Button variant="secondary" @click="logout">Logout</Button>
				</template>

				<template v-else>
					<NuxtLink :to="URI.user.login">
						<Button>Sign in</Button>
					</NuxtLink>
					<NuxtLink :to="URI.user.register">
						<Button>Sign up</Button>
					</NuxtLink>
				</template>
			</div>
		</div>

		<div v-if="menuOpen" class="dropdown-overlay" @click="closeMenu" />

		<div v-if="menuOpen" class="mobile-dropdown">
			<nav class="mobile-nav">
				<NuxtLink :to="URI.tool.fa" @click="closeMenu">
					<Text variant="body" link>investing</Text>
				</NuxtLink>
				<NuxtLink :to="URI.tool.congress" @click="closeMenu">
					<Text variant="body" link>trading</Text>
				</NuxtLink>
				<NuxtLink :to="URI.tool.watchlist" @click="closeMenu">
					<Text variant="body" link>watchlists</Text>
				</NuxtLink>
			</nav>
		</div>
	</header>
</template>

<style scoped>
.header {
	position: sticky;
	top: 0;
	z-index: 50;
	height: 62px;
	border-bottom: 1px solid var(--border);
	background: rgba(12, 12, 15, 0.92);
	backdrop-filter: blur(12px);
}

.header-inner {
	/* max-width: var(--container-max); */
	/* margin: 0 auto; */
	padding: 0 2rem;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.header-left {
	display: flex;
	align-items: center;
	gap: 1.5rem;
}

.menu-btn {
	display: none;
	align-items: center;
	justify-content: center;
	border: none;
	background: none;
	color: var(--fg);
	cursor: pointer;
	padding: 0.4rem;
}

.divider {
	display: block;
}

.header-right {
	display: flex;
	gap: 0.75rem;
}

.logo {
	display: flex;
	align-items: center;
	gap: 0.6rem;
	font-size: 15px;
	font-weight: 600;
	letter-spacing: 0.08em;
}

.logo-mark {
	width: 36px;
	height: 36px;
	display: block;
	flex-shrink: 0;
	object-fit: cover;
	mix-blend-mode: screen;

	background-color: white;

	-webkit-mask: var(--mask-url) no-repeat center;
	mask: var(--mask-url) no-repeat center;

	-webkit-mask-size: contain;
	mask-size: contain;
}

.logo-text {
	color: var(--fg);
}

.nav {
	display: flex;
	align-items: center;
	gap: 3rem;
	text-transform: uppercase;
}

.profile-menu {
	position: relative;
	display: flex;
}

.profile-icon {
	font-size: 23px;
	color: var(--bg);
	/* height: 36px; */
}

.dropdown-overlay {
	position: fixed;
	inset: 62px 0 0 0;
	z-index: 48;
}

.mobile-dropdown {
	position: absolute;
	top: 62px;
	left: 0;
	right: 0;
	z-index: 49;
	padding: 0.5rem 2rem 1rem;
	background: rgba(12, 12, 15, 0.92);
	backdrop-filter: blur(12px);
	border-bottom: 1px solid var(--border);
}

.mobile-nav {
	display: flex;
	flex-direction: column;
}

.mobile-nav a {
	padding: 0.8rem 0;
	text-transform: uppercase;
	border-bottom: 1px solid var(--border);
}

.mobile-nav a:last-child {
	border-bottom: none;
}

@media (max-width: 750px) {
	.branding,
	.divider,
	.nav {
		display: none;
	}

	.menu-btn {
		display: flex;
	}
}
</style>
