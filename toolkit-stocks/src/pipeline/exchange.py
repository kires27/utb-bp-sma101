'''Seed stock_exchange table from static exchange list (data/exchanges.py).
Idempotent: re-running updates session times, never duplicates rows.'''
import traceback

from psycopg2 import sql

from lib.module.printf import printf, level as lv
from lib.supabase.init import get_connection
from lib.functions.stats import new_phase, count_symbol
import constants.db_tables as dbt
from data.exchanges import exchanges


def _validate_seed() -> list[str]:
	'''Structural sanity of the static seed. Empty list = valid.'''
	errors = []
	seen = set()
	for ex in exchanges:
		code = ex.get("exchange_code")
		if not code:
			errors.append(f"missing exchange_code: {ex}")
			continue
		if code in seen:
			errors.append(f"duplicate exchange_code: {code}")
		seen.add(code)
		for field in ("short_name", "long_name", "timezone", "open_time", "close_time"):
			if not ex.get(field):
				errors.append(f"{code}: missing {field}")
		wp = ex.get("week_pattern", "1111100")
		if len(wp) != 7 or any(c not in "01" for c in wp):
			errors.append(f"{code}: bad week_pattern {wp!r}")
	return errors


def run_exchange(force: bool = False) -> dict:
	'''Seed the stock_exchange table. force is a no-op: upsert is idempotent.'''
	stats = new_phase("exchange", len(exchanges))

	seed_errors = _validate_seed()
	for err in seed_errors:
		printf(err, lv.ERROR)
	if seed_errors:
		count_symbol(stats, False, "seed")
		return stats

	conn = get_connection()
	cursor = conn.cursor()
	try:
		for ex in exchanges:
			cursor.execute(
				f"""
				INSERT INTO {dbt.stock_exchange} (
					exchange_code, mic, short_name, long_name, country,
					timezone, open_time, close_time, week_pattern, currency
				)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
				ON CONFLICT (exchange_code) DO UPDATE SET
					mic = EXCLUDED.mic,
					short_name = EXCLUDED.short_name,
					long_name = EXCLUDED.long_name,
					country = EXCLUDED.country,
					timezone = EXCLUDED.timezone,
					open_time = EXCLUDED.open_time,
					close_time = EXCLUDED.close_time,
					week_pattern = EXCLUDED.week_pattern,
					currency = EXCLUDED.currency,
					updated_at = now()
				""",
				(
					ex["exchange_code"], ex.get("mic"), ex["short_name"], ex["long_name"],
					ex.get("country"), ex["timezone"], ex["open_time"], ex["close_time"],
					ex.get("week_pattern", "1111100"), ex.get("currency"),
				),
			)
			count_symbol(stats, True, rows=1)
		conn.commit()
	except Exception as err:
		conn.rollback()
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		count_symbol(stats, False, "seed")

	# Coverage check: every exchange in stock table should be in the seed.
	# Missing row = that exchange can't be session-gated later (reference data, not fatal).
	try:
		cursor.execute(
			sql.SQL("SELECT DISTINCT exchange FROM {}").format(sql.Identifier(dbt.stock))
		)
		db_codes = {row[0] for row in cursor.fetchall() if row[0]}
		unmapped = db_codes - {ex["exchange_code"] for ex in exchanges}
		for code in sorted(unmapped):
			printf(f"Exchange {code!r} in stock table missing from seed", lv.WARNING)
	except Exception as err:
		printf(f"Coverage check failed: {err}", lv.WARNING)

	return stats
