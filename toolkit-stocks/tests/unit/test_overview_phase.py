'''run_overview: Python-side change detection (no DB trigger).
_differs type-quirk cases + unchanged rows skip the write, changed rows
write a partial update (changed cells + fresh stamp only).'''
from types import SimpleNamespace

import pytest

import pipeline.overview as ov
from pipeline.overview import _differs, run_overview


class FakeCtx:
	def __init__(self, symbols, known=True, force=False):
		self.args = SimpleNamespace(force=force, full=False)
		self.symbols = symbols
		# known=False simulates symbols not yet in stock (discovery flow);
		# without force they are dropped by the stale gate before any fetch
		self.stock_ids = {s: i + 1 for i, s in enumerate(symbols)} if known else {}
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


def _install_fakes(monkeypatch, existing_rows, inserted, updated):
	monkeypatch.setattr(ov, "get_stale_stock_ids", lambda ids, days: set(ids))
	monkeypatch.setattr(ov, "get_stock_overview_rows", lambda ids: existing_rows)
	monkeypatch.setattr(ov, "refresh_ids", lambda ctx: None)

	def fake_insert(row, table, **kwargs):
		inserted.append(row)
		return 1

	def fake_update(table, data, keys, label=""):
		updated.append({**data, **keys})
		return 1

	monkeypatch.setattr(ov, "insert_data_statement", fake_insert)
	monkeypatch.setattr(ov, "update_row", fake_update)


def test_unchanged_profile_skips_write(monkeypatch):
	inserted = []
	updated = []
	existing = {
		"symbol": "AAA", "address": None, "description": None,
		"employees": 123000, "industry": None, "key_executives": [],
		"phone_number": None, "sector": "Technology",
		"website": "https://example.com", "name": "AAA Inc",
		"exchange": None, "city": None, "country": None, "zip": None,
		"statement_currency": None,
	}
	_install_fakes(monkeypatch, {"AAA": existing}, inserted, updated)

	stats = run_overview(FakeCtx(["AAA"]))

	assert inserted == []
	assert updated == []
	assert stats["skipped_unchanged"] == 1


def test_changed_profile_writes_partial_row(monkeypatch):
	# Regression: a partial update must go through UPDATE, never the INSERT
	# half of an upsert (stock.name is NOT NULL -> NotNullViolation before
	# conflict resolution; broke the daily workflow 2026-11-16).
	inserted = []
	updated = []
	existing = {
		"symbol": "AAA", "address": None, "description": None,
		"employees": 999, "industry": None, "key_executives": [],
		"phone_number": None, "sector": "Technology",
		"website": "https://example.com", "name": "AAA Inc",
		"exchange": None, "city": None, "country": None, "zip": None,
		"statement_currency": None,
	}
	_install_fakes(monkeypatch, {"AAA": existing}, inserted, updated)

	stats = run_overview(FakeCtx(["AAA"]))

	assert inserted == []
	assert len(updated) == 1
	row = updated[0]
	# only the changed cell + key + fresh stamp; nothing else touched
	assert set(row) == {"employees", "symbol", "maintenance_update"}
	assert row["employees"] == 123000
	assert row["symbol"] == "AAA"
	assert row["maintenance_update"] is not None
	assert "skipped_unchanged" not in stats


def test_new_symbol_writes_full_row(monkeypatch):
	inserted = []
	updated = []
	_install_fakes(monkeypatch, {}, inserted, updated)

	stats = run_overview(FakeCtx(["NEW"], known=False, force=True))

	assert updated == []
	assert len(inserted) == 1
	row = inserted[0]
	assert row["name"] == "NEW Inc"
	assert row["sector"] == "Technology"
	assert row["maintenance_update"] is not None
	assert "skipped_unchanged" not in stats


def test_known_symbol_without_stored_row_updates_full_row(monkeypatch):
	# stored-row read failed (empty map): known symbol keeps the full fetched
	# row and still goes through UPDATE (NOT NULL columns all present).
	inserted = []
	updated = []
	_install_fakes(monkeypatch, {}, inserted, updated)

	stats = run_overview(FakeCtx(["AAA"]))

	assert inserted == []
	assert len(updated) == 1
	row = updated[0]
	assert row["name"] == "AAA Inc"
	assert row["symbol"] == "AAA"
	assert "skipped_unchanged" not in stats
