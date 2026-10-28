<script setup>
definePageMeta({
	options: {
		footerFullSize: true
	},
	middleware: 'auth'
})

import { ref, watch } from 'vue'
import { useToast } from "~/utils/toast"

const _user = useSupabaseUser()

// Mock user data
const user = ref({
	name: 'Jan Svoboda',
	handle: '@jsvoboda',
	memberSince: '2024',
	plan: 'Pro Plan',
	planStatus: 'active',
	renewalDate: '2027-04-01',
	email: 'j.svoboda@example.com',
	bio: '',
	timezone: 'Europe/Prague (CET+1)',
	passwordLastChanged: '2026-01-14',
	passwordStrength: 'STRONG'
})

// Form state
const form = ref({
	fullName: 'Jan Svoboda',
	email: 'j.svoboda@example.com',
	bio: '',
	timezone: 'Europe/Prague (CET+1)',
	currentPassword: '',
	newPassword: '',
	confirmPassword: ''
})

// Settings state
const settings = ref({
	// Channels
	inAppAlerts: true,
	emailNotifications: true,

	// Watchlist & Price
	priceThresholdAlerts: true,
	volumeAnomalies: false,

	// Reports
	dailyDigest: true,
	screenerMatches: false,

	// Congress & Fundamental
	congressFilings: true,
	ratioDriftFlags: true,

	// Digest Schedule
	digestFrequency: 'Daily',
	digestTime: '07:00 CET',

	// Display - Appearance
	theme: 'Terminal Dark',
	density: 'Default',
	fontSize: '13px',

	// Display - Data Formatting
	currency: 'USD ($)',
	numberFormat: '1,234.56',
	dateFormat: 'YYYY-MM-DD',
	tickerStrip: true,

	// Display - Dashboard
	defaultView: 'Financials',
	chartType: 'Candlestick'
})

// Sessions mock data
const sessions = ref([
	{
		id: 1,
		device: 'Chrome 124 · macOS 14',
		location: 'Frenštát pod Radhoštěm, CZ',
		isCurrent: true,
		time: 'Now',
		icon: '⊞'
	},
	{
		id: 2,
		device: 'Firefox 125 · Windows 11',
		location: 'Prague, CZ',
		isCurrent: false,
		time: '2026-04-17',
		icon: '⊞'
	},
	{
		id: 3,
		device: 'Safari · macOS 15',
		location: 'Ostrava, CZ',
		isCurrent: false,
		time: '2026-04-10',
		icon: '⊡'
	}
])

// 2FA status
const twoFA = ref({
	enabled: true,
	methods: [
		{ name: 'Authenticator App', desc: 'TOTP — Google Authenticator, Authy, or compatible', status: 'Active' },
		{ name: 'SMS / Text Message', desc: '6-digit code to registered phone number', status: 'Not Set' },
	]
})

// Dirty state tracking
const isDirty = ref(false)
const markDirty = () => { isDirty.value = true }

watch(form, markDirty, { deep: true })
watch(settings, markDirty, { deep: true })

// Toast notification
const { showToast } = useToast()

// Actions
const saveChanges = () => {
	isDirty.value = false
	showToast('Settings saved')
}

const discardChanges = () => {
	isDirty.value = false
}

const updatePassword = () => {
	showToast('Password updated')
	form.value.currentPassword = ''
	form.value.newPassword = ''
	form.value.confirmPassword = ''
}

const revokeSession = (id) => {
	sessions.value = sessions.value.filter(s => s.id !== id)
}

const revokeAllSessions = () => {
	sessions.value = sessions.value.filter(s => s.isCurrent)
}

const selectChip = (group, value) => {
	settings.value[group] = value
	markDirty()
}

const exportData = () => {
	showToast('Export started')
}

const resetSettings = () => {
	showToast('Settings reset')
}

const deleteAccount = () => {
	showToast('Account deletion requested')
}


</script>

