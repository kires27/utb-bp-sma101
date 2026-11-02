import pytest

from lib.functions.helper import evaluate_null_tolerance


def test_dict_converts_nan_to_none_and_preserves_keys():
	import pandas as pd
	row = {"open": pd.NA, "high": 1.5, "low": None, "close": 2.0}
	passed, cleaned = evaluate_null_tolerance(row, 1)
	assert passed is True
	assert cleaned == {"open": None, "high": 1.5, "low": None, "close": 2.0}


def test_dict_null_ratio_over_values():
	import pandas as pd
	row = {"a": pd.NA, "b": pd.NA, "c": 1.0, "d": 2.0}
	passed, cleaned = evaluate_null_tolerance(row, 0.49)
	assert passed is False
	assert cleaned == {"a": None, "b": None, "c": 1.0, "d": 2.0}


def test_dict_values_support_dot_get():
	import pandas as pd
	row = {"open": pd.NA, "close": 1.0}
	_, cleaned = evaluate_null_tolerance(row, 1)
	assert cleaned.get("close") == 1.0
	assert cleaned.get("missing") is None


def test_list_behavior_unchanged():
	passed, cleaned = evaluate_null_tolerance([1, None, 2, None, 3, 4, 5, 6, 7, 8], 0.3)
	assert passed is True
	assert cleaned == [1, None, 2, None, 3, 4, 5, 6, 7, 8]


def test_list_over_tolerance_fails():
	passed, cleaned = evaluate_null_tolerance([None, None, 3], 0.5)
	assert passed is False
	assert cleaned == [None, None, 3]


def test_empty_dict_passes():
	passed, cleaned = evaluate_null_tolerance({}, 0.0)
	assert passed is True
	assert cleaned == {}


def test_empty_list_passes():
	passed, cleaned = evaluate_null_tolerance([], 0.0)
	assert passed is True
	assert cleaned == []
