from datetime import datetime, timedelta, timezone
from datetime import date as dtdate

# Max age of historical prices (10 years, incl. leap days).
PRICE_HISTORY_DAYS = 3652


def price_history_cutoff() -> dtdate:
	'''Oldest date kept for historical prices (today - 10 years).'''
	return dtdate.today() - timedelta(days=PRICE_HISTORY_DAYS)


def time_to_timestamptz(time: str, time_format: str = "%Y-%m-%d %H:%M:%S") -> timezone.utc:
	dt = datetime.strptime(time, time_format)
	dt_utc = dt.replace(tzinfo=timezone.utc)
	timestamptz = dt_utc.isoformat().replace("+00:00", "Z")
	return timestamptz


def map_latest_yahoo_historical(db_date: datetime.date) -> str | None:
	today = dtdate.today()
	diff_days = (today - db_date).days

	if diff_days <= 1:
		return "1D"
	elif diff_days <= 5:
		return "5D"
	elif diff_days <= 90:
		return "3M"
	elif diff_days <= 180:
		return "6M"
	elif diff_days <= 365:
		return "1Y"
	elif diff_days <= 1825:
		return "5Y"
	else:
		return None


def to_date(x):
	if isinstance(x, datetime):
		return x.date()
	return x


def round_number(x):
	return int(x) if x.is_integer() else float(x)
