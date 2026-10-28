from domain.intrinsic_value.intrinsic_value import calculate_intrinsic_value


# Golden values backtracked from the canonical Excel model
# (concept/calculation/Analýza a dáta.xlsx, sheet AAPL, P53).
# price_to_fcf = peer-median P/FCF from sheet "PFCF Average" (2025 median = 7.8436...).
PEER_PFCF = 7.8436273373235155

CASH_FLOW = [
	{"fiscal_date": "2025-9-30", "free_cash_flow": 98767000000},
	{"fiscal_date": "2024-9-30", "free_cash_flow": 108807000000},
	{"fiscal_date": "2023-9-30", "free_cash_flow": 99584000000},
	{"fiscal_date": "2022-9-30", "free_cash_flow": 111443000000},
	{"fiscal_date": "2021-9-30", "free_cash_flow": 92953000000},
	{"fiscal_date": "2020-9-30", "free_cash_flow": 73365000000},
]


def _calc(stock_price, share_issued, cash_flow, price_to_fcf=PEER_PFCF):
	return calculate_intrinsic_value(
		stock_price=stock_price,
		share_issued=share_issued,
		cash_flow=cash_flow,
		price_to_fcf=price_to_fcf,
		growth_rate_discount=15,
		future_discount_rate=10,
		safety_margin=25,
	)


def test_aapl_2025():
	iv = _calc(255.2, 15_005_000_000, CASH_FLOW)
	assert round(iv["intrinsic_value_per_share"][0], 2) == 54.56
	assert round(iv["annual_growth_rate"][0], 4) == round(
		((98767 / 73365) ** (1 / 5) - 1) * 100, 4
	)


def test_aapl_2024():
	# Sheet Q-column (2024-2019): AGR uses 2024 vs 2019 FCF.
	iv = _calc(
		224.94,  # market price 2024-10-01
		15_408_000_000,
		CASH_FLOW[1:] + [{"fiscal_date": "2019-9-28", "free_cash_flow": 58896000000}],
		price_to_fcf=7.848663902326654,
	)
	assert round(iv["intrinsic_value_per_share"][0], 2) == 69.55


def test_few_years_fallback():
	"""< 6 FCF years: AGR falls back to available span (newest vs oldest)."""
	iv = _calc(255.2, 15_005_000_000, CASH_FLOW[:4])
	assert round(iv["annual_growth_rate"][0], 4) == round(
		((98767 / 111443) ** (1 / 3) - 1) * 100, 4
	)
