from lib.transforms.metrics import build_metric_row


def test_basic_row_fields():
	quote = {"stock_price": 100.5, "market_cap": 2e12, "regular_market_change_percent": 0.01, "regular_market_change": 1.2}
	row = build_metric_row("AAPL", 3, quote)
	assert row["stock_id"] == 3
	assert row["stock_price"] == 100.5
	assert row["market_cap"] == 2e12
	assert row["regular_market_change_percent"] == 0.01
	assert row["regular_market_change"] == 1.2


def test_string_market_time_converted():
	quote = {"stock_price": 1, "regular_market_time": "2024-01-02 15:30:00"}
	row = build_metric_row("AAPL", 3, quote)
	assert row["regular_market_time"] == "2024-01-02T15:30:00Z"


def test_epoch_market_time_converted():
	quote = {"stock_price": 1, "regular_market_time": 1704211200}
	row = build_metric_row("AAPL", 3, quote)
	assert row["regular_market_time"] == "2024-01-02T16:00:00Z"


def test_none_market_time_omitted():
	row = build_metric_row("AAPL", 3, {"stock_price": 1, "regular_market_time": None})
	assert "regular_market_time" not in row


def test_missing_quote_fields_none():
	row = build_metric_row("AAPL", 3, {})
	assert row["stock_price"] is None
	assert row["market_cap"] is None


def test_stock_id_none_returns_empty():
	assert build_metric_row("AAPL", None, {"stock_price": 1}) == {}


def test_bad_symbol_returns_empty():
	assert build_metric_row(123, 3, {"stock_price": 1}) == {}
