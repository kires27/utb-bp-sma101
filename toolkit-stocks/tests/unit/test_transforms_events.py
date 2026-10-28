from lib.transforms.events import build_dividend_rows, build_split_rows


def test_dividend_rows_basic():
	events = [
		{"date": "2024-02-01", "amount": 0.25},
		{"date": "2023-11-01", "amount": 0.2},
	]
	rows = build_dividend_rows("TEST", 5, events, None)
	assert rows == [
		{"stock_id": 5, "date": "2024-02-01", "dividend": 0.25},
		{"stock_id": 5, "date": "2023-11-01", "dividend": 0.2},
	]


def test_dividend_rows_incremental_filter():
	events = [
		{"date": "2024-02-01", "amount": 0.25},
		{"date": "2023-11-01", "amount": 0.2},
	]
	rows = build_dividend_rows("TEST", 5, events, "2024-01-01")
	assert [r["date"] for r in rows] == ["2024-02-01"]


def test_dividend_rows_stock_id_none_returns_empty():
	assert build_dividend_rows("TEST", None, [{"date": "2024-02-01", "amount": 1}], None) == []


def test_dividend_rows_bad_date_skipped():
	rows = build_dividend_rows("TEST", 5, [{"date": None, "amount": 1}], None)
	assert rows == []


def test_dividend_rows_zero_amount_skipped():
	rows = build_dividend_rows(
		"TEST", 5,
		[{"date": "2012-11-20", "amount": 0}, {"date": "2024-06-11", "amount": 0.01}],
		None,
	)
	assert rows == [{"stock_id": 5, "date": "2024-06-11", "dividend": 0.01}]


def test_split_rows_basic_and_int_factor():
	events = [
		{"date": "2024-06-10", "factor": 4},	 # int-valued -> int
		{"date": "2020-05-01", "factor": 1.5},	# fractional stays float
	]
	rows = build_split_rows("TEST", 3, events, None)
	# oldest first: split-trigger rebasis applies in insertion order
	assert rows == [
		{"stock_id": 3, "date": "2020-05-01", "factor": 1.5},
		{"stock_id": 3, "date": "2024-06-10", "factor": 4},
	]


def test_split_rows_none_and_zero_factor_skipped():
	events = [
		{"date": "2024-06-10", "factor": None},
		{"date": "2024-06-11", "factor": 0},
		{"date": "2024-06-12", "factor": 2},
	]
	rows = build_split_rows("TEST", 3, events, None)
	assert [r["date"] for r in rows] == ["2024-06-12"]


def test_split_rows_stock_id_none_returns_empty():
	assert build_split_rows("TEST", None, [{"date": "2024-06-10", "factor": 2}]) == []
