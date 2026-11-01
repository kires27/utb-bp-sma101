'''Screener discovery: YAML -> EquityQuery building, validation, pagination,
insert-only diff against the stock table.'''
import pytest

import pipeline.screener as sc
from pipeline.screener import build_query, load_queries


# ---- query building ----

def test_scalar_maps_to_eq():
	q = build_query({"region": "us"})
	assert q.operator == "EQ"
	assert q.operands == ["region", "us"]


def test_list_maps_to_is_in():
	q = build_query({"exchange": ["NMS", "NYQ"]})
	assert q.operator == "IS-IN"
	assert q.operands == ["exchange", "NMS", "NYQ"]


def test_explicit_operator_form():
	q = build_query({"eodprice": {"btwn": [2, 10000]}})
	assert q.operator == "BTWN"
	assert q.operands == ["eodprice", 2.0, 10000.0]

	q = build_query({"avgdailyvol3m": {"gt": 100000}})
	assert q.operator == "GT"


def test_composite_and_or():
	q = build_query({"and": [{"region": "us"}, {"exchange": ["LSE"]}]})
	assert q.operator == "AND"
	assert all(isinstance(child, type(q)) for child in q.operands)

	q = build_query({"or": [{"region": "us"}, {"region": "gb"}]})
	assert q.operator == "OR"


# ---- validation: fail loudly at startup ----

def test_unknown_field_fails():
	with pytest.raises(ValueError, match="Unknown screener field"):
		build_query({"not_a_real_field": 1})


def test_unknown_operator_fails():
	with pytest.raises(ValueError, match="Unknown operator"):
		build_query({"eodprice": {"zzz": 1}})


def test_invalid_region_value_fails():
	with pytest.raises(ValueError, match="Invalid region value"):
		build_query({"region": "mars"})


def test_invalid_exchange_value_fails():
	with pytest.raises(ValueError, match="Invalid exchange value"):
		build_query({"exchange": ["BOGUS"]})


def test_btwn_needs_two_values():
	with pytest.raises(ValueError, match="btwn needs a 2-value list"):
		build_query({"eodprice": {"btwn": [2]}})


def test_eq_rejects_list():
	with pytest.raises(ValueError, match="takes one value"):
		build_query({"sector": {"eq": ["Technology", "Health Care"]}})


# ---- config loading ----

def test_repo_config_loads():
	'''The versioned config parses and validates against the real vocabulary.'''
	queries = load_queries()
	by_name = dict(queries)
	assert by_name["us-core"].operator == "AND"
	assert by_name["us-europe"].operator == "OR"


def test_config_missing_name_fails(tmp_path):
	cfg = tmp_path / "screener.yml"
	cfg.write_text("universe:\n  - conditions:\n      - region: us\n")
	with pytest.raises(ValueError, match="missing 'name'"):
		load_queries(str(cfg))


# ---- pagination ----

class FakeScreenAPI:
	def __init__(self, total, page_size=3):
		self.total = total
		self.page_size = page_size
		self.calls = []

	def __call__(self, query, size=None, offset=None):
		self.calls.append((size, offset))
		start = offset or 0
		quotes = [{"symbol": f"S{i}"} for i in range(start, min(start + self.page_size, self.total))]
		return {"start": start, "count": len(quotes), "total": self.total, "quotes": quotes}


def test_screen_all_paginates(monkeypatch):
	fake = FakeScreenAPI(total=7, page_size=3)
	monkeypatch.setattr(sc.screener, "screen", fake)

	quotes = sc.screen_all(build_query({"region": "us"}))

	assert [q["symbol"] for q in quotes] == [f"S{i}" for i in range(7)]
	# every page requested at PAGE_SIZE
	assert all(size == sc.PAGE_SIZE for size, _ in fake.calls)


# ---- discovery: insert-only diff ----

class FakeFlusher:
	instances = []

	def __init__(self, table, flush_size=None, conflict_keys=None, null_tolerance=None):
		self.table = table
		self.conflict_keys = conflict_keys
		self.rows = []
		FakeFlusher.instances.append(self)

	def add(self, rows):
		self.rows.extend(rows)

	def finish(self):
		return len(self.rows)


@pytest.fixture(autouse=True)
def _reset_flushers():
	FakeFlusher.instances.clear()
	yield


def _quotes():
	return [
		{"symbol": "AAA", "longName": "New Co A", "fullExchangeName": "NasdaqGS", "currency": "USD", "quoteType": "EQUITY"},
		{"symbol": "BBB", "longName": "Existing Co", "fullExchangeName": "NasdaqGS", "currency": "USD", "quoteType": "EQUITY"},
		{"symbol": "CCC", "shortName": "C Co", "fullExchangeName": "NYSE", "currency": "EUR", "quoteType": "EQUITY"},
	]


def test_discover_inserts_only_new_symbols(monkeypatch):
	monkeypatch.setattr(sc, "screen_all", lambda query: _quotes())
	monkeypatch.setattr(sc, "get_symbols", lambda: ["BBB"])
	monkeypatch.setattr(sc, "RowFlusher", FakeFlusher)

	stats = sc.discover()

	assert stats["screened"] == 3
	assert stats["new_symbols"] == ["AAA", "CCC"]
	assert len(FakeFlusher.instances) == 1
	flusher = FakeFlusher.instances[0]
	assert flusher.table == "stock"
	# insert-only: no conflict keys -> ON CONFLICT DO NOTHING
	assert flusher.conflict_keys is None
	assert [r["symbol"] for r in flusher.rows] == ["AAA", "CCC"]
	assert flusher.rows[0]["name"] == "New Co A"
	assert "name" in flusher.rows[1] and flusher.rows[1]["name"] == "C Co"


def test_discover_nothing_new_writes_nothing(monkeypatch):
	monkeypatch.setattr(sc, "screen_all", lambda query: _quotes())
	monkeypatch.setattr(sc, "get_symbols", lambda: ["AAA", "BBB", "CCC"])
	monkeypatch.setattr(sc, "RowFlusher", FakeFlusher)

	stats = sc.discover()

	assert stats["new_symbols"] == []
	assert FakeFlusher.instances == []
