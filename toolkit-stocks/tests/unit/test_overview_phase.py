'''run_overview: Python-side change detection (no DB trigger).
_differs type-quirk cases + unchanged rows skip the write, changed rows
write a partial update (changed cells + fresh stamp only).'''
from types import SimpleNamespace

import pytest

import pipeline.overview as ov
from pipeline.overview import _differs, run_overview


class FakeCtx:
	def __init__(self, symbols):
		self.args = SimpleNamespace(force=False, full=False)
		self.symbols = symbols
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)}
		self.symbol_meta = {}
		self.yfs = FakeYfs()


class FakeYfs:
	def map_symbols(self, fn, symbols, label):
		return {s: fn(s) for s in symbols}

	@staticmethod
	def profile(symbol):
		return {
			"longName": f"{symbol} Inc",
			"sector": "Technology",
			"full_time_employees": 123000,
			"website": "https://example.com",
		}


@pytest.mark.parametrize("new,old,expected", [
	# identical / both None
	("Technology", "Technology", False),
	(None, None, False),
	# int/float vs Decimal-from-DB
	(123000, 123000.0, False),
	(123000, 123001, True),
	(123000, None, True),
	(None, 123000, True),
	# jsonb list from DB vs JSON string on the fetched side
	([{"name": "CEO"}], '[{"name": "CEO"}]', False),
	([{"name": "CEO"}], '[{"name": "CFO"}]', True),
	('["a"]', ["a"], False),
	# plain mismatches
	("a", "b", True),
	("a", None, True),
	(None, "a", True),
])
def test_differs(new, old, expected):
	assert _differs(new, old) is expected


def _install_fakes(monkeypatch, existing_rows, inserted):
	monkeypatch.setattr(ov, "get_stale_stock_ids", lambda ids, days: set(ids))
	monkeypatch.setattr(ov, "get_stock_overview_rows", lambda ids: existing_rows)
	monkeypatch.setattr(ov, "refresh_ids", lambda ctx: None)

	def fake_insert(row, table, **kwargs):
		inserted.append(row)
		return 1

	monkeypatch.setattr(ov, "insert_data_statement", fake_insert)


def test_unchanged_profile_skips_write(monkeypatch):
	inserted = []
	existing = {
		"symbol": "AAA", "address": None, "description": None,
		"employees": 123000, "industry": None, "key_executives": [],
		"phone_number": None, "sector": "Technology",
		"website": "https://example.com", "name": "AAA Inc",
		"exchange": None, "city": None, "country": None, "zip": None,
		"statement_currency": None,
	}
	_install_fakes(monkeypatch, {"AAA": existing}, inserted)

	stats = run_overview(FakeCtx(["AAA"]))

	assert inserted == []
	assert stats["skipped_unchanged"] == 1


def test_changed_profile_writes_partial_row(monkeypatch):
	inserted = []
	existing = {
		"symbol": "AAA", "address": None, "description": None,
		"employees": 999, "industry": None, "key_executives": [],
		"phone_number": None, "sector": "Technology",
		"website": "https://example.com", "name": "AAA Inc",
		"exchange": None, "city": None, "country": None, "zip": None,
		"statement_currency": None,
	}
	_install_fakes(monkeypatch, {"AAA": existing}, inserted)

	stats = run_overview(FakeCtx(["AAA"]))

	assert len(inserted) == 1
	row = inserted[0]
	# only the changed cell + key + fresh stamp; nothing else touched
	assert set(row) == {"employees", "symbol", "maintenance_update"}
	assert row["employees"] == 123000
	assert row["symbol"] == "AAA"
	assert row["maintenance_update"] is not None
	assert "skipped_unchanged" not in stats


def test_new_symbol_writes_full_row(monkeypatch):
	inserted = []
	_install_fakes(monkeypatch, {}, inserted)

	stats = run_overview(FakeCtx(["NEW"]))

	assert len(inserted) == 1
	row = inserted[0]
	assert row["name"] == "NEW Inc"
	assert row["sector"] == "Technology"
	assert row["maintenance_update"] is not None
	assert "skipped_unchanged" not in stats
