import datetime as dt

from .context import market_data


def build_us_quote(ctx, symbol: str) -> dict | None:
	'''EOD quote for a US symbol from batched DefeatBeta data (market_data(ctx)).'''
	md = market_data(ctx)
	prices = md["prices"].get(symbol)
	shares = md["shares"].get(symbol)
	divs = md["dividends"].get(symbol) or []

	if not prices:
		return None

	last = prices[0]  # sorted desc by date
	prev = prices[1] if len(prices) > 1 else None

	change = None
	change_pct = None
	if prev and prev.get("close") is not None and last.get("close") is not None:
		change = last["close"] - prev["close"]
		change_pct = (change / prev["close"] * 100) if prev["close"] else None

	market_cap = None
	if last.get("close") is not None and shares:
		market_cap = last["close"] * shares

	dividend_yield = None
	if divs and last.get("close"):
		cutoff = (dt.date.today() - dt.timedelta(days=365)).isoformat()
		ttm_div = sum(float(d["amount"]) for d in divs if str(d["date"])[:10] >= cutoff)
		# fraction (0-1) - fac.dividend_yield scales x100
		dividend_yield = (ttm_div / last["close"]) if last["close"] else None

	return {
		"stock_price": last.get("close"),
		"market_cap": market_cap,
		"regular_market_change_percent": change_pct,
		"regular_market_change": change,
		"regular_market_time": None,
		"dividend_yield": dividend_yield,
	}
