import pandas as pd


def batch_tickers(symbols: list, batch_size=50) -> list[list]:
	for i in range(0, len(symbols), batch_size):
		yield symbols[i:i + batch_size]


def evaluate_null_tolerance(
	data: list,
	null_tolerance_p: float
) -> list[bool, list, float]:
	'''
	Function converts NoneType to None and returns tolerance and data and null_ratio
	:percentage_tolerance
		- has format of "0.25" which would be "25%"
		- how many % from all items can be None?
	'''
	
	converted_data = []
	null_count = 0

	for val in data:
		if pd.isna(val) is True:
			null_count += 1
			converted_data.append(None)
		else:
			converted_data.append(val)

	# % of None that is present in the data
	null_ratio = round(null_count / len(converted_data), 2)

	if null_tolerance_p >= null_ratio:
		return [True, converted_data]
	else:
		return [False, converted_data]
