"""Post-run verification: freshness + row volume + per-symbol failure thresholds.

Run as a separate CI step after the pipeline. Exits non-zero on any failed check
so the workflow goes red and GitHub sends the failure email.

Usage: python src/verify.py --prices-metrics | --fa
"""
import argparse
import sys
from datetime import date

from lib.module.printf import printf, level as lv
from lib.supabase.init import get_connection
import constants.db_tables as dbt

MAX_PRICE_AGE_DAYS = 4		# EOD data, weekends/holidays tolerated
MAX_FA_AGE_DAYS = 40		# annual data, quarterly refresh cadence tolerated
MAX_FAILED_RATIO = 0.02		# >2% of symbols failed -> suspicious
MIN_ROWS = 1				# a healthy run always writes something


def days_since(d: date) -> int:
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
	failed = total - ok
	ratio = failed / total
	ok_flag = ratio <= MAX_FAILED_RATIO
	extra = f" first: {', '.join(stats.get('failed_symbols', []))}" if failed else ""
	msg = f"symbols: ok={ok}/{total} failed={failed} ({ratio:.1%}, limit {MAX_FAILED_RATIO:.0%}){extra}"
	return ok_flag, msg


def parse_phase_lines(log_text: str) -> dict[str, dict]:
	'''Parse "PHASE <name> total=.. ok=.. rows=.." lines from pipeline output.'''
	stats = {}
	for line in log_text.splitlines():
		if not line.startswith("PHASE "):
			continue
		parts = line.split()
		try:
			entry = {
				"symbols_total": int(parts[2].split("=")[1]),
				"symbols_ok": int(parts[3].split("=")[1]),
				"rows_written": int(parts[4].split("=")[1]),
			}
		except (IndexError, ValueError):
			continue
		stats[parts[1]] = entry
	return stats


def run(mode: str, log_path: str | None) -> int:
	conn = get_connection()
	cursor = conn.cursor()
	failures = []

	if mode == "--prices-metrics":
		for table in (dbt.historical_price, dbt.metric):
			ok, msg = check_freshness(cursor, table, "date" if table == dbt.historical_price else "maintenance_update", MAX_PRICE_AGE_DAYS)
			printf(msg, lv.INFO if ok else lv.ERROR)
			if not ok:
				failures.append(msg)
	elif mode == "--fa":
		ok, msg = check_freshness(cursor, dbt.analysis, "maintenance_update", MAX_FA_AGE_DAYS)
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
			if rows < MIN_ROWS:
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
	parser.add_argument("mode", choices=["--prices-metrics", "--fa"])
	parser.add_argument("--log", help="path to pipeline log file with PHASE summary lines")
	args = parser.parse_args()
	sys.exit(run(args.mode, args.log))
