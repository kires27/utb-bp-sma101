import argparse, os, warnings
from lib.module.printf import printf, level as lv
from dotenv import load_dotenv

# yfinance internals use pandas-deprecated Timestamp.utcnow; noise only
warnings.filterwarnings("ignore", message="Timestamp.utcnow is deprecated.*")


# Phase registry: one entry per selectable phase. runner.run_phases gates on
# these attrs; execution order is fixed there, not by CLI order.
PHASES = ["quote", "overview", "statements", "prices", "dividends", "splits", "fa", "fqs", "calendar", "exchange"]
SYMBOL_MODES = ["db", "file", "screener"]

parser = argparse.ArgumentParser(description="MICE script to insert/update data to database")
parser.add_argument("--phases", required=True,
	help="Comma-separated phase selection (order irrelevant): " + ",".join(PHASES))
parser.add_argument("--symbols", choices=SYMBOL_MODES, default="db", help="Symbol discovery mode (default: db)")
parser.add_argument("--full", action="store_true",
	help="Full-history fetch mode (prices/statements); implied by a wiped table needing re-pull")
parser.add_argument("--force", action="store_true",
	help="Bypass freshness checks, re-pull everything (price history capped at 10y)")
args = parser.parse_args()

selected = [p.strip() for p in args.phases.split(",") if p.strip()]
unknown = [p for p in selected if p not in PHASES]
if unknown:
	parser.error(f"unknown phase(s): {', '.join(unknown)} (choose from: {', '.join(PHASES)})")
if not selected:
	parser.error(f"--phases is empty (choose from: {', '.join(PHASES)})")
for phase in PHASES:
	setattr(args, phase, phase in selected)

printf.open("log", create_log=False, console_print=True)
load_dotenv()

from lib.supabase.sql_functions import get_symbols, get_stock_id_map
from pipeline.runner import run_phases
from lib.functions.stats import report

# exchange seeds static reference data, calendar sweeps the universe-wide
# calendar feed; both are standalone and unused symbols/stock_ids
symbols, stock_ids = [], {}
if not set(selected) <= {"exchange", "calendar"}:
	if args.symbols == "file":
		from data.symbols import manual_symbols as symbols
	elif args.symbols == "screener":
		from pipeline.screener import discover
		discovery = discover()
		# Backfill queue: only symbols discovery just inserted. Insert-only,
		# so next scheduled run picks up anything missed today.
		symbols = discovery["new_symbols"]
	else:
		symbols = get_symbols()
	stock_ids = get_stock_id_map(symbols)
printf(f"-- Phases {args.phases}, {len(symbols)} symbols ({args.symbols}) --", lv.INFO)

try:
	phases = run_phases(args, symbols, stock_ids, force=args.force)
	report(phases, prod=True)
finally:
	from lib.supabase.init import get_connection
	get_connection().close()
	printf("Disconnected from the database", lv.INFO)
	printf.close()
os._exit(0)
