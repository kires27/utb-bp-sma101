'''
Layer 2 — golden/fixture tests.

Frozen payloads in tests/fixtures/**.json, expected mapper output in sibling
*.expected.json. Regenerate expected files: tests/capture_fixtures.py --update
(or full re-capture without flag, needs network).
'''
import datetime
import json
from pathlib import Path

import pytest

from lib.transforms import (
	build_price_rows, build_dividend_rows, build_split_rows,
	build_overview_row, build_metric_row, build_statement_rows,
)
from lib.transforms.statements import group_statement_records
from conftest import FIXTURES_DIR, expected_path

STMT_FINANCE_TYPE = {"income": "income_statement", "balance": "balance_sheet", "cash": "cash_flow"}

SOURCES = sorted(d.name for d in FIXTURES_DIR.iterdir() if d.is_dir()) if FIXTURES_DIR.exists() else []


def _load(path: Path):
	return json.load(open(path, encoding="utf-8"))


def _sym_dirs():
	for source in SOURCES:
		for sym_dir in sorted((FIXTURES_DIR / source).iterdir()):
			if sym_dir.is_dir():
				yield source, sym_dir


def _assert_expected(got, expected_path: Path, keys=None):
	assert expected_path.exists(), f"missing expected file {expected_path}; run capture_fixtures.py"
	expected = _load(expected_path)
	single = isinstance(expected, dict)	 # single-row expectation (profile, quote)
	rows = got if single else list(got)
	normalized = []
	for row in rows:
		row = {
			k: (str(v) if isinstance(v, datetime.date) else v)
			for k, v in row.items() if k != "maintenance_update"	# nondeterministic timestamp
		}
		if keys is not None:
			row = {k: row.get(k) for k in keys}
		normalized.append(row)
	if single:
		normalized = normalized[0]
	if keys is not None:
		expected = {k: expected.get(k) for k in keys} if single else [ {k: row.get(k) for k in keys} for row in expected ]
	assert normalized == expected


pytestmark = pytest.mark.skipif(not SOURCES, reason="no fixtures captured yet - run tests/capture_fixtures.py")


@pytest.mark.parametrize("sym_dir", [d for s, d in _sym_dirs() if s == "defeatbeta"], ids=lambda d: d.name)
class TestDefeatBetaGolden:
	def test_prices(self, sym_dir):
		rows = build_price_rows(sym_dir.name.upper(), 1, _load(sym_dir / "prices.json"), None)
		_ = _assert_expected(rows, expected_path(sym_dir / "prices.json"))

	def test_dividends(self, sym_dir):
		rows = build_dividend_rows(sym_dir.name.upper(), 1, _load(sym_dir / "dividends.json"), None)
		_ = _assert_expected(rows, expected_path(sym_dir / "dividends.json"))

	def test_splits(self, sym_dir):
		rows = build_split_rows(sym_dir.name.upper(), 1, _load(sym_dir / "splits.json"), None)
		_ = _assert_expected(rows, expected_path(sym_dir / "splits.json"))

	def test_profile(self, sym_dir):
		row = build_overview_row(sym_dir.name.upper(), _load(sym_dir / "profile.json"),
			_load(sym_dir / "officers.json"), {}, None)
		_ = _assert_expected([row], expected_path(sym_dir / "profile.json"))

	@pytest.mark.parametrize("name", ["income", "balance", "cash"])
	def test_statements(self, sym_dir, name):
		path = sym_dir / f"statements_{name}.json"
		if not path.exists():
			pytest.skip(f"no {name} fixture")
		grouped = group_statement_records(_load(path))
		rows = build_statement_rows(sym_dir.name.upper(), 1, grouped, "annual", STMT_FINANCE_TYPE[name])
		_ = _assert_expected(rows, expected_path(path))


@pytest.mark.parametrize("sym_dir", [d for s, d in _sym_dirs() if s == "yfinance"], ids=lambda d: d.name)
class TestYfinanceGolden:
	def test_history(self, sym_dir):
		h = _load(sym_dir / "history.json")
		rows = build_price_rows(sym_dir.name.upper(), 1, h["price_rows"], None)
		_ = _assert_expected(rows, expected_path(sym_dir / "history.json"))

	def test_info(self, sym_dir):
		info = _load(sym_dir / "info.json")
		row = build_overview_row(sym_dir.name.upper(), info, None, {}, info)
		_ = _assert_expected([row], expected_path(sym_dir / "info.json"))

	def test_quote(self, sym_dir):
		row = build_metric_row(sym_dir.name.upper(), 1, _load(sym_dir / "quote.json"))
		_ = _assert_expected([row], expected_path(sym_dir / "quote.json"))

	@pytest.mark.parametrize("name", ["income", "balance", "cash"])
	def test_statements(self, sym_dir, name):
		path = sym_dir / f"statements_{name}.json"
		if not path.exists():
			pytest.skip(f"no {name} fixture")
		rows = build_statement_rows(sym_dir.name.upper(), 1, _load(path), "annual", STMT_FINANCE_TYPE[name])
		_ = _assert_expected(rows, expected_path(path))
