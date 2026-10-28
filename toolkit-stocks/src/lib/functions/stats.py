"""Per-run phase stats: collection, parseable summary, optional GITHUB_STEP_SUMMARY write."""
import os

from lib.module.printf import printf, level as lv

_failed_cap = 20


def new_phase(phase: str, symbols_total: int) -> dict:
	'''Fresh stats dict for one phase run.'''
	return {"phase": phase, "symbols_total": symbols_total, "symbols_ok": 0, "rows_written": 0, "failed_symbols": []}


def count_symbol(stats: dict, ok: bool, symbol: str = None, rows: int = 0):
	'''Record one symbol outcome in a phase stats dict.'''
	if ok:
		stats["symbols_ok"] += 1
		stats["rows_written"] += rows
	else:
		if len(stats["failed_symbols"]) < _failed_cap and symbol:
			stats["failed_symbols"].append(symbol)


def summary_line(stats: dict) -> str:
	failed = stats["failed_symbols"]
	failed_str = f" first={','.join(failed)}" if failed else ""
	return (
		f"PHASE {stats['phase']} total={stats['symbols_total']} "
		f"ok={stats['symbols_ok']} rows={stats['rows_written']}"
		f" skipped_fresh={stats.get('skipped_fresh', 0)}{failed_str}"
	)


def report(phases: list[dict], prod: bool = False):
	'''Print parseable PHASE lines + machine-readable summary (prod runs only).'''
	if not phases:
		printf("No phases reported stats", lv.WARNING)
		return

	printf("---- FINAL SUMMARY ----", lv.INFO)
	for stats in phases:
		printf(summary_line(stats), lv.INFO)

	if prod:
		_write_machine_file(phases)
		_write_step_summary(phases)


def _write_machine_file(phases: list[dict]):
	'''Plain PHASE lines for the verify step (workspace file, same job).'''
	try:
		with open("run_summary.txt", "w", encoding="utf-8") as f:
			for stats in phases:
				f.write(summary_line(stats) + "\n")
	except OSError as err:
		printf(f"Could not write run summary file: {err}", lv.WARNING)


def _write_step_summary(phases: list[dict]):
	path = os.environ.get("GITHUB_STEP_SUMMARY")
	if not path:
		return

	try:
		with open(path, "a", encoding="utf-8") as f:
			f.write("## Pipeline run summary\n\n")
			f.write("| phase | total | ok | rows written | skipped (fresh) | failed (first) |\n")
			f.write("|---|---|---|---|---|---|\n")
			for stats in phases:
				failed = ", ".join(stats["failed_symbols"][:5])
				suffix = "…" if len(stats["failed_symbols"]) > 5 else ""
				f.write(
					f"| {stats['phase']} | {stats['symbols_total']} | {stats['symbols_ok']} "
					f"| {stats['rows_written']} | {stats.get('skipped_fresh', 0)} "
					f"| {failed}{suffix} |\n"
				)
			f.write("\n")
	except OSError as err:
		printf(f"Could not write step summary: {err}", lv.WARNING)
