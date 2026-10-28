import traceback
from datetime import date

from datasource.base import normalize_title, STATEMENT_FIELDS
from lib.module.printf import printf, level as lv


def period_from_date(d: date, period_type: str) -> str:
	if period_type == "annual":
		return "FY"
	month = d.month
	if month <= 3:
		return "Q1"
	elif month <= 6:
		return "Q2"
	elif month <= 9:
		return "Q3"
	return "Q4"


def _clean_value(value):
	'''Statement cell -> float | None.'''
	try:
		if value is None:
			return None
		f = float(value)
		return None if f != f else f	# NaN check without pandas
	except (TypeError, ValueError):
		return None


def _parse_date(raw) -> date | None:
	if raw is None:
		return None
	try:
		return date.fromisoformat(str(raw)[:10])
	except ValueError:
		return None


def build_statement_rows(symbol: str, stock_id: int, grouped: list[dict], period_type: str, finance_type: str) -> list[dict]:
	'''
	Transform grouped statement records into DB rows.

	grouped: list of records, one per (report_date, item) - each a dict of
		normalized field name -> raw value. Built by the datasource adapters.
	period_type: "annual" | "quarterly".
	finance_type: "income_statement" | "balance_sheet" | "cash_flow" -
		selects which DB columns the table has.
	'''
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		fields = STATEMENT_FIELDS[finance_type]
		rows: list[dict] = []
		for record in grouped:
			fiscal_date = _parse_date(record["report_date"])
			if fiscal_date is None:
				continue

			row = {
				"stock_id": stock_id,
				"fiscal_date": fiscal_date,
				"period": period_from_date(fiscal_date, period_type),
			}

			for db_field in fields:
				row[db_field] = _clean_value(record.get(db_field))

			rows.append(row)

		return rows
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{symbol}: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return []


def group_statement_records(records: list[dict]) -> list[dict]:
	'''
	Collapse long-format records [{report_date, item_name, item_value}] into
	one record per report_date: {report_date, <normalized_field>: value, ...}.
	'''
	grouped: dict[str, dict] = {}
	for record in records:
		key = str(record["report_date"])[:10]
		entry = grouped.setdefault(key, {"report_date": key})
		entry[normalize_title(record["item_name"])] = record["item_value"]
	return list(grouped.values())
