'''
Layer 2b — failover unit tests (no network).

Tests the per-symbol failover CONTRACT the future FailoverSource must satisfy
(datasource/failover.py, planned in PLAN.md). Until it exists, the contract is
verified against a reference implementation defined here; when FailoverSource
lands, these tests point at it instead.
'''
import pytest

from conftest import FIXTURES_DIR

HAS_FAILOVER = (FIXTURES_DIR.parent.parent / "src" / "datasource" / "failover.py").exists()

if HAS_FAILOVER:
	from datasource.failover import FailoverSource as ReferenceFailover
else:
	class ReferenceFailover:
		'''
		Minimal reference contract implementation:
		FailoverSource(primary, fallback, validate) where validate(result) -> bool.
		get(symbol) tries primary then fallback per symbol; returns (result, source_name)
		or (None, None).
		'''
		def __init__(self, primary, fallback, validate):
			self.primary, self.fallback, self.validate = primary, fallback, validate

		def get(self, symbol):
			try:
				result = self.primary.get(symbol)
				if self.validate(result):
					return result, "primary"
			except Exception:
				pass
			try:
				result = self.fallback.get(symbol)
				if self.validate(result):
					return result, "fallback"
			except Exception:
				pass
			return None, None


class StubSource:
	def __init__(self, behavior):
		self.behavior = behavior	# symbol -> ("raise" | "empty" | "junk" | "good", payload)
		self.calls = []

	def get(self, symbol):
		self.calls.append(symbol)
		mode, payload = self.behavior[symbol]
		if mode == "raise":
			raise ConnectionError(f"{symbol} failed")
		if mode == "empty":
			return None
		if mode == "junk":
			return {"unexpected_key": 1}
		return payload


def is_good(result):
	return isinstance(result, dict) and "price" in result


def make_failover(primary_behavior, fallback_behavior):
	return ReferenceFailover(StubSource(primary_behavior), StubSource(fallback_behavior), is_good)


def test_primary_good_fallback_never_called():
	fo = make_failover({"AAPL": ("good", {"price": 1})}, {"AAPL": ("good", {"price": 2})})
	result, source = fo.get("AAPL")
	assert result == {"price": 1}
	assert source == "primary"
	assert fo.fallback.calls == []


def test_primary_raises_falls_back():
	fo = make_failover({"AAPL": ("raise", None)}, {"AAPL": ("good", {"price": 2})})
	result, source = fo.get("AAPL")
	assert result == {"price": 2}
	assert source == "fallback"


def test_primary_empty_falls_back():
	fo = make_failover({"AAPL": ("empty", None)}, {"AAPL": ("good", {"price": 2})})
	result, source = fo.get("AAPL")
	assert (result, source) == ({"price": 2}, "fallback")


def test_primary_junk_falls_back():
	fo = make_failover({"AAPL": ("junk", None)}, {"AAPL": ("good", {"price": 2})})
	assert fo.get("AAPL") == ({"price": 2}, "fallback")


def test_both_fail_returns_none():
	fo = make_failover({"AAPL": ("raise", None)}, {"AAPL": ("empty", None)})
	assert fo.get("AAPL") == (None, None)


def test_per_symbol_independence():
	# One symbol failing does not affect others (per-symbol failover, not per-phase)
	fo = make_failover(
		{"GOOD": ("good", {"price": 1}), "BAD": ("raise", None)},
		{"GOOD": ("good", {"price": 9}), "BAD": ("good", {"price": 2})},
	)
	assert fo.get("GOOD") == ({"price": 1}, "primary")
	assert fo.get("BAD") == ({"price": 2}, "fallback")


def test_validate_rejects_none_result():
	fo = make_failover({"AAPL": ("good", None)}, {"AAPL": ("good", {"price": 2})})
	assert fo.get("AAPL") == ({"price": 2}, "fallback")


@pytest.mark.skipif(HAS_FAILOVER, reason="FailoverSource exists - this test documents contract only")
def test_failover_module_yet_to_be_built():
	pytest.skip("datasource/failover.py not built yet - Layer 2b runs against reference impl")
