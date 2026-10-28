from .utils.constants import METRIC_COLUMNS, HIGHER_IS_BETTER, GROUPS
from .utils.sql import get_stock_ids_within_industry, get_financial_analysis, get_stock_industry
from .utils.func import normalize
from datetime import date


def calculate_quality_score(
	target_stock_id: int,
	fiscal_date: str | date,
	period: str
) -> dict:
	"""
	Get industry peers, normalize metrics 0–100, compute weighted quality_score.
	Returns {stock_id, quality_score, category_scores}
	"""
	industry = get_stock_industry(target_stock_id)
	peer_ids = get_stock_ids_within_industry(industry)

	analyses = get_financial_analysis(peer_ids, fiscal_date, period)
	if not analyses:
		return {"stock_id": target_stock_id, "quality_score": None, "category_scores": {}, "median_comparison": None}

	# Initialize the structure for all peers
	normalized = {stock_id: {} for stock_id in analyses}
	# Normalize columns across all peers
	for metric in METRIC_COLUMNS:
		metric_values = [(stock_id, data.get(metric)) for stock_id, data in analyses.items()]
		normalized_scores = normalize(metric_values, higher_is_better=HIGHER_IS_BETTER[metric])
		for stock_id, score in normalized_scores.items():
			normalized[stock_id][metric] = score

	if target_stock_id not in normalized:
		return {"stock_id": target_stock_id, "quality_score": None, "category_scores": {}, "median_comparison": None}

	# Compute quality scores for all peers to find the industry median
	peer_quality_scores = {}
	for sid, metrics in normalized.items():
		peer_total = 0.0
		for group_name, group in GROUPS.items():
			scores = [
				metrics[m]
				for m in group["metrics"]
				if m in metrics and metrics[m] is not None
			]
			avg = sum(scores) / len(scores) if scores else 0.0
			peer_total += avg * group["weight"]
		peer_quality_scores[sid] = round(peer_total, 2)

	all_scores = sorted(peer_quality_scores.values())
	n = len(all_scores)
	if n == 0:
		median = 0.0
	elif n % 2 == 0:
		median = (all_scores[n // 2 - 1] + all_scores[n // 2]) / 2
	else:
		median = all_scores[n // 2]

	total = 0.0
	category_scores = {}
	target_metrics = normalized[target_stock_id]

	for group_name, group in GROUPS.items():
		scores = [
			target_metrics[m]
			for m in group["metrics"]
			if m in target_metrics and target_metrics[m] is not None
		]
		avg = sum(scores) / len(scores) if scores else 0.0
		weighted = avg * group["weight"]
		category_scores[group_name] = round(weighted, 2)
		total += weighted

	quality_score = round(total, 2)
	median_comparison = round((quality_score - median) / median, 4) if median != 0 else None

	return {
		"quality_score": quality_score,
		"category_scores": category_scores,
		"median_comparison": median_comparison
	}
