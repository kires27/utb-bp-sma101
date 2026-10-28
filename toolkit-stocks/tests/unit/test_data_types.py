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
	assert map_latest_yahoo_historical(date.today()) == "1D"
	from datetime import timedelta
	assert map_latest_yahoo_historical(date.today() - timedelta(days=1)) == "1D"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=3)) == "5D"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=30)) == "3M"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=100)) == "6M"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=300)) == "1Y"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=1000)) == "5Y"
	assert map_latest_yahoo_historical(date.today() - timedelta(days=3000)) is None


def test_to_date():
	assert to_date(datetime(2024, 1, 2, 5)) == date(2024, 1, 2)
	assert to_date(date(2024, 1, 2)) == date(2024, 1, 2)
	assert to_date("x") == "x"
