import argparse, os, warnings
from lib.module.printf import printf, level as lv
from dotenv import load_dotenv

# yfinance internals use pandas-deprecated Timestamp.utcnow; noise only
warnings.filterwarnings("ignore", message="Timestamp.utcnow is deprecated.*")


PHASES = ["overview", "balance", "cash", "income", "dividends", "prices", "splits", "metrics", "fa"]
RUN_MODES = ["hourly", "daily", "backfill"]
SYMBOL_MODES = ["db", "file", "screener"]

parser = argparse.ArgumentParser(description="MICE script to insert/update data to database")
parser.add_argument("--run", choices=RUN_MODES, required=True, help="Composition runner: hourly|daily|backfill")
parser.add_argument("--symbols", choices=SYMBOL_MODES, default="db", help="Symbol discovery mode (default: db)")
parser.add_argument("--force", action="store_true", help="Bypass freshness checks, re-pull everything (price history capped at 10y)")
args = parser.parse_args()

printf.open("log", create_log=False, console_print=True)
load_dotenv()

from lib.supabase.sql_functions import get_symbols, get_stock_id_map
from pipeline.runner import run_mode
from lib.functions.stats import report

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
printf(f"-- Run mode {args.run}, {len(symbols)} symbols ({args.symbols}) --", lv.INFO)

# ctx phases gate on fetch-style flags; daily runs everything, backfill =
# prices (full), statements (full), overview, fa.
for phase in PHASES:
	setattr(args, phase, args.run == "daily" or (args.run == "backfill" and phase != "metrics"))
if args.run == "backfill":
	args.full = True  # full-history fetch mode, read by prices/statements

try:
	phases = run_mode(args.run, args, symbols, stock_ids, force=args.force)
	report(phases, prod=True)
finally:
	from lib.supabase.init import get_connection
	get_connection().close()
	printf("Disconnected from the database", lv.INFO)
	printf.close()
os._exit(0)
