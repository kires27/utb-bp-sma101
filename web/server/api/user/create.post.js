import { supabaseClientAuth } from '~~/server/utils/supabase/auth';
import { validateRegistrationInput } from '#shared/validators/user-registration';

export default defineEventHandler(async (event) => {
	const body = await readBody(event).catch(() => null);
	if (!body) {
		throw createError({
			statusCode: 400,
			statusMessage: 'Bad Request',
			data: { message: 'Invalid request body' },
		});
	}

	const { email, password } = body;
	const validation = validateRegistrationInput(email, password);
	if (!validation.isValid) {
		throw createError({
			statusCode: 400,
			statusMessage: 'Bad Request',
			data: { message: Object.values(validation.errors).join(', ') },
		});
	}

	const { client } = await supabaseClientAuth(event, false);

	const { data, error } = await client.auth.signUp({
		email: email.trim().toLowerCase(),
		password,
	});

	if (error) {
		const msg = error.message?.toLowerCase() || '';

		// Supabase message text has changed across versions/locales —
		// match on multiple known variants instead of one exact phrase
		if (
			msg.includes('already registered') ||
			msg.includes('already exists') ||
			msg.includes('user already') ||
			error.status === 422 // Supabase uses 422 for "already registered" in some versions
		) {
			throw createError({
				statusCode: 409,
				statusMessage: 'Conflict',
				data: { message: 'An account with this email already exists' },
			});
		}

		if (msg.includes('rate limit') || error.status === 429) {
			throw createError({
				statusCode: 429,
				statusMessage: 'Too Many Requests',
				data: { message: 'Too many attempts. Please try again shortly.' },
			});
		}

		throw createError({
			statusCode: 400,
			statusMessage: 'Bad Request',
			data: { message: error.message },
		});
	}

	// Duplicate email + confirm-email enabled => no `error`, but identities is empty
	const identities = data?.user?.identities ?? [];
	if (data?.user && identities.length === 0) {
		throw createError({
			statusCode: 409,
			statusMessage: 'Conflict',
			data: { message: 'An account with this email already exists' },
		});
	}

	return { success: true, user: data.user };
});