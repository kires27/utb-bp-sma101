from datetime import date

from lib.transforms.statements import (
	build_statement_rows,
	group_statement_records,
	period_from_date,
)


def test_period_from_date():
	assert period_from_date(date(2024, 1, 15), "annual") == "FY"
	assert period_from_date(date(2024, 2, 15), "quarterly") == "Q1"
	assert period_from_date(date(2024, 5, 15), "quarterly") == "Q2"
	assert period_from_date(date(2024, 8, 15), "quarterly") == "Q3"
	assert period_from_date(date(2024, 11, 15), "quarterly") == "Q4"


def test_group_statement_records():
	records = [
		{"report_date": "2024-01-01", "item_name": "Total Revenue", "item_value": 100},
		{"report_date": "2024-01-01", "item_name": "Gross Profit", "item_value": 40},
		{"report_date": "2023-01-01", "item_name": "Total Revenue", "item_value": 90},
	]
	grouped = group_statement_records(records)
	assert len(grouped) == 2
	by_date = {g["report_date"]: g for g in grouped}
	assert by_date["2024-01-01"]["total_revenue"] == 100
	assert by_date["2024-01-01"]["gross_profit"] == 40
	assert by_date["2023-01-01"]["total_revenue"] == 90


def test_build_statement_rows_maps_fields_and_period():
	grouped = [{
		"report_date": "2024-09-28",
		"total_revenue": 100.0,
		" gross_profit": 40.0,
		"net_income": float("nan"),	 # NaN -> None
		"operating_income": None,
	}]
	rows = build_statement_rows("TEST", 9, grouped, "annual", "income_statement")
	assert len(rows) == 1
	row = rows[0]
	assert row["stock_id"] == 9
	assert row["fiscal_date"] == date(2024, 9, 28)
	assert row["period"] == "FY"
	assert row["total_revenue"] == 100.0
	assert row["net_income"] is None
	assert row["operating_income"] is None
	# untouched field present as None
	assert row["basic_average_shares"] is None


def test_build_statement_rows_bad_date_skipped():
	grouped = [{"report_date": "not-a-date", "total_revenue": 1}]
	assert build_statement_rows("TEST", 9, grouped, "annual", "income_statement") == []


def test_build_statement_rows_stock_id_none_returns_empty():
	grouped = [{"report_date": "2024-01-01", "total_revenue": 1}]
	assert build_statement_rows("TEST", None, grouped, "annual", "income_statement") == []


def test_build_statement_rows_cash_flow_fields():
	grouped = [{"report_date": "2024-01-01", "free_cash_flow": 5, "capital_expenditure": -1, "operating_cash_flow": 8}]
	rows = build_statement_rows("TEST", 9, grouped, "quarterly", "cash_flow")
	assert rows[0]["free_cash_flow"] == 5.0
	assert rows[0]["period"] == "Q1"
