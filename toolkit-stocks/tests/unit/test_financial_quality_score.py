# flake8: noqa: E241
from unittest.mock import patch
from domain.financial_quality_score.quality_score import calculate_quality_score


def helper_translate_object(peers, data):
	result = {}
	for i, peer_id in enumerate(peers):
		result[peer_id] = {}
		for metric, values in data.items():
			result[peer_id][metric] = values[i]
	return result

def test_calculate_quality_score_success():
	fake_industry = "Technology"
	fake_peers = [101, 102, 103, 104, 105]
	fake_analyses_data = {
		"gross_margin":             [0.47,         0.34,         0.21,         0.35,      0.61],
		"operating_margin":         [0.32,         0.11,         0.06,         -0.04,     0.24],
		"net_margin":               [0.27,         0.09,         0.05,         -0.01,     0.24],
		"return_on_equity":         [1.52,         0.13,         -7.31,        0.00,      0.10],
		"earnings_per_share":       [7.46,         1.24,         2.65,         -0.06,     0.40],
		"debt_to_equity":           [3.87,         3.15,         -121.72,      0.67,      0.25],
		"debt_growth":              [-0.05,        0.18,         0.10,         0.05,      None],
		"current_ratio":            [0.89,         0.70,         0.77,         2.02,      4.61],
		"revenue_growth":           [0.09,         0.02,         0.00,         -0.07,     -0.09],
		"gross_income_growth":      [0.13,         -0.02,        0.02,         -0.16,     -0.05],
		"net_income_growth":        [0.14,         0.07,         -0.02,        -1.42,     -0.05],
		"retained_earning_growth":  [-1.99,        0.12,         0.01,         -0.03,     0.03],
		"revenues_per_share":       [27.73,        14.08,        58.02,        11.67,     1.65],
		"capital_index":            [0.44,         1.33,         1.21,         -394.81,   0.40],
		"payback_period":           [0.79,         0.70,         1.92,         1.81,      None],
		"assets_price":             [0.03,         0.55,         -0.02,        2.07,      0.34],
		"pe_ratio":                 [34.19,        20.29,        10.43,        -343.06,   43.38],
		"pb_ratio":                 [51.93,        2.72,         -76.27,       0.72,      4.44],
		"dividend_yield":           [0.004027132,  0.004974699,  0.041229972,  None,      0.015974008],
	}
	fake_category_scores_data = {
    	"profitability_earnings":  [23.75,  12.50,  6.25,   3.75,   16.25],
		"financial_stability":     [10.00,  1.67,   10.56,  12.78,  17.50],
		"growth_quality":          [15.00,  14.00,  13.00,  3.00,   5.00],
		"capital_discipline":      [5.83,   5.00,   1.25,   6.67,   7.50],
		"market_value":            [2.50,   8.75,   8.75,   13.75,  3.75],
		"shareholder_value":       [0.00,   3.33,   10.00,  0.00,   6.67],
	}
	fake_analyses = helper_translate_object(fake_peers, fake_analyses_data)
	fake_category_scores = helper_translate_object(fake_peers, fake_category_scores_data)
	fake_quality_scores = {
		101: 57.08, 
		102: 45.25, 
		103: 49.81, 
		104: 39.94, 
		105: 56.67,
	}

	with (patch("domain.financial_quality_score.quality_score.get_stock_industry", return_value=fake_industry),
		  patch("domain.financial_quality_score.quality_score.get_stock_ids_within_industry", return_value=fake_peers),
		  patch("domain.financial_quality_score.quality_score.get_financial_analysis", return_value=fake_analyses)):

		result1 = calculate_quality_score(
			target_stock_id=fake_peers[0],
			fiscal_date="2026-03-31",
			period="FY"
		)

		result2 = calculate_quality_score(
			target_stock_id=fake_peers[1],
			fiscal_date="2026-03-31",
			period="FY"
		)

		result3 = calculate_quality_score(
			target_stock_id=fake_peers[2],
			fiscal_date="2026-03-31",
			period="FY"
		)

		result4 = calculate_quality_score(
			target_stock_id=fake_peers[3],
			fiscal_date="2026-03-31",
			period="FY"
		)

		result5 = calculate_quality_score(
			target_stock_id=fake_peers[4],
			fiscal_date="2026-03-31",
			period="FY"
		)

	assert result1["quality_score"] == fake_quality_scores[fake_peers[0]]
	assert result1["category_scores"] == fake_category_scores[fake_peers[0]]

	assert result2["quality_score"] == fake_quality_scores[fake_peers[1]]
	assert result2["category_scores"] == fake_category_scores[fake_peers[1]]

	assert result3["quality_score"] == fake_quality_scores[fake_peers[2]]
	assert result3["category_scores"] == fake_category_scores[fake_peers[2]]

	assert result4["quality_score"] == fake_quality_scores[fake_peers[3]]
	assert result4["category_scores"] == fake_category_scores[fake_peers[3]]

	assert result5["quality_score"] == fake_quality_scores[fake_peers[4]]
	assert result5["category_scores"] == fake_category_scores[fake_peers[4]]
