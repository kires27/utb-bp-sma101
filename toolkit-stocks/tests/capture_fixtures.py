'''
Capture real API payloads once, save as frozen fixtures + expected rows.

Run manually with network + venv:
	.venv/bin/python tests/capture_fixtures.py            # capture + write expected
	.venv/bin/python tests/capture_fixtures.py --update   # regenerate expected rows only

Files written:
	tests/fixtures/defeatbeta/aapl/<kind>.json
	tests/fixtures/yfinance/aapl/<kind>.json
	... plus sibling <kind>.expected.json files (mapper output at capture time)
'''
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

FIXTURES = Path(__file__).parent / "fixtures"
SYMBOL_US = "AAPL"
SYMBOL_INTL = "ASML.AS"


def strip_volatile(rows):
	'''Drop nondeterministic fields before saving expected rows.'''
	if isinstance(rows, dict):
		return {k: v for k, v in rows.items() if k != "maintenance_update"}
	return [{k: v for k, v in row.items() if k != "maintenance_update"} for row in rows]


def write(path: Path, data):
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, default=str, sort_keys=True)
	print(f"wrote {path.relative_to(FIXTURES.parent)} ({len(json.dumps(data, default=str))} chars)")


def expected_path(path: Path) -> Path:
	return path.with_name(path.stem + ".expected.json")


def capture_defeatbeta():
	from datasource.defeatbeta import DefeatBetaSource
	from lib.transforms import (
		build_price_rows, build_dividend_rows, build_split_rows,
		build_overview_row, build_statement_rows,
	)
	from lib.transforms.statements import group_statement_records

	ds = DefeatBetaSource()
	sym = SYMBOL_US
	base = FIXTURES / "defeatbeta" / sym.lower()

	prices = ds.prices([sym])[sym]
	divs = ds.dividends([sym])[sym]
	splits = ds.splits([sym])[sym]
	profile = ds.profiles([sym])[sym]
	officers = ds.officers([sym]).get(sym, [])

	write(base / "prices.json", prices)
	write(base / "dividends.json", divs)
	write(base / "splits.json", splits)
	write(base / "profile.json", profile)
	write(base / "officers.json", officers)

	# expected rows
	write(expected_path(base / "prices.json"), strip_volatile(build_price_rows(sym, 1, prices, None)))
	write(expected_path(base / "dividends.json"), strip_volatile(build_dividend_rows(sym, 1, divs, None)))
	write(expected_path(base / "splits.json"), strip_volatile(build_split_rows(sym, 1, splits, None)))
	write(expected_path(base / "profile.json"), strip_volatile(build_overview_row(sym, profile, officers, {}, None)))

	for finance_type, name in [("income_statement", "income"), ("balance_sheet", "balance"), ("cash_flow", "cash")]:
		raw = ds.statements([sym], finance_type)[sym]
		grouped = group_statement_records(raw)
		write(base / f"statements_{name}.json", raw)
		write(expected_path(base / f"statements_{name}.json"), strip_volatile(build_statement_rows(sym, 1, grouped, "annual", finance_type)))

	return ds


def capture_yfinance_symbol(source, sym: str, intl: bool):
	from lib.transforms import (
		build_price_rows, build_overview_row, build_metric_row,
	)
	from lib.transforms.statements import build_statement_rows

	base = FIXTURES / "yfinance" / sym.lower()
	history = source.history_payload(sym)
	info = source.info(sym)
	quote = source.quote(sym)

	write(base / "history.json", history)
	write(base / "info.json", info)

	# expected rows (stock_id=1 sentinel, latest=None -> full history)
	write(expected_path(base / "history.json"), strip_volatile(build_price_rows(
		sym, 1, history["price_rows"], None
	)))
	write(expected_path(base / "info.json"), strip_volatile(build_overview_row(sym, info, None, {}, info)))
	write(expected_path(base / "quote.json"), strip_volatile(build_metric_row(sym, 1, quote)))
	write(base / "quote.json", quote)

	for kind, name in [("income_statement", "income"), ("balance_sheet", "balance"), ("cash_flow", "cash")]:
		grouped = source.statements_payload(sym, kind)
		if grouped is None:
			print(f"{sym}: no {kind}, skipping")
			continue
		write(base / f"statements_{name}.json", grouped)
		write(expected_path(base / f"statements_{name}.json"), strip_volatile(build_statement_rows(sym, 1, grouped, "annual", kind)))


def main():
	update_only = "--update" in sys.argv
	if not update_only:
		capture_defeatbeta()
		yfs = __import__("datasource.yfinance_source", fromlist=["YFinanceSource"]).YFinanceSource()
		capture_yfinance_symbol(yfs, SYMBOL_US, intl=False)
		capture_yfinance_symbol(yfs, SYMBOL_INTL, intl=True)
	else:
		# --update: re-run mappers over existing fixtures, refresh expected files
		_recompute_expected()
	print("done")


def _recompute_expected():
	from lib.transforms import (
		build_price_rows, build_dividend_rows, build_split_rows,
		build_overview_row, build_metric_row, build_statement_rows,
	)
	from lib.transforms.statements import group_statement_records

	for source_dir in ["defeatbeta", "yfinance"]:
		for sym_dir in sorted((FIXTURES / source_dir).iterdir()):
			sym = sym_dir.name.upper()
			if source_dir == "defeatbeta":
				prices = json.load(open(sym_dir / "prices.json"))
				divs = json.load(open(sym_dir / "dividends.json"))
				splits = json.load(open(sym_dir / "splits.json"))
				write(expected_path(sym_dir / "prices.json"), strip_volatile(build_price_rows(sym, 1, prices, None)))
				write(expected_path(sym_dir / "dividends.json"), strip_volatile(build_dividend_rows(sym, 1, divs, None)))
				write(expected_path(sym_dir / "splits.json"), strip_volatile(build_split_rows(sym, 1, splits, None)))
				profile = json.load(open(sym_dir / "profile.json"))
				officers = json.load(open(sym_dir / "officers.json"))
				write(expected_path(sym_dir / "profile.json"), strip_volatile(build_overview_row(sym, profile, officers, {}, None)))
				for name in ["income", "balance", "cash"]:
					raw = json.load(open(sym_dir / f"statements_{name}.json"))
					grouped = group_statement_records(raw)
					ft = {"income": "income_statement", "balance": "balance_sheet", "cash": "cash_flow"}[name]
					write(expected_path(sym_dir / f"statements_{name}.json"), strip_volatile(build_statement_rows(sym, 1, grouped, "annual", ft)))
			else:
				h = json.load(open(sym_dir / "history.json"))
				write(expected_path(sym_dir / "history.json"), strip_volatile(build_price_rows(
					sym, 1, h["price_rows"], None
				)))
				info = json.load(open(sym_dir / "info.json"))
				write(expected_path(sym_dir / "info.json"), strip_volatile(build_overview_row(sym, info, None, {}, info)))
				quote = json.load(open(sym_dir / "quote.json"))
				write(expected_path(sym_dir / "quote.json"), strip_volatile(build_metric_row(sym, 1, quote)))
				for name in ["income", "balance", "cash"]:
					p = sym_dir / f"statements_{name}.json"
					if not p.exists():
						continue
					grouped = json.load(open(p))
					ft = {"income": "income_statement", "balance": "balance_sheet", "cash": "cash_flow"}[name]
					write(expected_path(sym_dir / f"statements_{name}.json"), strip_volatile(build_statement_rows(sym, 1, grouped, "annual", ft)))


if __name__ == "__main__":
	main()
