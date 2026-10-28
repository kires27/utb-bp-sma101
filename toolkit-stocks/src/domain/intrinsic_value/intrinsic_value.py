import math


def free_cash_flows(cash_flow):
	dates = []
	values = []
	for i in range(len(cash_flow)):
		if i + 1 < len(cash_flow) and cash_flow[i]["fiscal_date"] <= cash_flow[i + 1]["fiscal_date"]:
			raise ValueError("Cash Flow statements corrupted")
		value = cash_flow[i]["free_cash_flow"]
		if isinstance(value, (int, float)) and not math.isnan(value):
			dates.append(cash_flow[i]["fiscal_date"])
			values.append(value)
	return {"dates": dates, "values": values}


def annual_growth_rate(fcfs):
	"""Growth over the full available span, newest vs oldest."""
	periods = len(fcfs) - 1
	return (fcfs[0] / fcfs[-1]) ** (1 / periods) - 1


def normalized_free_cash_flow(fcfs):
	"""Mean of the 3 newest FCFs (Excel: (C84+D84+E84)/3)."""
	return sum(fcfs[:3]) / 3


def future_free_cash_flows(fcf, length, dagr):
	holder = []
	current = fcf
	for _ in range(length):
		current = current * (1 + dagr)
		holder.append(current)
	return holder


def discounted_future_free_cash_flows(ffcfs, disc):
	holder = []
	for exp in range(1, len(ffcfs) + 1):
		holder.append(ffcfs[exp - 1] / disc ** exp)
	return holder


def calculate_intrinsic_value(
	stock_price,
	share_issued,
	cash_flow,
	price_to_fcf,
	growth_rate_discount,
	future_discount_rate,
	safety_margin,
):
	"""Canonical model mirrors the Excel sheet (concept/calculation).

	- NFCF: mean of the 3 newest FCFs
	- AGR: newest vs FCF 5y back (full available span if fewer than 6 years)
	- 5 projected years, growth discount applied, discounted by FDR^year
	- Terminal: FCF5 * peer P/FCF, discounted
	- NO cash added; margin of safety applied to per-share result
	"""
	grd_decimal = 1 - growth_rate_discount / 100
	fdr_decimal = 1 + future_discount_rate / 100
	sm_decimal = 1 - safety_margin / 100

	fcfs = free_cash_flows(cash_flow)["values"]

	agr = annual_growth_rate(fcfs[:6])
	dagr = agr * grd_decimal

	nfcf = normalized_free_cash_flow(fcfs)
	ffcfs = future_free_cash_flows(nfcf, 5, dagr)

	ter = ffcfs[-1] * price_to_fcf

	dffcf_sum = sum(discounted_future_free_cash_flows(ffcfs, fdr_decimal))
	dter = ter / (fdr_decimal ** 5)
	iv = dffcf_sum + dter

	ivps = (iv * sm_decimal) / share_issued
	ivpspd = ((ivps - stock_price) / stock_price) * 100

	return {
		"stock_price": stock_price,
		"projection_horizon": 5,
		"annual_growth_rate": [
			agr * 100,
		],
		"intrinsic_value": [
			iv,
		],
		"intrinsic_value_per_share": [
			ivps,
		],
		"iv_upside": [
			ivpspd,
		],
	}
