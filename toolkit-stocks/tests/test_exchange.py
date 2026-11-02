'''Simple test: static seed validation only. No DB, no network.'''
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.exchanges import exchanges
from pipeline.exchange import _validate_seed


def test_seed_is_valid():
	assert _validate_seed() == []


def test_seed_codes_unique():
	codes = [ex["exchange_code"] for ex in exchanges]
	assert len(codes) == len(set(codes))


def test_seed_covers_stock_table():
	'''Every exchange code in the seed must be a real yfinance-style name
	(checked against stock table is done at runtime; here just sanity).'''
	assert len(exchanges) >= 30
	for ex in exchanges:
		assert ex["open_time"] < ex["close_time"]
