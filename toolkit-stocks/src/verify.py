"""Post-run verification: freshness + row volume + per-symbol failure thresholds.

Run as a separate CI step after the pipeline. Exits non-zero on any failed check
so the workflow goes red and GitHub sends the failure email.

Usage: python src/verify.py quote [--log run_summary.txt]
"""
import argparse
import sys
from datetime import date, datetime

from dotenv import load_dotenv

from lib.module.printf import printf, level as lv
from lib.supabase.init import get_connection
import constants.db_tables as dbt

load_dotenv()

MAX_PRICE_AGE_DAYS = 4		# EOD data, weekends/holidays tolerated
MAX_FAILED_RATIO = 0.02		# >2% of symbols failed -> suspicious
MIN_ROWS = 1				# a healthy run always writes something
# Phases whose 0-row runs are healthy: quote is marketState-gated (closed
# markets write nothing; hourly cron keeps freshness), calendar writes only
# when new events appear, overview is an idempotent upsert (unchanged stock
# rows legitimately update nothing).
MIN_ROWS_PHASE_EXEMPT = {"quote", "calendar", "overview"}


def days_since(d: date) -> int:
	if isinstance(d, datetime):
		# timestamptz (maintenance_update) arrives as tz-aware datetime; convert
		# to local before .date() so the calendar date matches date.today().
		# Comparing UTC date vs local date is off by one between local midnight
		# and UTC midnight (e.g. 00:00-01:00 CET).
		d = d.astimezone().date() if d.tzinfo else d.date()
	return (date.today() - d).days


def fetch_one(cursor, query: str):
	cursor.execute(query)
	return cursor.fetchone()


def check_freshness(cursor, table: str, column: str, max_age_days: int) -> tuple[bool, str]:
	row = fetch_one(cursor, f"SELECT max({column}) FROM {table}")
	latest = row[0] if row else None
	if latest is None:
		return False, f"{table}: table empty"
	age = days_since(latest)
	ok = age <= max_age_days
	return ok, f"{table}: latest {column} = {latest} ({age}d ago, limit {max_age_days}d)"


def check_failed_ratio(stats: dict) -> tuple[bool, str]:
	total, ok = stats.get("symbols_total", 0), stats.get("symbols_ok", 0)
	if total == 0:
		return False, "no symbols processed at all"
	skipped = stats.get("skipped_fresh", 0)
	no_q = stats.get("skipped_no_q", 0)
	# skipped_fresh symbols fetched nothing (not failures); no_q symbols are
	# data-availability skips ALREADY counted inside symbols_ok by
	# statements.py (count_symbol(True) alongside skipped_no_q) — subtracting
	# no_q again double-counts and produced negative failed counts.
	failed = max(0, total - ok - skipped)
	ratio = failed / total
	ok_flag = ratio <= MAX_FAILED_RATIO
	failed_syms = stats.get("failed_symbols", [])
	extra = f" first: {', '.join(failed_syms)}" if failed and failed_syms else ""
	skip_str = f" skipped_fresh={skipped}" if skipped else ""
	no_q_str = f" no_q={no_q}" if no_q else ""
	msg = f"symbols: ok={ok}/{total} failed={failed} ({ratio:.1%}, limit {MAX_FAILED_RATIO:.0%}){skip_str}{no_q_str}{extra}"
	return ok_flag, msg


def parse_phase_lines(log_text: str) -> dict[str, dict]:
	'''Parse "PHASE <name> total=.. ok=.. rows=.. skipped_fresh=.." lines.'''
	stats = {}
	for line in log_text.splitlines():
		if not line.startswith("PHASE "):
			continue
		parts = line.split()
		try:
			first_part = next((p for p in parts[5:] if p.startswith("first=")), None)
			skip_part = next((p for p in parts[5:] if p.startswith("skipped_fresh=")), None)
			no_q_part = next((p for p in parts[5:] if p.startswith("no_q=")), None)
			entry = {
				"symbols_total": int(parts[2].split("=")[1]),
				"symbols_ok": int(parts[3].split("=")[1]),
				"rows_written": int(parts[4].split("=")[1]),
				"skipped_fresh": int(skip_part.removeprefix("skipped_fresh=")) if skip_part else 0,
				"skipped_no_q": int(no_q_part.removeprefix("no_q=")) if no_q_part else 0,
				"failed_symbols": first_part.removeprefix("first=").split(",") if first_part else [],
			}
		except (IndexError, ValueError):
			continue
		stats[parts[1]] = entry
	return stats


def run(mode: str, log_path: str | None) -> int:
	conn = get_connection()
	cursor = conn.cursor()
	failures = []

	if mode == "quote":
		for table in (dbt.historical_price, dbt.quote):
			ok, msg = check_freshness(cursor, table, "date" if table == dbt.historical_price else "maintenance_update", MAX_PRICE_AGE_DAYS)
			printf(msg, lv.INFO if ok else lv.ERROR)
			if not ok:
				failures.append(msg)

	cursor.close()
	conn.close()

	# PHASE stats come from the run log uploaded by the workflow step
	if log_path:
		with open(log_path, encoding="utf-8") as f:
			log_text = f.read()
		for name, stats in parse_phase_lines(log_text).items():
			ok, msg = check_failed_ratio(stats)
			printf(f"{name}: {msg}", lv.INFO if ok else lv.ERROR)
			if not ok:
				failures.append(msg)
			rows = stats.get("rows_written", 0)
			skipped = stats.get("skipped_fresh", 0)
			# 0 rows is healthy when nothing was attempted (every symbol fresh —
			# no fetch happened, so nothing could be written), when the phase is
			# marketState-gated / episodic / idempotent-upsert (see EXEMPT), or
			# for quarterly phases (fresh + upcoming-earnings suppression).
			attempted = stats["symbols_total"] - skipped
			if rows < MIN_ROWS and name not in MIN_ROWS_PHASE_EXEMPT and attempted > 0 and not name.endswith("_quarterly"):
				failures.append(f"{name}: rows_written={rows} below minimum {MIN_ROWS}")

	if failures:
		printf(f"VERIFY FAILED ({len(failures)} problems):", lv.ERROR)
		for msg in failures:
			printf(f"  - {msg}", lv.ERROR)
		return 1
	printf("VERIFY OK: all checks passed", lv.INFO)
	return 0


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Post-run pipeline verification")
	parser.add_argument("mode", choices=["quote"])
	parser.add_argument("--log", help="path to pipeline log file with PHASE summary lines")
	args = parser.parse_args()
	sys.exit(run(args.mode, args.log))
