/**
 * Market session + freshness label helpers (client-side only).
 *
 * Session math runs on the exchange's IANA timezone via Intl — DST is
 * handled by the formatter, never by manual offsets.
 *
 * week_pattern is 7 chars Mon→Sun ("1" = trading day), default "1111100".
 *
 * KNOWN LIMIT (no data): public holidays are not detected — a holiday may
 * still show as "open" (matches seed design). Lunch breaks ARE detected via
 * break_start_time/break_end_time (NULL = continuous session).
 */

/** "09:30" → minutes since midnight, null on garbage */
function parseHHMM(str) {
	if (!str) return null;
	const [h, m] = str.split(":").map(Number);
	if (Number.isNaN(h) || Number.isNaN(m)) return null;
	return h * 60 + m;
}

/** zone offset (ms) at instant `atMs` — positive means ahead of UTC */
function zoneOffsetMs(timezone, atMs) {
	const dtf = new Intl.DateTimeFormat("en-US", {
		timeZone: timezone,
		hour12: false,
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	});
	const get = (type) => Number(
		dtf.formatToParts(new Date(atMs)).find((p) => p.type === type)?.value,
	);
	// hour % 24: ICU may render "24" for midnight
	const asUTC = Date.UTC(
		get("year"), get("month") - 1, get("day"),
		get("hour") % 24, get("minute"), get("second"),
	);
	return asUTC - atMs;
}

/** UTC instant of local y/m/d + "HH:MM" in `timezone` (one DST re-check) */
function zonedToUtc(y, m, d, hhmm, timezone) {
	const mins = parseHHMM(hhmm);
	if (mins == null) return null;
	const naive = Date.UTC(y, m - 1, d, Math.floor(mins / 60), mins % 60);
	let utc = naive - zoneOffsetMs(timezone, naive);
	if (zoneOffsetMs(timezone, utc) !== zoneOffsetMs(timezone, naive)) {
		utc = naive - zoneOffsetMs(timezone, utc);
	}
	return utc;
}

/** exchange-local wall clock as {y, m, d, day, minutes} */
function exchangeClock(timezone, now) {
	const off = zoneOffsetMs(timezone, now.getTime());
	const local = new Date(now.getTime() + off);
	return {
		y: local.getUTCFullYear(),
		m: local.getUTCMonth() + 1,
		d: local.getUTCDate(),
		day: local.getUTCDay(), // 0=Sun
		minutes: local.getUTCHours() * 60 + local.getUTCMinutes(),
	};
}

/**
 * @param {object|null} exchangeInfo — { timezone, open_time, close_time,
 *   break_start_time, break_end_time, week_pattern }
 * @param {Date} [now]
 * @returns {null | { isOpen: boolean, nextEvent: { type: "opens"|"closes", utcMs: number } }}
 *   null when exchangeInfo is unusable
 */
export function getMarketStatus(exchangeInfo, now = new Date()) {
	if (!exchangeInfo?.timezone) return null;
	const open = parseHHMM(exchangeInfo.open_time);
	const close = parseHHMM(exchangeInfo.close_time);
	if (open == null || close == null) return null;
	const pattern = exchangeInfo.week_pattern || "1111100";
	const tz = exchangeInfo.timezone;

	// lunch break: null times = continuous session
	const breakStart = parseHHMM(exchangeInfo.break_start_time);
	const breakEnd = parseHHMM(exchangeInfo.break_end_time);
	const hasBreak = breakStart != null && breakEnd != null;

	const clock = exchangeClock(tz, now);
	const patternIdx = (clock.day + 6) % 7; // pattern index 0 = Monday
	const tradingToday = pattern[patternIdx] === "1";

	if (tradingToday && clock.minutes >= open && clock.minutes < close) {
		// inside session: lunch break = closed, next event is the re-open
		if (hasBreak && clock.minutes >= breakStart && clock.minutes < breakEnd) {
			return {
				isOpen: false,
				nextEvent: {
					type: "opens",
					utcMs: zonedToUtc(clock.y, clock.m, clock.d, exchangeInfo.break_end_time, tz),
				},
			};
		}
		// open: next close event is the break start (morning) or final close (afternoon)
		const nextClose = hasBreak && clock.minutes < breakStart
			? exchangeInfo.break_start_time
			: exchangeInfo.close_time;
		return {
			isOpen: true,
			nextEvent: {
				type: "closes",
				utcMs: zonedToUtc(clock.y, clock.m, clock.d, nextClose, tz),
			},
		};
	}

	// closed → next open: today later, else first trading day within a week
	for (let day = 0; day < 8; day += 1) {
		const date = new Date(Date.UTC(clock.y, clock.m - 1, clock.d + day));
		const idx = (date.getUTCDay() + 6) % 7;
		const afterCloseToday = day === 0 && clock.minutes >= close;
		if (pattern[idx] === "1" && !afterCloseToday) {
			return {
				isOpen: false,
				nextEvent: {
					type: "opens",
					utcMs: zonedToUtc(
						date.getUTCFullYear(),
						date.getUTCMonth() + 1,
						date.getUTCDate(),
						exchangeInfo.open_time,
						tz,
					),
				},
			};
		}
	}
	return { isOpen: false, nextEvent: null };
}

/** event time in the user's local timezone, e.g. "18:00" */
export function formatEventTime(utcMs) {
	return new Intl.DateTimeFormat(undefined, {
		hour: "2-digit",
		minute: "2-digit",
	}).format(new Date(utcMs));
}

/** short weekday in the user's locale, e.g. "Mon" */
export function formatEventWeekday(utcMs) {
	return new Intl.DateTimeFormat(undefined, {
		weekday: "short",
	}).format(new Date(utcMs));
}

/** does the event fall on the user's current local day? */
export function isEventToday(utcMs, nowMs = Date.now()) {
	const ymd = new Intl.DateTimeFormat(undefined, {
		year: "numeric",
		month: "numeric",
		day: "numeric",
	});
	return ymd.format(new Date(utcMs)) === ymd.format(new Date(nowMs));
}

/**
 * "Updated 14:32" — time in the user's local timezone; date only when the
 * updated timestamp is not the user's current local day ("Updated 5 Nov, 14:32")
 * @param {Date|null} updatedAt
 * @returns {string} "" when unknown
 */
export function formatUpdatedAt(updatedAt) {
	if (!updatedAt || Number.isNaN(updatedAt.getTime())) return "";
	const time = new Intl.DateTimeFormat(undefined, {
		hour: "2-digit",
		minute: "2-digit",
	}).format(updatedAt);
	const ymd = new Intl.DateTimeFormat(undefined, {
		year: "numeric",
		month: "numeric",
		day: "numeric",
	});
	if (ymd.format(updatedAt) === ymd.format(new Date())) {
		return `Updated ${time}`;
	}
	const day = new Intl.DateTimeFormat(undefined, {
		month: "short",
		day: "numeric",
	}).format(updatedAt);
	return `Updated ${day}, ${time}`;
}
