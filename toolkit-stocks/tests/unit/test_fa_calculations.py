import pytest

from domain.financial_analysis.fa_calculations import (
	gross_margin, operating_margin, net_margin, return_on_equity,
	earning_per_share, debt_to_equity, current_ratio, revenues_per_share,
	capital_index, payback_period, assets_price, pe_ratio, pb_ratio,
	dividend_yield, growth_calculation,
)


def test_gross_margin():
	assert gross_margin(40, 100) == 0.4
	assert gross_margin(0, 100) == 0.0


def test_operating_margin():
	assert operating_margin(20, 100) == 0.2


def test_net_margin_int_semantics():
	assert net_margin(15, 300) == 0.05


def test_return_on_equity():
	assert return_on_equity(10, 200) == 0.05


def test_earning_per_share_preferred_dividends_deducted():
	# (1000 - 100) / 900
	assert earning_per_share(1000, 900, 100) == 1.0
	# None preferred dividends treated as 0
	assert earning_per_share(1000, 900, None) == pytest.approx(1.1111)


def test_debt_to_equity():
	assert debt_to_equity(150, 100) == 1.5


def test_current_ratio():
	assert current_ratio(200, 100) == 2.0


def test_revenues_per_share():
	assert revenues_per_share(1000, 100) == 10.0


def test_capital_index_negative_capex():
	# capex stored negative: -(-30) / 100
	assert capital_index(100, -30) == 0.3


def test_payback_period():
	assert payback_period(500, 100) == 5.0


def test_assets_price():
	# ((500 - 100) * 1.5) / 1000
	assert assets_price(500, 100, 1000) == 0.6


def test_pe_and_pb_ratio():
	assert pe_ratio(100, 5) == 20.0
	assert pb_ratio(1000, 200) == 5.0


def test_dividend_yield_percent_scaling():
	assert dividend_yield(0.0055) == 0.55
	assert dividend_yield(None) is None


def test_division_by_zero_returns_none():
	assert gross_margin(40, 0) is None
	assert pe_ratio(100, 0) is None
	assert current_ratio(200, 0) is None


def test_none_inputs_return_none():
	assert gross_margin(None, 100) is None
	assert return_on_equity(10, None) is None


def test_growth_calculation_cagr():
	# 100 -> 200 over 4 statements: (2^(1/4) - 1)
	statements = [
		{"net_income": 200},
		{"net_income": 150},
		{"net_income": 120},
		{"net_income": 100},
	]
	g = growth_calculation(statements, "net_income")
	assert g == pytest.approx(2 ** 0.25 - 1, abs=1e-4)


def test_growth_calculation_sign_flip_returns_none():
	statements = [{"v": 100}, {"v": -50}]
	assert growth_calculation(statements, "v") is None


def test_growth_calculation_missing_key_returns_none():
	assert growth_calculation([{"other": 1}], "net_income") is None


def test_growth_calculation_empty_returns_none():
	assert growth_calculation([], "net_income") is None
