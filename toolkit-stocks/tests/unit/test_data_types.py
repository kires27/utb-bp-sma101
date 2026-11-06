import pytest

from lib.functions.data_types import map_latest_yahoo_historical, time_to_timestamptz, to_date
from datetime import date, datetime


def test_time_to_timestamptz_default_format():
	assert time_to_timestamptz("2024-01-02 15:30:00") == "2024-01-02T15:30:00Z"


def test_time_to_timestamptz_custom_format():
	assert time_to_timestamptz("02/01/2024", "%d/%m/%Y") == "2024-01-02T00:00:00Z"


def test_time_to_timestamptz_malformed_raises():
	with pytest.raises(ValueError):
		time_to_timestamptz("garbage")


def test_map_latest_yahoo_historical_ranges():
	assert map_latest_yahoo_historical(date.today()) == "1d"
	from datetime import timedelta
	assert map_latest_yahoo_historical(date.today() - timedelta(days=1)) == "1d"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=3)) == "5d"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=30)) == "3mo"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=100)) == "6mo"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=300)) == "1y"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=1000)) == "5y"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=3000)) is None


def test_map_latest_yahoo_historical_periods_are_valid():
	'''Every mapped period must be accepted by yfinance, else the symbol
	fetches 0 rows forever and can never self-heal.'''
	from lib.functions.data_types import PRICE_HISTORY_PERIOD
	valid = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
	for days in [0, 1, 2, 5, 6, 30, 91, 180, 181, 365, 366, 1825, 1826]:
		from datetime import timedelta
		period = map_latest_yahoo_historical(date.today() - timedelta(days=days))
		assert period is None or period in valid
	assert PRICE_HISTORY_PERIOD in valid


def test_to_date():
	assert to_date(datetime(2024, 1, 2, 5)) == date(2024, 1, 2)
	assert to_date(date(2024, 1, 2)) == date(2024, 1, 2)
	assert to_date("x") == "x"
