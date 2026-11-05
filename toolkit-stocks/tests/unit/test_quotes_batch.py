import pytest

from datasource.quotes_batch import QuotesBatchSource


def _record(**over):
	base = {
		"symbol": "TSCO.L",
		"regularMarketPrice": 553.4,
		"regularMarketChange": 14.8,
		"regularMarketChangePercent": 2.7,
		"regularMarketTime": 1704211200,
		"marketCap": 34290253824,
		"marketState": "CLOSED",
		"currency": "GBp",
		"regularMarketVolume": 1000,
		"regularMarketPreviousClose": 538.6,
	}
	base.update(over)
	return base


def test_normalize_gbp_scales_price_and_change():
	q = QuotesBatchSource._normalize(_record())
	assert q["stock_price"] == 5.534
	assert q["regular_market_change"] == pytest.approx(0.148)
	assert q["currency"] == "GBP"
	assert q["market_cap"] == 34290253824  # already base currency, untouched
	assert q["market_state"] == "CLOSED"


def test_normalize_gbx_label_normalized():
	assert QuotesBatchSource._normalize(_record(currency="GBX"))["currency"] == "GBP"


def test_normalize_gbp_null_fields_survive():
	q = QuotesBatchSource._normalize(_record(regularMarketPrice=None, regularMarketChange=None))
	assert q["stock_price"] is None
	assert q["regular_market_change"] is None
	assert q["currency"] == "GBP"


def test_normalize_usd_untouched():
	q = QuotesBatchSource._normalize(_record(symbol="AAPL", currency="USD", regularMarketPrice=339.5, regularMarketChange=-3.44))
	assert q["stock_price"] == 339.5
	assert q["regular_market_change"] == -3.44
	assert q["currency"] == "USD"
