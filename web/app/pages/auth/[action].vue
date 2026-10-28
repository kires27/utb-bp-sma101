<script setup>
import { URI } from '#shared/constants/routes'
import { Icon } from '@iconify/vue'
import { validateRegistrationInput } from '#shared/validators/user-registration'

const route = useRoute()

const action = computed(() => route.params.action)

const isLogin = computed(() => action.value === 'login')

if (!['login', 'register'].includes(action.value)) {
	throw createError({
		statusCode: 404
	})
}

const supabase = useSupabaseClient();

const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const rememberMe = ref(false);
const loading = ref(false);
const error = ref('');
const info = ref('');
const showPasswordChecks = ref(false)

const handlePasswordFocus = () => {
	showPasswordChecks.value = true
}

const passwordChecks = computed(() => {
	return validateRegistrationInput('', password.value).checks
})

// Centralized error message extraction — handles the fact that
// statusMessage can be sanitized in production, so we prefer
// data.message (set explicitly on the server) as the source of truth.
const extractErrorMessage = (err, fallback) => {
	return (
		err?.data?.data?.message ||
		err?.data?.statusMessage ||
		err?.message ||
		fallback
	)
}

const handleSubmit = async () => {
	if (isLogin.value) {
		if (!email.value || !password.value) {
			error.value = 'Please fill in all fields'
			return
		}

		loading.value = true
		error.value = ''
		info.value = ''

		try {
			const { data, error: authError } = await supabase.auth.signInWithPassword({
				email: email.value,
				password: password.value
			})

			if (authError) {
				error.value = authError.message
			} else {
				info.value = 'Login successful!'
				navigateTo(URI.home)
			}
		} catch (err) {
			error.value = err instanceof Error ? err.message : 'Unknown error'
		} finally {
			loading.value = false
		}
	} else {
		const validation = validateRegistrationInput(email.value, password.value)

		if (!validation.isValid) {
			error.value = Object.values(validation.errors).join(', ')
			return
		}

		if (password.value !== confirmPassword.value) {
			error.value = 'Passwords do not match'
			return
		}

		loading.value = true
		error.value = ''
		info.value = ''

		try {
			await $fetch('/api/user/create', {
				method: 'POST',
				body: { email: email.value, password: password.value },
			})

			info.value = 'Account created! Please check your email to confirm.'
		} catch (err) {
			error.value = extractErrorMessage(err, 'Registration failed')
		} finally {
			loading.value = false
		}
	}
}

const handleGoogleLogin = async () => {
	const { error: googleError } = await supabase.auth.signInWithOAuth({
		provider: 'google'
	})
	if (googleError) error.value = googleError.message
}

const handleForgotPassword = async () => {
	if (!email.value) {
		error.value = 'Please enter your email address'
		return
	}

	loading.value = true
	error.value = ''
	info.value = ''

	try {
		const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.value, {
			redirectTo: `${window.location.origin}/reset-password`
		})

		if (resetError) {
			error.value = resetError.message
		} else {
			info.value = 'Password reset email sent!'
		}
	} catch (err) {
		error.value = err instanceof Error ? err.message : 'Unknown error'
	} finally {
		loading.value = false
	}
}
</script>

