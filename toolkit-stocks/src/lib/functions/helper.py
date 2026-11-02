import pandas as pd


def batch_tickers(symbols: list, batch_size=50) -> list[list]:
	for i in range(0, len(symbols), batch_size):
		yield symbols[i:i + batch_size]


def evaluate_null_tolerance(
	data: dict | list,
	null_tolerance_p: float,
) -> tuple[bool, dict | list]:
	'''
	Converts pandas NaN to None, then checks the null ratio against tolerance.
	Accepts a dict (row: ratio over values, keys preserved) or a list
	(ratio over items). Returns (passed, converted_data).
	:percentage_tolerance
		- has format of "0.25" which would be "25%"
		- how many % from all items can be None?
	'''
	if not data:
		return True, data

	if isinstance(data, dict):
		converted_data = {
			key: (None if pd.isna(val) else val) for key, val in data.items()
		}
		null_count = sum(1 for val in converted_data.values() if val is None)
	else:
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
		return True, converted_data
	else:
		return False, converted_data
