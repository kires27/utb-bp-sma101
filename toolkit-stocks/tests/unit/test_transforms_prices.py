from lib.transforms.prices import _clean, build_price_rows


def test_clean_none_and_nan():
	assert _clean(None) is None
	assert _clean(float("nan")) is None
	assert _clean("abc") is None
	assert _clean("12.5") == 12.5
	assert _clean(0) == 0.0


def test_build_price_rows_incremental_filter():
	rows = [
		{"date": "2024-01-03", "open": 1, "high": 2, "low": 0.5, "close": 100, "volume": 10},
		{"date": "2024-01-02", "close": 99},
	]
	out = build_price_rows("TEST", 7, rows, "2024-01-03")
	assert len(out) == 1
	assert out[0]["stock_id"] == 7
	assert out[0]["date"] == "2024-01-03"
	assert out[0]["close"] == 100


def test_build_price_rows_stock_id_none_returns_empty():
	rows = [{"date": "2024-01-03", "close": 100}]
	assert build_price_rows("TEST", None, rows, None) == []


def test_build_price_rows_none_latest_returns_all():
	rows = [{"date": "2024-01-03", "close": 100}, {"date": "2024-01-02", "close": 99}]
	out = build_price_rows("TEST", 1, rows, None)
	assert [r["date"] for r in out] == ["2024-01-03", "2024-01-02"]


def test_build_price_rows_fields_and_bad_close_skip():
	rows = [
		{"date": "2024-01-03", "open": 1, "high": 2, "low": 0.5, "close": 100, "volume": 10},
		{"date": "2024-01-02", "close": None},
	]
	out = build_price_rows("TEST", 1, rows, None)
	assert len(out) == 1
	assert out[0] == {
		"stock_id": 1,
		"date": "2024-01-03",
		"open": 1.0,
		"high": 2.0,
		"low": 0.5,
		"close": 100.0,
		"volume": 10.0,
	}