<template>
	<Container hAlign="center">
		<Section class="auth-section">
			<div class="card">
				<Text variant="h3">{{ isLogin ? 'Sign in' : 'Sign up' }}</Text>

				<form class="form" @submit.prevent="handleSubmit">
					<div class="form-group">
						<Text variant="label">Email or mobile</Text>
						<Input v-model="email" type="text" placeholder="Email or mobile phone number" />
					</div>

					<div class="form-group">
						<Text variant="label">Password</Text>
						<Input v-model="password" type="password" placeholder="Password" @focus="handlePasswordFocus" />
						<Transition name="fade-slide">
							<div v-if="!isLogin && showPasswordChecks" class="password-checks">
								<div class="check-row" :class="{ met: passwordChecks.case }">
									<Icon :icon="passwordChecks.case
										? 'material-symbols:check-circle'
										: 'material-symbols:check-circle-outline'" width="16" height="16" />
									<Text variant="body-sm" tone="muted">Lowercase & uppercase letters</Text>
								</div>
								<div class="check-row" :class="{ met: passwordChecks.length }">
									<Icon :icon="passwordChecks.length
										? 'material-symbols:check-circle'
										: 'material-symbols:check-circle-outline'" width="16" height="16" />
									<Text variant="body-sm" tone="muted">At least 8 characters</Text>
								</div>
								<div class="check-row" :class="{ met: passwordChecks.number }">
									<Icon :icon="passwordChecks.number
										? 'material-symbols:check-circle'
										: 'material-symbols:check-circle-outline'" width="16" height="16" />
									<Text variant="body-sm" tone="muted">Contains a number</Text>
								</div>
							</div>
						</Transition>
					</div>

					<div class="form-group" v-if="!isLogin">
						<Text variant="label">Confirm password</Text>
						<Input v-model="confirmPassword" type="password" placeholder="Confirm password" />
					</div>

					<div class="row" v-if="isLogin">
						<Checkbox v-model="rememberMe" label="Remember me" />
						<NuxtLink>
							<Text variant="label" tone="muted" link @click.prevent="handleForgotPassword">Forgot
								password</Text>
						</NuxtLink>
					</div>

					<p v-if="error" class="error-text">{{ error }}</p>
					<p v-if="info" class="info-text">{{ info }}</p>

					<Button variant="primary" wide type="submit" :disabled="loading">
						{{ loading ? 'Please wait...' : (isLogin ? 'SIGN IN' : 'SIGN UP') }}
					</Button>

					<div class="or-text">
						<Text variant="label" tone="muted">or</Text>
					</div>


					<Button type="button" wide @click="handleGoogleLogin">
						<Icon icon="material-icon-theme:google" width="20" height="20" />
						<Text variant="body-sm">
							Continue with Google
						</Text>
					</Button>

					<NuxtLink :to="isLogin ? URI.user.register : URI.user.login">
						<Button wide>
							<Text variant="body-sm">
								{{ isLogin ? 'Create account' : 'Already have an account?' }}
							</Text>
						</Button>
					</NuxtLink>
				</form>
			</div>
		</Section>
	</Container>

	<Footer :fullMode="false"></Footer>
</template>

<style scoped>

.card {
	width: 420px;
	background: linear-gradient(180deg, var(--bg-card), var(--bg-2));
	border: 1px solid var(--border-hi);
	padding: 2rem;
	margin-top: 1rem;
}

.form {
	display: flex;
	flex-direction: column;
	gap: 1rem;
	padding-top: 15px;
}

.form-group {
	display: flex;
	flex-direction: column;
	gap: 0.4rem;
}

.row {
	display: flex;
	justify-content: space-between;
	font-size: 11px;
	color: var(--fg-3);
}

.or-text {
	text-align: center;
}

.error-text {
	font-size: 12px;
	color: var(--rose);
	text-align: center;
}

.info-text {
	font-size: 12px;
	color: var(--teal);
	text-align: center;
}

.password-checks {
	display: flex;
	flex-direction: column;
	gap: 0.3rem;
	padding-top: 0.2rem;
}

.check-row {
	display: flex;
	align-items: center;
	gap: 0.4rem;
	color: var(--fg-3);
}

.check-row.met {
	color: var(--teal);
}

.fade-slide-enter-active {
	transition: all 0.25s ease-out;
}

.fade-slide-leave-active {
	transition: all 0.15s ease-in;
}

.fade-slide-enter-from {
	opacity: 0;
	transform: translateY(-6px);
}

.fade-slide-leave-to {
	opacity: 0;
	transform: translateY(-6px);
}
</style>
