import argparse, os, warnings
from lib.module.printf import printf, level as lv
from dotenv import load_dotenv

# yfinance internals use pandas-deprecated Timestamp.utcnow; noise only
warnings.filterwarnings("ignore", message="Timestamp.utcnow is deprecated.*")


PHASES = ["overview", "balance", "cash", "income", "dividends", "prices", "splits", "metrics", "fa"]

parser = argparse.ArgumentParser(description="MICE script to insert/update data to database")
mode_group = parser.add_mutually_exclusive_group(required=True)
mode_group.add_argument("--dev", action="store_true", help="Dev run: manual symbol list, writes log file")
mode_group.add_argument("--prod", action="store_true", help="Production run: stocks from DB, no log file")
parser.add_argument("--force", action="store_true", help="Bypass freshness checks, fetch everything")
parser.add_argument("--fetch", nargs="+", required=True, choices=PHASES + ["all"], help="Phases to run (one or more, or 'all')")
args = parser.parse_args()

if "all" in args.fetch:
	args.fetch = PHASES

# Default all phases to False so orchestrator can test any phase attribute,
# even when only a subset is selected via --fetch
for phase in PHASES:
	setattr(args, phase, False)

for mode in args.fetch:
	setattr(args, mode, True)

if args.prod:
	printf.open("log", create_log=False, console_print=True)
else:
	printf.open("log", create_log=True, console_print=True)
	load_dotenv()


from pipeline import run

try:
	run(args)
except KeyboardInterrupt:
	printf("Interrupted by user", lv.WARNING)
	printf.close()
	os._exit(130)
