"""Per-run phase stats: collection, parseable summary, optional GITHUB_STEP_SUMMARY write."""
import os

from lib.functions.netstats import snapshot
from lib.module.printf import printf, level as lv

_failed_line_cap = 20		# PHASE log line is parseable input for verify.py; keep it bounded


def new_phase(phase: str, symbols_total: int) -> dict:
	'''Fresh stats dict for one phase run.'''
	return {"phase": phase, "symbols_total": symbols_total, "symbols_ok": 0, "rows_written": 0, "failed_symbols": []}


def count_symbol(stats: dict, ok: bool, symbol: str = None, rows: int = 0):
	'''Record one symbol outcome in a phase stats dict.'''
	if ok:
		stats["symbols_ok"] += 1
		stats["rows_written"] += rows
	elif symbol:
		stats["failed_symbols"].append(symbol)


def summary_line(stats: dict) -> str:
	failed = stats["failed_symbols"][:_failed_line_cap]
	failed_str = f" first={','.join(failed)}" if failed else ""
	# Per-phase network deltas, stamped by runner._with_net (absent in tests).
	net = ""
	if "db_requests" in stats or "yf_requests" in stats:
		net = f" db={stats.get('db_requests', 0)} yf={stats.get('yf_requests', 0)}"
	no_q = stats.get("skipped_no_q", 0)
	no_q_str = f" no_q={no_q}" if no_q else ""
	return (
		f"PHASE {stats['phase']} total={stats['symbols_total']} "
		f"ok={stats['symbols_ok']} rows={stats['rows_written']}"
		f" skipped_fresh={stats.get('skipped_fresh', 0)}{no_q_str}{failed_str}{net}"
	)


def network_line() -> str:
	'''Parseable NETWORK line from the run-level request counters.'''
	net = snapshot()
	return f"NETWORK yfinance={net['yfinance']} db={net['db']}"


def report(phases: list[dict], prod: bool = False):
	'''Print parseable PHASE lines + machine-readable summary (prod runs only).'''
	if not phases:
		printf("No phases reported stats", lv.WARNING)
		return

	printf("-- FINAL SUMMARY --", lv.INFO)
	for stats in phases:
		printf(summary_line(stats), lv.INFO)
	printf(network_line(), lv.INFO)

	if prod:
		_write_machine_file(phases)
		_write_step_summary(phases)


def _write_machine_file(phases: list[dict]):
	'''Plain PHASE lines for the verify step (workspace file, same job).'''
	try:
		with open("run_summary.txt", "w", encoding="utf-8") as f:
			for stats in phases:
				f.write(summary_line(stats) + "\n")
			f.write(network_line() + "\n")
	except OSError as err:
		printf(f"Could not write run summary file: {err}", lv.WARNING)


def _write_step_summary(phases: list[dict]):
	path = os.environ.get("GITHUB_STEP_SUMMARY")
	if not path:
		return

	try:
		with open(path, "a", encoding="utf-8") as f:
			f.write("## Pipeline run summary\n\n")
			f.write("| phase | total | ok | rows written | skipped (fresh) | failed | db req | yf req |\n")
			f.write("|---|---|---|---|---|---|---|---|\n")
			for stats in phases:
				failed = ", ".join(stats["failed_symbols"])
				f.write(
					f"| {stats['phase']} | {stats['symbols_total']} | {stats['symbols_ok']} "
					f"| {stats['rows_written']} | {stats.get('skipped_fresh', 0)} "
					f"| {failed} | {stats.get('db_requests', 0)} | {stats.get('yf_requests', 0)} |\n"
				)
			f.write("\n")
			net = snapshot()
			f.write(f"**Network requests:** yfinance {net['yfinance']} · db {net['db']}\n\n")
	except OSError as err:
		printf(f"Could not write step summary: {err}", lv.WARNING)