<template>
	<div class="settings-page">
		<!-- Header -->
		<div class="page-header">
			<Text variant="label">// Account</Text>
			<Text variant="h3">Settings</Text>
		</div>

		<!-- PROFILE -->
		<div class="settings-section animate-fade-up">
			<Text variant="label" class="section-title">Profile</Text>
			<div class="block">
				<!-- Identity Row -->
				<div class="identity-row">
					<div class="identity-info">
						<div class="identity-name">{{ _user?.email }}</div>
						<div class="plan-tag">
							<span class="dot dot--running"></span>
							{{ user.plan }}
						</div>
					</div>
					<div class="identity-actions">
						<div class="renewal-date">Renewal {{ user.renewalDate }}</div>
						<Button size="sm">Manage Plan</Button>
					</div>
				</div>

				<!-- Form Rows -->
				<div class="row">
					<Text variant="label" class="row-label">Email</Text>
					<div class="row-field">
						<Input v-model="form.email" type="email" />
					</div>
					<div></div>
				</div>
			</div>
		</div>

		<!-- SECURITY -->
		<div class="settings-section animate-fade-up animate-delay-1">
			<Text variant="label" class="section-title">Security</Text>
			<div class="block">
				<!-- Password -->
				<Text variant="label" class="sub-label">Password</Text>
				<div class="row">
					<Text variant="label" class="row-label">Current Password</Text>
					<div class="row-field">
						<Input v-model="form.currentPassword" type="password" placeholder="••••••••••••" />
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">New Password</Text>
					<div class="row-field">
						<Input v-model="form.newPassword" type="password" placeholder="min 12 chars" />
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Confirm</Text>
					<div class="row-field">
						<Input v-model="form.confirmPassword" type="password" placeholder="repeat" />
					</div>
					<div><Button size="sm" variant="primary" @click="updatePassword">Update</Button></div>
				</div>
				<div class="password-meta">
					<span class="password-meta-text">
						LAST CHANGED {{ user.passwordLastChanged }}
					</span>
				</div>

				<!-- 2FA -->
				<Text variant="label" class="sub-label">Two-Factor Authentication</Text>
				<div class="twofa-header">
					<span class="dot dot--running"></span>
					<div class="twofa-header-info">
						<div class="twofa-header-title">2FA Enabled</div>
						<div class="twofa-header-desc">Account protected with two-factor authentication</div>
					</div>
					<Button variant="danger" size="sm">Disable</Button>
				</div>
				<div class="twofa-method" v-for="method in twoFA.methods" :key="method.name">
					<div class="twofa-method-info">
						<div class="twofa-method-name">{{ method.name }}</div>
						<div class="twofa-method-desc">{{ method.desc }}</div>
					</div>
					<span class="method-tag" :class="{ 'method-tag--active': method.status === 'Active' }">{{
						method.status }}</span>
				</div>

			</div>
		</div>

		<!-- NOTIFICATIONS -->
		<div class="settings-section animate-fade-up animate-delay-2">
			<Text variant="label" class="section-title">Notifications</Text>
			<div class="block">
				<!-- Channels -->
				<Text variant="label" class="sub-label">Channels</Text>
				<div class="row">
					<Text variant="label" class="row-label">In-App Alerts</Text>
					<div class="row-value row-value--small">Tray notifications inside the platform</div>
					<Toggle v-model="settings.inAppAlerts" />
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Email</Text>
					<div class="row-value row-value--small">{{ form.email }}</div>
					<Toggle v-model="settings.emailNotifications" />
				</div>

				<!-- Watchlist & Price -->
				<Text variant="label" class="sub-label">Watchlist & Price</Text>
				<div class="notif-row" v-for="item in [
					{ title: 'Price Threshold Alerts', desc: 'Symbol crosses user-defined price level', channel: 'In-App', key: 'priceThresholdAlerts' },
				]" :key="item.title">
					<div class="notif-info">
						<div class="notif-title">{{ item.title }}</div>
						<div class="notif-desc">{{ item.desc }}</div>
					</div>
					<div class="notif-channel">{{ item.channel }}</div>
					<Toggle v-model="settings[item.key]" />
				</div>

				<!-- Reports -->
				<Text variant="label" class="sub-label">Reports</Text>
				<div class="notif-row" v-for="item in [
					{ title: 'Daily Digest', desc: 'Fundamental & price delta report at scheduled time', channel: 'Email', key: 'dailyDigest' },
					{ title: 'Screener Matches', desc: 'New symbols matching saved screener criteria', channel: 'In-App', key: 'screenerMatches' }
				]" :key="item.title">
					<div class="notif-info">
						<div class="notif-title">{{ item.title }}</div>
						<div class="notif-desc">{{ item.desc }}</div>
					</div>
					<div class="notif-channel">{{ item.channel }}</div>
					<Toggle v-model="settings[item.key]" />
				</div>

				<!-- Congress & Fundamental -->
				<Text variant="label" class="sub-label">Congress & Fundamental</Text>
				<div class="notif-row" v-for="item in [
					{ title: 'Congress Trade Filings', desc: 'New disclosures filed for tracked symbols', channel: 'In-App', key: 'congressFilings' },
				]" :key="item.title">
					<div class="notif-info">
						<div class="notif-title">{{ item.title }}</div>
						<div class="notif-desc">{{ item.desc }}</div>
					</div>
					<div class="notif-channel">{{ item.channel }}</div>
					<Toggle v-model="settings[item.key]" />
				</div>

				<!-- Digest Schedule -->
				<Text variant="label" class="sub-label">Digest Schedule</Text>
				<div class="row">
					<Text variant="label" class="row-label">Frequency</Text>
					<div class="row-field">
						<Select v-model="settings.digestFrequency"
							:options="['Daily', 'Weekly (Mon)', 'Disabled']" />
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Delivery Time</Text>
					<div class="row-field">
						<Select v-model="settings.digestTime"
							:options="['07:00 CET', '08:00 CET', '09:00 CET', '18:00 CET']" />
					</div>
					<div></div>
				</div>
			</div>
		</div>

		<!-- DISPLAY -->
		<div class="settings-section animate-fade-up animate-delay-3">
			<Text variant="label" class="section-title">Display</Text>
			<div class="block">
				<!-- Appearance -->
				<Text variant="label" class="sub-label">Appearance</Text>
				<div class="row">
					<Text variant="label" class="row-label">Theme</Text>
					<div class="chips">
						<button v-for="opt in ['Terminal Dark', 'Dim', 'Light']" :key="opt" class="chip"
							:class="{ 'chip--on': settings.theme === opt }" @click="selectChip('theme', opt)">{{ opt
							}}</button>
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Density</Text>
					<div class="chips">
						<button v-for="opt in ['Compact', 'Default', 'Relaxed']" :key="opt" class="chip"
							:class="{ 'chip--on': settings.density === opt }" @click="selectChip('density', opt)">{{ opt
							}}</button>
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Font Size</Text>
					<div class="chips">
						<button v-for="opt in ['11px', '13px', '15px']" :key="opt" class="chip"
							:class="{ 'chip--on': settings.fontSize === opt }" @click="selectChip('fontSize', opt)">{{
								opt }}</button>
					</div>
					<div></div>
				</div>

				<!-- Data Formatting -->
				<Text variant="label" class="sub-label">Data Formatting</Text>
				<div class="row">
					<Text variant="label" class="row-label">Currency</Text>
					<div class="row-field">
						<Select v-model="settings.currency"
							:options="['USD ($)', 'EUR (€)', 'CZK (Kč)', 'GBP (£)']" />
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Number Format</Text>
					<div class="chips">
						<button v-for="opt in ['1,234.56', '1.234,56', '1 234,56']" :key="opt" class="chip"
							:class="{ 'chip--on': settings.numberFormat === opt }"
							@click="selectChip('numberFormat', opt)">{{ opt }}</button>
					</div>
					<div></div>
				</div>
				<div class="row">
					<Text variant="label" class="row-label">Date Format</Text>
					<div class="chips">
						<button v-for="opt in ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY']" :key="opt" class="chip"
							:class="{ 'chip--on': settings.dateFormat === opt }"
							@click="selectChip('dateFormat', opt)">{{ opt }}</button>
					</div>
					<div></div>
				</div>


				<!-- Dashboard -->
				<Text variant="label" class="sub-label">Fundamental Analysis</Text>
				<div class="row">
					<Text variant="label" class="row-label">Default View</Text>
					<div class="chips">
						<button v-for="opt in ['Financials', 'Intrinsic Value', 'Stock Profile']" :key="opt"
							class="chip" :class="{ 'chip--on': settings.defaultView === opt }"
							@click="selectChip('defaultView', opt)">{{ opt }}</button>
					</div>
					<div></div>
				</div>
			</div>
		</div>

		<!-- DANGER -->
		<div class="settings-section animate-fade-up animate-delay-4">
			<Text variant="label" class="section-title section-title--danger">Account Actions</Text>
			<div class="danger-block">
				<div class="danger-row">
					<div>
						<div class="danger-title">Export All Data</div>
						<div class="danger-desc">Download complete archive of watchlists, portfolios, screeners, and
							settings as JSON.</div>
					</div>
					<Button size="sm" @click="exportData">Export →</Button>
				</div>
				<div class="danger-row">
					<div>
						<div class="danger-title">Reset All Settings</div>
						<div class="danger-desc">Restore to factory defaults. Watchlists and portfolios unaffected.
						</div>
					</div>
					<Button variant="danger" size="sm" @click="resetSettings">Reset</Button>
				</div>
				<div class="danger-row danger-row--delete">
					<div>
						<div class="danger-title danger-title--delete">Delete Account</div>
						<div class="danger-desc">Permanently delete account and all associated data. Irreversible.
							Subscription not refunded.</div>
					</div>
					<Button variant="danger" @click="deleteAccount">Delete Account</Button>
				</div>
			</div>
		</div>

	</div>

	<!-- Save Bar -->
	<Transition name="save-bar">
		<div v-if="isDirty" class="save-bar">
			<div class="save-bar-inner">
				<span class="save-bar-msg">Unsaved <span>changes</span></span>
				<div class="save-bar-actions">
					<Button size="sm" @click="discardChanges">Discard</Button>
					<Button size="sm" variant="primary" @click="saveChanges">Save Changes</Button>
				</div>
			</div>
		</div>
	</Transition>

	<Footer></Footer>
</template>

<style scoped>
.settings-page {
	max-width: 780px;
	margin: 0 auto;
}

/* Page Header */
.page-header {
	margin-bottom: 3rem;
	margin-top: 3rem;
}

.page-sub {
	font-family: var(--font-main);
	font-size: 13px;
	color: var(--fg-3);
}

/* Section */
.settings-section {
	margin-bottom: 2.75rem;
}

.section-title {
	padding-bottom: 0.6rem;
	border-bottom: 1px solid var(--border);
}

.section-title--danger {
	border-color: rgba(196, 122, 122, 0.2);
}

/* Block */
.block {
	border: 1px solid var(--border);
	border-top: none;
}

/* Rows */
.row {
	display: grid;
	grid-template-columns: 190px 1fr auto;
	align-items: center;
	gap: 1.5rem;
	padding: 0.9rem 1.25rem;
	border-bottom: 1px solid var(--border);
	transition: var(--transition);
}

.row:last-child {
	border-bottom: none;
}

.row:hover {
	background: var(--bg-hover);
}

.row-label {
	flex-shrink: 0;
}

.row-value {
	font-size: 12px;
	color: var(--fg-2);
}

.row-value--small {
	font-size: 10px;
}

.row-field {
	display: flex;
}



/* Identity Row */
.identity-row {
	display: flex;
	align-items: center;
	gap: 1.5rem;
	padding: 1.5rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

.identity-info {
	flex: 1;
}

.identity-name {
	font-size: 15px;
	font-weight: 500;
	margin-bottom: 0.15rem;
}

.plan-tag {
	display: inline-flex;
	align-items: center;
	gap: 0.4rem;
	font-size: 9px;
	letter-spacing: 0.14em;
	text-transform: uppercase;
	padding: 0.2rem 0.55rem;
	background: var(--teal-dim);
	border: 1px solid var(--teal-border);
	color: var(--teal);
}

.identity-actions {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 0.5rem;
}

.renewal-date {
	font-size: 10px;
	color: var(--fg-3);
}

/* Password meta */
.password-meta {
	padding: 0.6rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

.password-meta-text {
	font-size: 10px;
	color: var(--fg-3);
	letter-spacing: 0.05em;
}

/* Sub-label */
.sub-label {
	display: block;
	padding: 0.5rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

/* 2FA */
.twofa-header {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	padding: 1rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

.twofa-header-info {
	flex: 1;
}

.twofa-header-title {
	font-size: 12px;
	color: var(--fg);
	margin-bottom: 2px;
}

.twofa-header-desc {
	font-size: 10px;
	color: var(--fg-3);
}

.twofa-method {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0.85rem 1.25rem;
	border-bottom: 1px solid var(--border);
	transition: var(--transition);
}

.twofa-method:last-child {
	border-bottom: none;
}

.twofa-method:hover {
	background: var(--bg-hover);
}

.twofa-method-info {
	display: flex;
	flex-direction: column;
}

.twofa-method-name {
	font-size: 11px;
	color: var(--fg);
	margin-bottom: 2px;
}

.twofa-method-desc {
	font-size: 10px;
	color: var(--fg-3);
}

.method-tag {
	font-size: 9px;
	letter-spacing: 0.1em;
	text-transform: uppercase;
	padding: 0.2rem 0.5rem;
	border: 1px solid var(--border);
	color: var(--fg-3);
	white-space: nowrap;
}

.method-tag--active {
	background: var(--teal-dim);
	border-color: var(--teal-border);
	color: var(--teal);
}

/* Notifications */
.notif-row {
	display: grid;
	grid-template-columns: 1fr auto auto;
	align-items: center;
	gap: 1.5rem;
	padding: 0.85rem 1.25rem;
	border-bottom: 1px solid var(--border);
}

.notif-row:last-child {
	border-bottom: none;
}

.notif-title {
	font-size: 11px;
	color: var(--fg);
	margin-bottom: 2px;
}

.notif-desc {
	font-size: 10px;
	color: var(--fg-3);
}

.notif-channel {
	font-size: 9px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: var(--fg-3);
	white-space: nowrap;
}

/* Chips */
.chips {
	display: flex;
	gap: 0.4rem;
	flex-wrap: wrap;
}

.chip {
	font-size: 10px;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	padding: 0.28rem 0.7rem;
	border: 1px solid var(--border-hi);
	color: var(--fg-3);
	cursor: pointer;
	transition: var(--transition);
	background: transparent;
	font-family: var(--font-main);
}

.chip:hover {
	color: var(--fg);
	border-color: var(--border-hi);
}

.chip--on {
	background: var(--teal-dim);
	border-color: var(--teal-border);
	color: var(--teal);
}

/* Danger Block */
.danger-block {
	border: 1px solid rgba(196, 122, 122, 0.15);
	border-top: none;
}

.danger-row {
	display: grid;
	grid-template-columns: 1fr auto;
	align-items: center;
	gap: 1.5rem;
	padding: 1rem 1.25rem;
	border-bottom: 1px solid rgba(196, 122, 122, 0.1);
}

.danger-row:last-child {
	border-bottom: none;
}

.danger-row--delete {
	border-top: 1px solid rgba(196, 122, 122, 0.15);
}

.danger-title {
	font-size: 11px;
	color: var(--fg);
	margin-bottom: 3px;
}

.danger-title--delete {
	color: var(--rose);
}

.danger-desc {
	font-size: 10px;
	color: var(--fg-3);
	max-width: 480px;
}

/* Save Bar */
.save-bar {
	position: sticky;
	bottom: 0;
	height: 52px;
	background: rgba(12, 12, 15, 0.97);
	border-top: 1px solid var(--border);
	display: flex;
	align-items: center;
	z-index: 90;
	/* margin-top: 2rem; */
}

/* Save Bar Transition */
.save-bar-enter-active,
.save-bar-leave-active {
	transition: all 0.2s ease;
}

.save-bar-enter-from,
.save-bar-leave-to {
	transform: translateY(100%);
	opacity: 0;
}

.save-bar--visible {
	transform: translateY(0);
}

.save-bar-inner {
	width: 100%;
	max-width: 720px;
	margin: 0 auto;
	padding: 0 2.5rem;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.save-bar-msg {
	font-size: 11px;
	color: var(--fg-3);
	letter-spacing: 0.05em;
}

.save-bar-msg span {
	color: var(--gold);
}

.save-bar-actions {
	display: flex;
	gap: 0.6rem;
}
</style>
